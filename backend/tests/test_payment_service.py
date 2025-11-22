"""Tests for payment service"""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.payment_service import payment_service
from app.models.claim import Claim
from app.models.farm import Farm
from app.schemas.claim import ClaimStatus


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_farm():
    """Sample farm for testing"""
    farm = Farm(
        id=uuid4(),
        farmer_name="John Doe",
        farmer_id="12345678",
        phone_number="+254712345678",
        crop_type="maize",
        gps_lat=Decimal("-1.2921"),
        gps_lng=Decimal("36.8219"),
        gps_accuracy=5.0
    )
    return farm


@pytest.fixture
def sample_approved_claim(sample_farm):
    """Sample approved claim for testing"""
    claim = Claim(
        id=uuid4(),
        agent_id=uuid4(),
        farm_id=sample_farm.id,
        status=ClaimStatus.AUTO_APPROVED.value,
        ml_class="drought_stress",
        ml_confidence=0.92,
        image_url="https://storage.example.com/claim123.jpg",
        payout_amount=Decimal("5000.00"),
        payout_status="pending"
    )
    return claim


@pytest.mark.asyncio
async def test_process_payout_success(mock_db, sample_farm, sample_approved_claim):
    """Test successful payment processing"""
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,  # First call for claim
        sample_farm  # Second call for farm
    ]
    
    # Mock mobile money service
    mock_payment_result = MagicMock()
    mock_payment_result.success = True
    mock_payment_result.transaction_id = "MM123456789ABC"
    mock_payment_result.message = "Payment successful"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment', 
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result
        
        # Mock SMS service
        with patch('app.services.payment_service.sms_service.send_payment_notification',
                   new_callable=AsyncMock) as mock_send_sms:
            mock_send_sms.return_value = True
            
            # Execute
            result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
            
            # Verify
            assert result is True
            assert sample_approved_claim.status == ClaimStatus.PAID.value
            assert sample_approved_claim.payout_status == "completed"
            assert sample_approved_claim.payout_reference == "MM123456789ABC"
            
            # Verify mobile money was called
            mock_send_payment.assert_called_once_with(
                phone_number="+254712345678",
                amount=Decimal("5000.00"),
                reference=str(sample_approved_claim.id),
                db=mock_db
            )
            
            # Verify SMS was sent with correct parameters
            mock_send_sms.assert_called_once_with(
                phone_number="+254712345678",
                amount=5000.00,
                claim_id=str(sample_approved_claim.id)
            )
            
            # Verify database commit was called
            mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_payout_claim_not_found(mock_db):
    """Test payment processing when claim doesn't exist"""
    # Setup mock to return None
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Execute and verify exception
    with pytest.raises(ValueError, match="Claim .* not found"):
        await payment_service.process_payout(uuid4(), mock_db)


@pytest.mark.asyncio
async def test_process_payout_claim_not_approved(mock_db, sample_farm):
    """Test payment processing when claim is not in approved status"""
    # Create pending claim
    pending_claim = Claim(
        id=uuid4(),
        agent_id=uuid4(),
        farm_id=sample_farm.id,
        status=ClaimStatus.PENDING.value,
        ml_class="drought_stress",
        ml_confidence=0.92,
        image_url="https://storage.example.com/claim123.jpg"
    )
    
    # Setup mock
    mock_db.query.return_value.filter.return_value.first.return_value = pending_claim
    
    # Execute
    result = await payment_service.process_payout(pending_claim.id, mock_db)
    
    # Verify
    assert result is False


@pytest.mark.asyncio
async def test_process_payout_farm_not_found(mock_db, sample_approved_claim):
    """Test payment processing when farm doesn't exist"""
    # Setup mocks - claim exists but farm doesn't
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,  # First call for claim
        None  # Second call for farm
    ]
    
    # Execute and verify exception
    with pytest.raises(ValueError, match="Farm not found"):
        await payment_service.process_payout(sample_approved_claim.id, mock_db)


