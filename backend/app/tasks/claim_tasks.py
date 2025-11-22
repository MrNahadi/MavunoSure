"""Celery tasks for claim processing"""

import logging
from uuid import UUID
from datetime import datetime
from celery import chain
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.claim_service import claim_service
from app.services.satellite_service import satellite_service
from app.services.weighted_verification_service import weighted_verification_service
from app.schemas.claim import ClaimUpdate, ClaimStatus
from app.schemas.verification import GroundTruth, CropCondition

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """Get database session for tasks"""
    return SessionLocal()


@celery_app.task(
    bind=True,
    name="process_claim_satellite_verification",
    max_retries=3,
    default_retry_delay=60
)
def process_claim_satellite_verification(self, claim_id: str):
    """
    Task to process satellite verification for a claim
    
    Args:
        claim_id: UUID of the claim to process
        
    Returns:
        dict with satellite verification results
        
    Raises:
        Exception: If satellite verification fails after retries
    """
    logger.info(f"Starting satellite verification for claim {claim_id}")
    
    db = get_db()
    try:
        # Get claim from database
        claim = claim_service.get_claim_by_id(UUID(claim_id), db)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")
        
        # Get farm GPS coordinates
        if not claim.farm:
            raise ValueError(f"Farm not found for claim {claim_id}")
        
        lat = float(claim.farm.gps_lat)
        lng = float(claim.farm.gps_lng)
        claim_date = claim.created_at
        
        # Query satellite data
        try:
            space_truth = satellite_service.verify_claim(lat, lng, claim_date)
        except Exception as e:
            logger.error(f"Satellite verification failed for claim {claim_id}: {str(e)}")
            # Retry the task
            raise self.retry(exc=e)
        
        # Update claim with Space Truth data
        update_data = ClaimUpdate(
            space_truth=space_truth
        )
        claim_service.update_claim(UUID(claim_id), update_data, db)
        
        logger.info(
            f"Satellite verification completed for claim {claim_id}: "
            f"NDMI={space_truth.ndmi_value:.3f}, verdict={space_truth.verdict}"
        )
        
        return {
            "claim_id": claim_id,
            "ndmi_value": space_truth.ndmi_value,
            "ndmi_14day_avg": space_truth.ndmi_14day_avg,
            "satellite_verdict": space_truth.verdict.value,
            "observation_date": space_truth.observation_date.isoformat(),
            "cloud_cover_pct": space_truth.cloud_cover_pct
        }
        
    except Exception as e:
        logger.error(f"Error in satellite verification task for claim {claim_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="process_claim_weighted_algorithm",
    max_retries=3,
    default_retry_delay=30
)
def process_claim_weighted_algorithm(self, claim_id: str, satellite_result: dict = None):
    """
    Task to process weighted algorithm verification for a claim
    
    Args:
        claim_id: UUID of the claim to process
        satellite_result: Result from satellite verification task (optional)
        
    Returns:
        dict with weighted verification results
        
    Raises:
        Exception: If weighted algorithm fails after retries
    """
    logger.info(f"Starting weighted algorithm for claim {claim_id}")
    
    db = get_db()
    try:
        # Get claim from database
        claim = claim_service.get_claim_by_id(UUID(claim_id), db)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")
        
        # Verify Space Truth data is available
        if not claim.ndmi_value:
            raise ValueError(f"Space Truth data not available for claim {claim_id}")
        
        # Build Ground Truth object
        ground_truth = GroundTruth(
            ml_class=CropCondition(claim.ml_class),
            ml_confidence=claim.ml_confidence,
            top_three_classes=[(CropCondition(cls), conf) for cls, conf in claim.top_three_classes] if claim.top_three_classes else [],
            device_tilt=claim.device_tilt,
            device_azimuth=claim.device_azimuth,
            capture_gps_lat=claim.capture_gps_lat,
            capture_gps_lng=claim.capture_gps_lng
        )
        
        # Build Space Truth object
        from app.services.satellite_service import SpaceTruth, SatelliteVerdict
        space_truth = SpaceTruth(
            ndmi_value=claim.ndmi_value,
            ndmi_14day_avg=claim.ndmi_14day_avg,
            observation_date=claim.observation_date,
            cloud_cover_pct=claim.cloud_cover_pct,
            verdict=SatelliteVerdict(claim.satellite_verdict)
        )
        
        # Run weighted verification algorithm
        try:
            verification_result = weighted_verification_service.verify(
                ground_truth=ground_truth,
                space_truth=space_truth,
                claim_date=claim.created_at
            )
        except Exception as e:
            logger.error(f"Weighted algorithm failed for claim {claim_id}: {str(e)}")
            raise self.retry(exc=e)
        
        # Update claim with verification result
        update_data = ClaimUpdate(
            verification_result=verification_result
        )
        claim_service.update_claim(UUID(claim_id), update_data, db)
        
        logger.info(
            f"Weighted algorithm completed for claim {claim_id}: "
            f"status={verification_result.status}, score={verification_result.score:.2f}"
        )
        
        return {
            "claim_id": claim_id,
            "status": verification_result.status.value,
            "weighted_score": verification_result.score,
            "explanation": verification_result.explanation,
            "ground_truth_confidence": verification_result.ground_truth_confidence,
            "space_truth_confidence": verification_result.space_truth_confidence
        }
        
    except Exception as e:
        logger.error(f"Error in weighted algorithm task for claim {claim_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="process_claim_payment",
    max_retries=3,
    default_retry_delay=120
)
def process_claim_payment(self, claim_id: str, verification_result: dict = None):
    """
    Task to process payment for an approved claim
    
    Implements requirements 9.1, 9.4, 9.5:
    - Trigger payment when claim status changes to Approved
    - Retry logic with exponential backoff (up to 3 attempts)
    - Flag claims for manual processing after failed retries
    - Update claim payout_status in database
    
    Args:
        claim_id: UUID of the claim to process
        verification_result: Result from weighted algorithm task (optional)
        
    Returns:
        dict with payment processing results
        
    Raises:
        Exception: If payment processing fails after retries
    """
    logger.info(f"Starting payment processing for claim {claim_id}")
    
    db = get_db()
    try:
        # Get claim from database
        claim = claim_service.get_claim_by_id(UUID(claim_id), db)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")
        
        # Only process payment for auto-approved claims
        if claim.status != ClaimStatus.AUTO_APPROVED.value:
            logger.info(
                f"Skipping payment for claim {claim_id} - status is {claim.status}, "
                "not auto_approved"
            )
            return {
                "claim_id": claim_id,
                "payment_processed": False,
                "reason": f"Claim status is {claim.status}"
            }
        
        # Import payment service
        from app.services.payment_service import payment_service
        
        # Process payout with retry logic
        try:
            # Run async payment processing
            import asyncio
            payment_success = asyncio.run(
                payment_service.process_payout(UUID(claim_id), db)
            )
            
            if payment_success:
                logger.info(f"Payment processed successfully for claim {claim_id}")
                return {
                    "claim_id": claim_id,
                    "payment_processed": True,
                    "status": "paid",
                    "message": "Payment completed successfully"
                }
            else:
                logger.error(f"Payment processing failed for claim {claim_id}")
                return {
                    "claim_id": claim_id,
                    "payment_processed": False,
                    "status": "failed_manual_review_required",
                    "message": "Payment failed after all retries. Flagged for manual processing."
                }
                
        except Exception as payment_error:
            logger.error(
                f"Error processing payment for claim {claim_id}: {str(payment_error)}"
            )
            # Retry the task if we haven't exceeded max retries
            raise self.retry(exc=payment_error)
        
    except Exception as e:
        logger.error(f"Error in payment processing task for claim {claim_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(name="process_claim_workflow")
def process_claim_workflow(claim_id: str):
    """
    Orchestrate the complete claim processing workflow
    
    Chains together:
    1. Satellite verification
    2. Weighted algorithm execution
    3. Payment processing (if approved)
    
    Args:
        claim_id: UUID of the claim to process
        
    Returns:
        Celery chain result
    """
    logger.info(f"Starting claim processing workflow for claim {claim_id}")
    
    # Create task chain
    workflow = chain(
        process_claim_satellite_verification.s(claim_id),
        process_claim_weighted_algorithm.s(claim_id),
        process_claim_payment.s(claim_id)
    )
    
    # Execute the chain
    result = workflow.apply_async()
    
    logger.info(f"Claim processing workflow queued for claim {claim_id}")
    
    return result
