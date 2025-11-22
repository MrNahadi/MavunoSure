"""Report generation API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.core.dependencies import get_current_agent
from app.models.agent import Agent
from app.services.report_service import report_service
from app.schemas.report import PDFReportResponse

router = APIRouter()


@router.get(
    "/{claim_id}/pdf",
    response_model=PDFReportResponse,
    summary="Generate PDF report for claim",
    description="Generate a comprehensive PDF report for a specific claim with all verification details"
)
async def generate_claim_pdf(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Generate a comprehensive PDF report for a claim.
    
    - **claim_id**: UUID of the claim to generate report for
    
    Returns a download URL for the generated PDF report valid for 7 days.
    
    The PDF includes:
    - Claim photo with proper sizing
    - GPS coordinates and timestamps
    - Ground Truth section with ML classification and confidence scores
    - Top 3 predicted classes for explainability
    - Space Truth section with NDMI values and satellite observation date
    - Satellite data visualization (NDMI chart)
    - Final verification result with weighted score and explanation
    """
    try:
        # Generate PDF report
        pdf_url = await report_service.generate_claim_pdf(claim_id, db)
        
        return PDFReportResponse(
            claim_id=claim_id,
            pdf_url=pdf_url,
            message="PDF report generated successfully",
            expires_in_days=7
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error generating PDF: {str(e)}"
        )