@pytest.mark.asyncio
async def test_process_payout_retry_logic(mock_db, sample_farm, sample_approved_claim):
    """Test payment retry logic with exponential backoff"""
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,  # First call for claim
        sample_farm  # Second call for farm
    ]
    
    # Mock mobile money service to fail twice then succeed
    mock_payment_result_fail = MagicMock()
    mock_payment_result_fail.success = False
    mock_payment_result_fail.message = "Payment failed"
    
    mock_payment_result_success = MagicMock()
    mock_payment_result_success.success = True
    mock_payment_result_success.transaction_id = "MM123456789ABC"
    mock_payment_result_success.message = "Payment successful"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.side_effect = [
            mock_payment_result_fail,
            mock_payment_result_fail,
            mock_payment_result_success
        ]
        
        # Mock SMS service
        with patch('app.services.payment_service.sms_service.send_payment_notification',
                   new_callable=AsyncMock) as mock_send_sms:
            mock_send_sms.return_value = True
            
            # Mock asyncio.sleep to speed up test
            with patch('asyncio.sleep', new_callable=AsyncMock):
                # Execute
                result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
                
                # Verify
                assert result is True
                assert mock_send_payment.call_count == 3  # Failed twice, succeeded on third
                assert sample_approved_claim.status == ClaimStatus.PAID.value


@pytest.mark.asyncio
async def test_process_payout_all_retries_fail(mock_db, sample_farm, sample_approved_claim):
    """Test payment processing when all retries fail"""
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,  # First call for claim
        sample_farm  # Second call for farm
    ]
    
    # Mock mobile money service to always fail
    mock_payment_result_fail = MagicMock()
    mock_payment_result_fail.success = False
    mock_payment_result_fail.message = "Payment failed"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result_fail
        
        # Mock asyncio.sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            # Execute
            result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
            
            # Verify
            assert result is False
            assert mock_send_payment.call_count == 3  # All 3 retries attempted
            assert sample_approved_claim.payout_status == "failed_manual_review_required"
            mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_payout_sms_failure_doesnt_fail_payment(mock_db, sample_farm, sample_approved_claim):
    """Test that SMS failure doesn't cause payment to fail"""
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,  # First call for claim
        sample_farm  # Second call for farm
    ]
    
    # Mock successful payment
    mock_payment_result = MagicMock()
    mock_payment_result.success = True
    mock_payment_result.transaction_id = "MM123456789ABC"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result
        
        # Mock SMS service to fail
        with patch('app.services.payment_service.sms_service.send_payment_notification',
                   new_callable=AsyncMock) as mock_send_sms:
            mock_send_sms.side_effect = Exception("SMS service unavailable")
            
            # Execute
            result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
            
            # Verify payment still succeeded despite SMS failure
            assert result is True
            assert sample_approved_claim.status == ClaimStatus.PAID.value


@pytest.mark.asyncio
async def test_retry_failed_payment_success(mock_db, sample_farm):
    """Test manually retrying a failed payment"""
    # Create claim with failed payment status
    failed_claim = Claim(
        id=uuid4(),
        agent_id=uuid4(),
        farm_id=sample_farm.id,
        status=ClaimStatus.AUTO_APPROVED.value,
        ml_class="drought_stress",
        ml_confidence=0.92,
        image_url="https://storage.example.com/claim123.jpg",
        payout_amount=Decimal("5000.00"),
        payout_status="failed_manual_review_required"
    )
    
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        failed_claim,  # First call to get claim for retry
        failed_claim,  # Second call in process_payout
        sample_farm  # Third call for farm
    ]
    
    # Mock successful payment
    mock_payment_result = MagicMock()
    mock_payment_result.success = True
    mock_payment_result.transaction_id = "MM123456789ABC"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result
        
        with patch('app.services.payment_service.sms_service.send_payment_notification',
                   new_callable=AsyncMock) as mock_send_sms:
            mock_send_sms.return_value = True
            
            # Execute
            result = await payment_service.retry_failed_payment(failed_claim.id, mock_db)
            
            # Verify
            assert result is True
            assert failed_claim.status == ClaimStatus.PAID.value
            assert failed_claim.payout_status == "completed"


