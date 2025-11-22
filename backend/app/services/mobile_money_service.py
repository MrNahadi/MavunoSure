"""Mobile Money service for payment processing"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)


class PaymentTransaction:
    """Payment transaction result"""
    
    def __init__(
        self,
        success: bool,
        transaction_id: str,
        message: str,
        amount: Decimal,
        phone_number: str
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.message = message
        self.amount = amount
        self.phone_number = phone_number
        self.timestamp = datetime.utcnow()


class MobileMoneyService:
    """
    Service for mobile money payment integration
    
    For MVP, this is a simulated implementation that logs transactions
    In production, this would integrate with actual mobile money APIs
    (e.g., M-Pesa, Airtel Money, etc.)
    
    Implements requirement 9.1
    """
    
    def __init__(self):
        """Initialize mobile money service"""
        self.api_url = settings.MOBILE_MONEY_API_URL
        self.api_key = settings.MOBILE_MONEY_API_KEY
        self.is_production = settings.ENVIRONMENT == "production"
    
    async def send_payment(
        self,
        phone_number: str,
        amount: Decimal,
        reference: str,
        db: Session
    ) -> PaymentTransaction:
        """
        Send mobile money payment to farmer
        
        Args:
            phone_number: Farmer's phone number (format: +254XXXXXXXXX)
            amount: Payment amount in KES
            reference: Payment reference (claim_id)
            db: Database session for logging
            
        Returns:
            PaymentTransaction with result details
        """
        logger.info(
            f"Initiating mobile money payment: phone={phone_number}, "
            f"amount={amount}, reference={reference}"
        )
        
        # Validate inputs
        if not phone_number or not phone_number.startswith("+254"):
            logger.error(f"Invalid phone number format: {phone_number}")
            return PaymentTransaction(
                success=False,
                transaction_id="",
                message="Invalid phone number format. Must start with +254",
                amount=amount,
                phone_number=phone_number
            )
        
        if amount <= 0:
            logger.error(f"Invalid payment amount: {amount}")
            return PaymentTransaction(
                success=False,
                transaction_id="",
                message="Invalid payment amount. Must be greater than 0",
                amount=amount,
                phone_number=phone_number
            )
        
        # Generate transaction ID
        transaction_id = f"MM{uuid.uuid4().hex[:12].upper()}"
        
        # For MVP, simulate payment processing
        # In production, this would call actual mobile money API
        if self.is_production and self.api_url:
            # Production implementation would go here
            # Example:
            # response = await self._call_mobile_money_api(
            #     phone_number, amount, reference, transaction_id
            # )
            logger.warning("Production mobile money API not yet implemented")
            success = False
            message = "Mobile money API not configured"
        else:
            # Simulated success for MVP/development
            success = True
            message = f"Payment of KES {amount:,.2f} sent successfully (simulated)"
            logger.info(
                f"Simulated payment successful: transaction_id={transaction_id}, "
                f"phone={phone_number}, amount={amount}"
            )
        
        # Log transaction to database
        await self._log_transaction(
            db=db,
            transaction_id=transaction_id,
            phone_number=phone_number,
            amount=amount,
            reference=reference,
            success=success,
            message=message
        )
        
        return PaymentTransaction(
            success=success,
            transaction_id=transaction_id,
            message=message,
            amount=amount,
            phone_number=phone_number
        )
    
    async def _log_transaction(
        self,
        db: Session,
        transaction_id: str,
        phone_number: str,
        amount: Decimal,
        reference: str,
        success: bool,
        message: str
    ) -> None:
        """
        Log payment transaction to database
        
        Args:
            db: Database session
            transaction_id: Unique transaction identifier
            phone_number: Recipient phone number
            amount: Payment amount
            reference: Payment reference (claim_id)
            success: Whether payment was successful
            message: Transaction message/status
        """
        from app.models.payment_transaction import PaymentTransactionModel
        
        try:
            transaction = PaymentTransactionModel(
                transaction_id=transaction_id,
                claim_id=reference,
                phone_number=phone_number,
                amount=amount,
                status="completed" if success else "failed",
                message=message,
                created_at=datetime.utcnow()
            )
            
            db.add(transaction)
            db.commit()
            
            logger.info(f"Payment transaction logged: {transaction_id}")
            
        except Exception as e:
            logger.error(f"Failed to log payment transaction: {str(e)}")
            db.rollback()
    
    async def check_payment_status(self, transaction_id: str) -> dict:
        """
        Check status of a payment transaction
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            Dictionary with transaction status details
        """
        logger.info(f"Checking payment status: transaction_id={transaction_id}")
        
        # For MVP, return simulated status
        # In production, this would query the mobile money API
        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "message": "Payment completed successfully (simulated)"
        }


# Singleton instance
mobile_money_service = MobileMoneyService()
