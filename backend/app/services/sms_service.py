"""SMS service using Africa's Talking API"""

import africastalking
import asyncio
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """
    Service for sending SMS via Africa's Talking
    
    Implements requirements 9.2, 9.3:
    - Send SMS notifications to farmers on successful payment
    - Include claim amount in Kenya Shillings (KES)
    """
    
    def __init__(self):
        """Initialize Africa's Talking SDK"""
        # Initialize SDK
        africastalking.initialize(
            username=settings.AFRICASTALKING_USERNAME,
            api_key=settings.AFRICASTALKING_API_KEY
        )
        self.sms = africastalking.SMS
    
    async def send_otp(self, phone_number: str, otp: str) -> bool:
        """
        Send OTP via SMS
        
        Args:
            phone_number: Recipient phone number in international format (e.g., +254712345678)
            otp: One-time password to send
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        try:
            message = f"Your MavunoSure verification code is: {otp}. Valid for 5 minutes."
            
            # Send SMS in thread pool to avoid blocking
            response = await asyncio.to_thread(
                self.sms.send,
                message,
                [phone_number]
            )
            
            logger.info(f"OTP SMS sent to {phone_number}: {response}")
            
            # Check if SMS was sent successfully
            if response.get('SMSMessageData', {}).get('Recipients'):
                recipient = response['SMSMessageData']['Recipients'][0]
                if recipient.get('status') == 'Success':
                    logger.info(f"OTP SMS delivered successfully to {phone_number}")
                    return True
                else:
                    logger.warning(
                        f"OTP SMS failed for {phone_number}: "
                        f"status={recipient.get('status')}, "
                        f"cost={recipient.get('cost')}"
                    )
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send OTP SMS to {phone_number}: {str(e)}")
            return False
    
    async def send_message(self, phone_number: str, message: str) -> bool:
        """
        Send generic SMS message
        
        Args:
            phone_number: Recipient phone number in international format (e.g., +254712345678)
            message: Message content to send
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        try:
            # Send SMS in thread pool to avoid blocking
            response = await asyncio.to_thread(
                self.sms.send,
                message,
                [phone_number]
            )
            
            logger.info(f"SMS sent to {phone_number}: {response}")
            
            # Check if SMS was sent successfully
            if response.get('SMSMessageData', {}).get('Recipients'):
                recipient = response['SMSMessageData']['Recipients'][0]
                if recipient.get('status') == 'Success':
                    logger.info(
                        f"SMS delivered successfully to {phone_number}, "
                        f"messageId={recipient.get('messageId')}, "
                        f"cost={recipient.get('cost')}"
                    )
                    return True
                else:
                    logger.warning(
                        f"SMS failed for {phone_number}: "
                        f"status={recipient.get('status')}, "
                        f"cost={recipient.get('cost')}"
                    )
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    async def send_payment_notification(
        self,
        phone_number: str,
        amount: float,
        claim_id: Optional[str] = None
    ) -> bool:
        """
        Send payment notification SMS to farmer
        
        Implements requirements 9.2, 9.3:
        - Send SMS on successful payment
        - Include amount in Kenya Shillings (KES)
        
        Args:
            phone_number: Farmer's phone number in international format
            amount: Payment amount in KES
            claim_id: Optional claim ID for reference
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        try:
            # Format message with amount in KES (requirement 9.3)
            message = f"MavunoSure: Your claim for KES {amount:,.2f} has been approved and payment sent."
            
            if claim_id:
                logger.info(f"Sending payment notification for claim {claim_id} to {phone_number}")
            
            # Send SMS
            success = await self.send_message(phone_number, message)
            
            if success:
                logger.info(
                    f"Payment notification sent successfully to {phone_number} "
                    f"for amount KES {amount:,.2f}"
                )
            else:
                logger.error(
                    f"Failed to send payment notification to {phone_number} "
                    f"for amount KES {amount:,.2f}"
                )
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error sending payment notification to {phone_number}: {str(e)}"
            )
            return False


# Singleton instance
sms_service = SMSService()