@pytest.mark.asyncio
async def test_retry_failed_payment_wrong_status(mock_db):
    """Test retrying payment for claim not in failed status"""
    # Create claim with completed payment status
    completed_claim = Claim(
        id=uuid4(),
        agent_id=uuid4(),
        farm_id=uuid4(),
        status=ClaimStatus.PAID.value,
        ml_class="drought_stress",
        ml_confidence=0.92,
        image_url="https://storage.example.com/claim123.jpg",
        payout_amount=Decimal("5000.00"),
        payout_status="completed"
    )
    
    # Setup mock
    mock_db.query.return_value.filter.return_value.first.return_value = completed_claim
    
    # Execute
    result = await payment_service.retry_failed_payment(completed_claim.id, mock_db)
    
    # Verify
    assert result is False


# Integration Tests for SMS Sending
# These tests verify the integration between payment service and SMS service

@pytest.mark.asyncio
async def test_payment_with_sms_integration_success(mock_db, sample_farm, sample_approved_claim):
    """
    Integration test: Verify SMS is sent with correct parameters after successful payment
    
    Tests requirement 9.2, 9.3: SMS notification with amount in KES
    """
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,
        sample_farm
    ]
    
    # Mock successful payment
    mock_payment_result = MagicMock()
    mock_payment_result.success = True
    mock_payment_result.transaction_id = "MM123456789ABC"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result
        
        # Use real SMS service but mock the underlying Africa's Talking API
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {
                'SMSMessageData': {
                    'Message': 'Sent to 1/1 Total Cost: KES 0.8000',
                    'Recipients': [{
                        'statusCode': 101,
                        'number': '+254712345678',
                        'status': 'Success',
                        'cost': 'KES 0.8000',
                        'messageId': 'ATXid_test123'
                    }]
                }
            }
            
            # Execute
            result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
            
            # Verify payment succeeded
            assert result is True
            assert sample_approved_claim.status == ClaimStatus.PAID.value
            
            # Verify SMS was sent through the actual SMS service
            mock_to_thread.assert_called_once()
            
            # Verify SMS message content
            call_args = mock_to_thread.call_args
            sms_message = call_args[0][1]  # Second argument to sms.send
            
            # Verify message contains required elements (requirement 9.3)
            assert "MavunoSure" in sms_message
            assert "KES 5,000.00" in sms_message or "5000" in sms_message
            assert "approved" in sms_message.lower() or "payment" in sms_message.lower()
            
            # Verify phone number
            recipients = call_args[0][2]  # Third argument to sms.send
            assert "+254712345678" in recipients


@pytest.mark.asyncio
async def test_payment_with_sms_integration_retry_on_failure(mock_db, sample_farm, sample_approved_claim):
    """
    Integration test: Verify SMS failure doesn't prevent payment completion
    
    Tests that SMS errors are handled gracefully without failing the payment
    """
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,
        sample_farm
    ]
    
    # Mock successful payment
    mock_payment_result = MagicMock()
    mock_payment_result.success = True
    mock_payment_result.transaction_id = "MM123456789ABC"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result
        
        # Mock SMS service to fail
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {
                'SMSMessageData': {
                    'Message': 'Sent to 0/1 Total Cost: KES 0.0000',
                    'Recipients': [{
                        'statusCode': 403,
                        'number': '+254712345678',
                        'status': 'InvalidPhoneNumber',
                        'cost': 'KES 0.0000',
                        'messageId': None
                    }]
                }
            }
            
            # Execute
            result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
            
            # Verify payment still succeeded despite SMS failure
            assert result is True
            assert sample_approved_claim.status == ClaimStatus.PAID.value
            assert sample_approved_claim.payout_status == "completed"
            
            # Verify SMS was attempted
            mock_to_thread.assert_called_once()


@pytest.mark.asyncio
async def test_payment_with_sms_integration_network_error(mock_db, sample_farm, sample_approved_claim):
    """
    Integration test: Verify payment succeeds even when SMS service has network errors
    
    Tests resilience to SMS service failures
    """
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,
        sample_farm
    ]
    
    # Mock successful payment
    mock_payment_result = MagicMock()
    mock_payment_result.success = True
    mock_payment_result.transaction_id = "MM123456789ABC"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result
        
        # Mock SMS service to raise network exception
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Network timeout")
            
            # Execute
            result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
            
            # Verify payment still succeeded
            assert result is True
            assert sample_approved_claim.status == ClaimStatus.PAID.value
            assert sample_approved_claim.payout_status == "completed"


