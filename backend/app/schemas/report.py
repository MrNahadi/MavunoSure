"""Report Pydantic schemas"""

from pydantic import BaseModel, Field
from uuid import UUID


class PDFReportResponse(BaseModel):
    """Schema for PDF report generation response"""
    claim_id: UUID = Field(..., description="Claim ID for which report was generated")
    pdf_url: str = Field(..., description="Download URL for the PDF report")
    message: str = Field(..., description="Response message")
    expires_in_days: int = Field(..., description="Number of days until download link expires")
