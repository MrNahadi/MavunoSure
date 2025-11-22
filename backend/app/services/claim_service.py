"""Claim service for business logic"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID
from typing import List, Optional, Tuple
from app.models.claim import Claim
from app.models.farm import Farm
from app.models.agent import Agent
from app.schemas.claim import (
    ClaimCreate,
    ClaimUpdate,
    ClaimResponse,
    ClaimCreateResponse,
    ClaimStatus,
    ClaimListResponse
)
from app.services.storage_service import storage_service


class ClaimService:
    """Service for claim-related operations"""
    
    def create_claim(self, claim_data: ClaimCreate, db: Session) -> ClaimCreateResponse:
        """
        Create a new claim
        
        Args:
            claim_data: Claim creation data
            db: Database session
            
        Returns:
            ClaimCreateResponse with claim_id
        """
        # Verify agent exists
        agent = db.query(Agent).filter(Agent.id == claim_data.agent_id).first()
        if not agent:
            raise ValueError(f"Agent with id {claim_data.agent_id} not found")
        
        # Verify farm exists
        farm = db.query(Farm).filter(Farm.id == claim_data.farm_id).first()
        if not farm:
            raise ValueError(f"Farm with id {claim_data.farm_id} not found")
        
        # Create claim model
        claim = Claim(
            agent_id=claim_data.agent_id,
            farm_id=claim_data.farm_id,
            status=ClaimStatus.PENDING.value,
            ml_class=claim_data.ground_truth.ml_class.value,
            ml_confidence=claim_data.ground_truth.ml_confidence,
            top_three_classes=[
                [cls.value, conf] for cls, conf in claim_data.ground_truth.top_three_classes
            ],
            device_tilt=claim_data.ground_truth.device_tilt,
            device_azimuth=claim_data.ground_truth.device_azimuth,
            capture_gps_lat=claim_data.ground_truth.capture_gps_lat,
            capture_gps_lng=claim_data.ground_truth.capture_gps_lng,
            image_url=""  # Will be updated after upload
        )
        
        # Add to database to get ID
        db.add(claim)
        db.flush()
        
        # Upload image
        try:
            image_url = storage_service.upload_claim_image(
                claim_data.image_data,
                claim.id
            )
            claim.image_url = image_url
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to upload image: {str(e)}")
        
        db.commit()
        db.refresh(claim)
        
        return ClaimCreateResponse(
            claim_id=claim.id,
            status=ClaimStatus.PENDING,
            message="Claim submitted successfully. Processing will begin shortly."
        )
    
    def get_claim_by_id(self, claim_id: UUID, db: Session) -> Optional[Claim]:
        """
        Get claim by ID
        
        Args:
            claim_id: Claim UUID
            db: Database session
            
        Returns:
            Claim model or None if not found
        """
        return db.query(Claim).filter(Claim.id == claim_id).first()
    
    def get_claims(
        self,
        db: Session,
        agent_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Claim], int]:
        """
        Get claims with optional filtering and pagination
        
        Args:
            db: Database session
            agent_id: Filter by agent ID
            status: Filter by status
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (claims list, total count)
        """
        query = db.query(Claim)
        
        # Apply filters
        filters = []
        if agent_id:
            filters.append(Claim.agent_id == agent_id)
        if status:
            filters.append(Claim.status == status)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        claims = query.order_by(Claim.created_at.desc()).offset(offset).limit(page_size).all()
        
        return claims, total
    
    def update_claim(self, claim_id: UUID, update_data: ClaimUpdate, db: Session) -> Optional[Claim]:
        """
        Update claim data
        
        Args:
            claim_id: Claim UUID
            update_data: Update data
            db: Database session
            
        Returns:
            Updated Claim model or None if not found
        """
        claim = self.get_claim_by_id(claim_id, db)
        if not claim:
            return None
        
        # Update status
        if update_data.status:
            claim.status = update_data.status.value
        
        # Update Space Truth data
        if update_data.space_truth:
            claim.ndmi_value = update_data.space_truth.ndmi_value
            claim.ndmi_14day_avg = update_data.space_truth.ndmi_14day_avg
            claim.satellite_verdict = update_data.space_truth.satellite_verdict.value
            claim.observation_date = update_data.space_truth.observation_date
            claim.cloud_cover_pct = update_data.space_truth.cloud_cover_pct
        
        # Update Verification Result
        if update_data.verification_result:
            claim.weighted_score = update_data.verification_result.weighted_score
            claim.status = update_data.verification_result.status.value
            claim.verdict_explanation = update_data.verification_result.verdict_explanation
            claim.ground_truth_confidence = update_data.verification_result.ground_truth_confidence
            claim.space_truth_confidence = update_data.verification_result.space_truth_confidence
        
        # Update Payment data
        if update_data.payout_amount is not None:
            claim.payout_amount = update_data.payout_amount
        if update_data.payout_status:
            claim.payout_status = update_data.payout_status
        if update_data.payout_reference:
            claim.payout_reference = update_data.payout_reference
        
        db.commit()
        db.refresh(claim)
        
        return claim
    
    def update_claim_status(self, claim_id: UUID, status: ClaimStatus, db: Session) -> Optional[Claim]:
        """
        Update claim status
        
        Args:
            claim_id: Claim UUID
            status: New status
            db: Database session
            
        Returns:
            Updated Claim model or None if not found
        """
        claim = self.get_claim_by_id(claim_id, db)
        if not claim:
            return None
        
        claim.status = status.value
        db.commit()
        db.refresh(claim)
        
        return claim


# Singleton instance
claim_service = ClaimService()