@pytest.mark.asyncio
async def test_payment_retry_with_sms_integration(mock_db, sample_farm, sample_approved_claim):
    """
    Integration test: Verify SMS is only sent once after successful payment retry
    
    Tests that SMS notification is sent only when payment finally succeeds,
    not on failed attempts
    """
    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_approved_claim,
        sample_farm
    ]
    
    # Mock payment to fail twice then succeed
    mock_payment_result_fail = MagicMock()
    mock_payment_result_fail.success = False
    mock_payment_result_fail.message = "Payment failed"
    
    mock_payment_result_success = MagicMock()
    mock_payment_result_success.success = True
    mock_payment_result_success.transaction_id = "MM123456789ABC"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.side_effect = [
            mock_payment_result_fail,
            mock_payment_result_fail,
            mock_payment_result_success
        ]
        
        # Mock SMS service
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {
                'SMSMessageData': {
                    'Message': 'Sent to 1/1 Total Cost: KES 0.8000',
                    'Recipients': [{
                        'statusCode': 101,
                        'number': '+254712345678',
                        'status': 'Success',
                        'cost': 'KES 0.8000',
                        'messageId': 'ATXid_test123'
                    }]
                }
            }
            
            # Mock asyncio.sleep to speed up test
            with patch('asyncio.sleep', new_callable=AsyncMock):
                # Execute
                result = await payment_service.process_payout(sample_approved_claim.id, mock_db)
                
                # Verify payment succeeded after retries
                assert result is True
                assert mock_send_payment.call_count == 3
                
                # Verify SMS was sent exactly once (only after successful payment)
                mock_to_thread.assert_called_once()


@pytest.mark.asyncio
async def test_payment_with_sms_integration_multiple_claims(mock_db, sample_farm):
    """
    Integration test: Verify SMS is sent correctly for multiple sequential payments
    
    Tests that SMS service handles multiple payment notifications correctly
    """
    # Create two different claims
    claim1 = Claim(
        id=uuid4(),
        agent_id=uuid4(),
        farm_id=sample_farm.id,
        status=ClaimStatus.AUTO_APPROVED.value,
        ml_class="drought_stress",
        ml_confidence=0.92,
        image_url="https://storage.example.com/claim1.jpg",
        payout_amount=Decimal("5000.00"),
        payout_status="pending"
    )
    
    claim2 = Claim(
        id=uuid4(),
        agent_id=uuid4(),
        farm_id=sample_farm.id,
        status=ClaimStatus.AUTO_APPROVED.value,
        ml_class="disease_blight",
        ml_confidence=0.88,
        image_url="https://storage.example.com/claim2.jpg",
        payout_amount=Decimal("7500.00"),
        payout_status="pending"
    )
    
    # Mock successful payment
    mock_payment_result = MagicMock()
    mock_payment_result.success = True
    mock_payment_result.transaction_id = "MM123456789ABC"
    
    with patch('app.services.payment_service.mobile_money_service.send_payment',
               new_callable=AsyncMock) as mock_send_payment:
        mock_send_payment.return_value = mock_payment_result
        
        # Mock SMS service
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {
                'SMSMessageData': {
                    'Message': 'Sent to 1/1 Total Cost: KES 0.8000',
                    'Recipients': [{
                        'statusCode': 101,
                        'number': '+254712345678',
                        'status': 'Success',
                        'cost': 'KES 0.8000',
                        'messageId': 'ATXid_test123'
                    }]
                }
            }
            
            # Process first claim
            mock_db.query.return_value.filter.return_value.first.side_effect = [claim1, sample_farm]
            result1 = await payment_service.process_payout(claim1.id, mock_db)
            
            # Process second claim
            mock_db.query.return_value.filter.return_value.first.side_effect = [claim2, sample_farm]
            result2 = await payment_service.process_payout(claim2.id, mock_db)
            
            # Verify both payments succeeded
            assert result1 is True
            assert result2 is True
            
            # Verify SMS was sent twice (once for each claim)
            assert mock_to_thread.call_count == 2
            
            # Verify first SMS had correct amount
            first_call_message = mock_to_thread.call_args_list[0][0][1]
            assert "5,000.00" in first_call_message or "5000" in first_call_message
            
            # Verify second SMS had correct amount
            second_call_message = mock_to_thread.call_args_list[1][0][1]
            assert "7,500.00" in second_call_message or "7500" in second_call_message
