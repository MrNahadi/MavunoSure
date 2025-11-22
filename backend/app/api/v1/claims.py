"""Claim management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from math import ceil

from app.database import get_db
from app.core.dependencies import get_current_agent
from app.models.agent import Agent
from app.schemas.claim import (
    ClaimCreate,
    ClaimCreateResponse,
    ClaimResponse,
    ClaimListResponse,
    ClaimStatus
)
from app.services.claim_service import claim_service

router = APIRouter()


@router.post(
    "",
    response_model=ClaimCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new claim",
    description="Create a new insurance claim with Ground Truth data and image"
)
async def create_claim(
    claim_data: ClaimCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Submit a new insurance claim with the following information:
    
    - **agent_id**: UUID of the agent submitting the claim
    - **farm_id**: UUID of the farm associated with the claim
    - **ground_truth**: Ground Truth data including ML classification and metadata
    - **image_data**: Base64 encoded image data
    
    The claim will be processed asynchronously:
    1. Image uploaded to storage
    2. Satellite verification queued
    3. Weighted algorithm execution queued
    4. Payment processing (if approved)
    
    Returns the claim_id immediately for tracking.
    """
    try:
        # Create claim and upload image
        response = claim_service.create_claim(claim_data, db)
        
        # Enqueue async processing workflow
        from app.tasks.claim_tasks import process_claim_workflow
        background_tasks.add_task(
            process_claim_workflow.delay,
            str(response.claim_id)
        )
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create claim: {str(e)}"
        )


@router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
    summary="Get claim by ID",
    description="Retrieve detailed information about a specific claim"
)
async def get_claim(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Get detailed information about a specific claim by ID.
    
    - **claim_id**: UUID of the claim to retrieve
    
    Returns full claim details including:
    - Ground Truth data (ML classification, device metadata)
    - Space Truth data (satellite NDMI, verdict) if available
    - Verification result (weighted score, status, explanation) if available
    - Payment information if applicable
    """
    claim = claim_service.get_claim_by_id(claim_id, db)
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )
    
    return ClaimResponse.from_orm_model(claim)


@router.get(
    "",
    response_model=ClaimListResponse,
    summary="List claims with filtering",
    description="Retrieve a paginated list of claims with optional filtering"
)
async def list_claims(
    agentId: Optional[UUID] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by claim status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    List claims with optional filtering and pagination.
    
    Query parameters:
    - **agentId**: Filter claims by agent UUID (optional)
    - **status**: Filter by claim status (pending, auto_approved, flagged_for_review, rejected, paid)
    - **page**: Page number, starting from 1
    - **page_size**: Number of items per page (max 100)
    
    Returns paginated list of claims with metadata.
    """
    try:
        # Validate status if provided
        if status:
            try:
                ClaimStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Must be one of: {', '.join([s.value for s in ClaimStatus])}"
                )
        
        # Get claims
        claims, total = claim_service.get_claims(
            db=db,
            agent_id=agentId,
            status=status,
            page=page,
            page_size=page_size
        )
        
        # Convert to response models
        claim_responses = [ClaimResponse.from_orm_model(claim) for claim in claims]
        
        # Calculate total pages
        total_pages = ceil(total / page_size) if total > 0 else 0
        
        return ClaimListResponse(
            claims=claim_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve claims: {str(e)}"
        )


@router.patch(
    "/{claim_id}/status",
    response_model=ClaimResponse,
    summary="Update claim status",
    description="Manually update the status of a claim (for review workflow)"
)
async def update_claim_status(
    claim_id: UUID,
    new_status: ClaimStatus,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Update the status of a claim. Used for manual review workflow.
    
    - **claim_id**: UUID of the claim to update
    - **new_status**: New status to set
    
    This endpoint is primarily used by reviewers to manually approve or reject
    claims that have been flagged for review.
    """
    claim = claim_service.update_claim_status(claim_id, new_status, db)
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )
    
    return ClaimResponse.from_orm_model(claim)
