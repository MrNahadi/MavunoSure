"""Tests for SMS service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.sms_service import sms_service


@pytest.fixture
def mock_africastalking_response_success():
    """Mock successful Africa's Talking API response"""
    return {
        'SMSMessageData': {
            'Message': 'Sent to 1/1 Total Cost: KES 0.8000',
            'Recipients': [
                {
                    'statusCode': 101,
                    'number': '+254712345678',
                    'status': 'Success',
                    'cost': 'KES 0.8000',
                    'messageId': 'ATXid_abc123def456'
                }
            ]
        }
    }


@pytest.fixture
def mock_africastalking_response_failure():
    """Mock failed Africa's Talking API response"""
    return {
        'SMSMessageData': {
            'Message': 'Sent to 0/1 Total Cost: KES 0.0000',
            'Recipients': [
                {
                    'statusCode': 403,
                    'number': '+254712345678',
                    'status': 'InvalidPhoneNumber',
                    'cost': 'KES 0.0000',
                    'messageId': None
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_send_otp_success(mock_africastalking_response_success):
    """Test sending OTP SMS successfully"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_success
        
        # Execute
        result = await sms_service.send_otp(
            phone_number="+254712345678",
            otp="123456"
        )
        
        # Verify
        assert result is True
        mock_to_thread.assert_called_once()
        
        # Verify the message format
        call_args = mock_to_thread.call_args
        message = call_args[0][1]  # Second argument to sms.send
        assert "123456" in message
        assert "MavunoSure" in message
        assert "5 minutes" in message


@pytest.mark.asyncio
async def test_send_otp_failure(mock_africastalking_response_failure):
    """Test OTP SMS sending failure"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_failure
        
        # Execute
        result = await sms_service.send_otp(
            phone_number="+254712345678",
            otp="123456"
        )
        
        # Verify
        assert result is False


@pytest.mark.asyncio
async def test_send_otp_exception():
    """Test OTP SMS sending with exception"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.side_effect = Exception("Network error")
        
        # Execute
        result = await sms_service.send_otp(
            phone_number="+254712345678",
            otp="123456"
        )
        
        # Verify
        assert result is False


@pytest.mark.asyncio
async def test_send_message_success(mock_africastalking_response_success):
    """Test sending generic SMS successfully"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_success
        
        # Execute
        result = await sms_service.send_message(
            phone_number="+254712345678",
            message="Test message"
        )
        
        # Verify
        assert result is True
        mock_to_thread.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_failure(mock_africastalking_response_failure):
    """Test generic SMS sending failure"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_failure
        
        # Execute
        result = await sms_service.send_message(
            phone_number="+254712345678",
            message="Test message"
        )
        
        # Verify
        assert result is False


@pytest.mark.asyncio
async def test_send_message_exception():
    """Test generic SMS sending with exception"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.side_effect = Exception("API error")
        
        # Execute
        result = await sms_service.send_message(
            phone_number="+254712345678",
            message="Test message"
        )
        
        # Verify
        assert result is False


@pytest.mark.asyncio
async def test_send_payment_notification_success(mock_africastalking_response_success):
    """
    Test sending payment notification SMS successfully
    
    Implements requirements 9.2, 9.3:
    - Send SMS on successful payment
    - Include amount in KES
    """
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_success
        
        # Execute
        result = await sms_service.send_payment_notification(
            phone_number="+254712345678",
            amount=5000.00,
            claim_id="claim-123"
        )
        
        # Verify
        assert result is True
        mock_to_thread.assert_called_once()
        
        # Verify the message format includes KES amount (requirement 9.3)
        call_args = mock_to_thread.call_args
        message = call_args[0][1]  # Second argument to sms.send
        assert "KES 5,000.00" in message
        assert "MavunoSure" in message
        assert "approved" in message
        assert "payment sent" in message


@pytest.mark.asyncio
async def test_send_payment_notification_with_decimal_amount(mock_africastalking_response_success):
    """Test payment notification with decimal amount formatting"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_success
        
        # Execute with decimal amount
        result = await sms_service.send_payment_notification(
            phone_number="+254712345678",
            amount=12345.67
        )
        
        # Verify
        assert result is True
        
        # Verify amount is formatted correctly with comma separator
        call_args = mock_to_thread.call_args
        message = call_args[0][1]
        assert "KES 12,345.67" in message


@pytest.mark.asyncio
async def test_send_payment_notification_without_claim_id(mock_africastalking_response_success):
    """Test payment notification without claim ID"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_success
        
        # Execute without claim_id
        result = await sms_service.send_payment_notification(
            phone_number="+254712345678",
            amount=5000.00
        )
        
        # Verify
        assert result is True


@pytest.mark.asyncio
async def test_send_payment_notification_failure(mock_africastalking_response_failure):
    """Test payment notification SMS sending failure"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = mock_africastalking_response_failure
        
        # Execute
        result = await sms_service.send_payment_notification(
            phone_number="+254712345678",
            amount=5000.00,
            claim_id="claim-123"
        )
        
        # Verify
        assert result is False


@pytest.mark.asyncio
async def test_send_payment_notification_exception():
    """Test payment notification with exception"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.side_effect = Exception("Network timeout")
        
        # Execute
        result = await sms_service.send_payment_notification(
            phone_number="+254712345678",
            amount=5000.00
        )
        
        # Verify
        assert result is False


@pytest.mark.asyncio
async def test_send_payment_notification_empty_response():
    """Test payment notification with empty API response"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        # Return response without Recipients
        mock_to_thread.return_value = {
            'SMSMessageData': {
                'Message': 'Error',
                'Recipients': []
            }
        }
        
        # Execute
        result = await sms_service.send_payment_notification(
            phone_number="+254712345678",
            amount=5000.00
        )
        
        # Verify
        assert result is False


@pytest.mark.asyncio
async def test_send_payment_notification_malformed_response():
    """Test payment notification with malformed API response"""
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        # Return malformed response
        mock_to_thread.return_value = {}
        
        # Execute
        result = await sms_service.send_payment_notification(
            phone_number="+254712345678",
            amount=5000.00
        )
        
        # Verify
        assert result is False
