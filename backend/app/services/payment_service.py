"""Payment service for claim payout processing"""

import logging
import asyncio
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.farm import Farm
from app.schemas.claim import ClaimStatus, ClaimUpdate
from app.services.mobile_money_service import mobile_money_service
from app.services.sms_service import sms_service

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for processing claim payouts
    
    Implements requirements 9.1, 9.4, 9.5:
    - Trigger payments when claims are approved
    - Retry logic with exponential backoff
    - Flag claims for manual processing after failures
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    BASE_BACKOFF_SECONDS = 2
    
    # Default payout amount for MVP (in KES)
    DEFAULT_PAYOUT_AMOUNT = Decimal("5000.00")
    
    async def process_payout(
        self,
        claim_id: UUID,
        db: Session
    ) -> bool:
        """
        Process payout for an approved claim
        
        Implements requirements 9.1, 9.4, 9.5:
        - Trigger mobile money payment
        - Retry up to 3 times with exponential backoff
        - Send SMS notification on success
        - Flag for manual processing on failure
        
        Args:
            claim_id: UUID of the claim to process payment for
            db: Database session
            
        Returns:
            bool: True if payment was successful, False otherwise
        """
        logger.info(f"Starting payout processing for claim {claim_id}")
        
        # Get claim from database
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            logger.error(f"Claim {claim_id} not found")
            raise ValueError(f"Claim {claim_id} not found")
        
        # Verify claim is in approved status
        if claim.status != ClaimStatus.AUTO_APPROVED.value:
            logger.warning(
                f"Claim {claim_id} is not in auto_approved status (current: {claim.status}). "
                "Skipping payment."
            )
            return False
        
        # Get farm to retrieve farmer phone number
        farm = db.query(Farm).filter(Farm.id == claim.farm_id).first()
        if not farm:
            logger.error(f"Farm {claim.farm_id} not found for claim {claim_id}")
            raise ValueError(f"Farm not found for claim {claim_id}")
        
        farmer_phone = farm.phone_number
        payout_amount = claim.payout_amount or self.DEFAULT_PAYOUT_AMOUNT
        
        # Update claim with payout amount if not set
        if not claim.payout_amount:
            claim.payout_amount = payout_amount
            claim.payout_status = "pending"
            db.commit()
        
        # Attempt payment with retry logic
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    f"Payment attempt {attempt + 1}/{self.MAX_RETRIES} for claim {claim_id}"
                )
                
                # Trigger mobile money payment
                payment_result = await mobile_money_service.send_payment(
                    phone_number=farmer_phone,
                    amount=payout_amount,
                    reference=str(claim_id),
                    db=db
                )
                
                if payment_result.success:
                    # Payment successful - update claim status
                    claim.status = ClaimStatus.PAID.value
                    claim.payout_status = "completed"
                    claim.payout_reference = payment_result.transaction_id
                    db.commit()
                    
                    logger.info(
                        f"Payment successful for claim {claim_id}: "
                        f"transaction_id={payment_result.transaction_id}"
                    )
                    
                    # Send SMS notification to farmer (requirement 9.2, 9.3)
                    try:
                        await sms_service.send_payment_notification(
                            phone_number=farmer_phone,
                            amount=float(payout_amount),
                            claim_id=str(claim_id)
                        )
                        logger.info(f"Payment notification SMS sent to {farmer_phone}")
                    except Exception as sms_error:
                        # Log SMS error but don't fail the payment
                        logger.error(f"Failed to send payment notification SMS: {str(sms_error)}")
                    
                    return True
                
                else:
                    # Payment failed - log and retry
                    logger.warning(
                        f"Payment attempt {attempt + 1} failed for claim {claim_id}: "
                        f"{payment_result.message}"
                    )
                    
                    # If not last attempt, wait with exponential backoff
                    if attempt < self.MAX_RETRIES - 1:
                        backoff_seconds = self.BASE_BACKOFF_SECONDS ** (attempt + 1)
                        logger.info(f"Waiting {backoff_seconds}s before retry...")
                        await asyncio.sleep(backoff_seconds)
                    
            except Exception as e:
                logger.error(
                    f"Error during payment attempt {attempt + 1} for claim {claim_id}: {str(e)}"
                )
                
                # If not last attempt, wait with exponential backoff
                if attempt < self.MAX_RETRIES - 1:
                    backoff_seconds = self.BASE_BACKOFF_SECONDS ** (attempt + 1)
                    logger.info(f"Waiting {backoff_seconds}s before retry...")
                    await asyncio.sleep(backoff_seconds)
        
        # All retries failed - flag for manual processing (requirement 9.5)
        logger.error(
            f"All payment attempts failed for claim {claim_id}. "
            "Flagging for manual processing."
        )
        
        claim.payout_status = "failed_manual_review_required"
        db.commit()
        
        return False
    
    async def retry_failed_payment(
        self,
        claim_id: UUID,
        db: Session
    ) -> bool:
        """
        Retry a failed payment manually
        
        Args:
            claim_id: UUID of the claim to retry payment for
            db: Database session
            
        Returns:
            bool: True if payment was successful, False otherwise
        """
        logger.info(f"Manually retrying payment for claim {claim_id}")
        
        # Get claim
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")
        
        # Verify claim has failed payment status
        if claim.payout_status != "failed_manual_review_required":
            logger.warning(
                f"Claim {claim_id} payout status is {claim.payout_status}, "
                "not failed_manual_review_required"
            )
            return False
        
        # Reset status and attempt payment
        claim.payout_status = "pending"
        db.commit()
        
        return await self.process_payout(claim_id, db)


# Singleton instance
payment_service = PaymentService()