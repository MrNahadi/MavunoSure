"""Report generation service for PDF exports"""

import io
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart

from app.models.claim import Claim
from app.models.farm import Farm
from app.config import settings


class ReportService:
    """Service for generating PDF reports"""
    
    def __init__(self):
        self.storage_provider = settings.STORAGE_PROVIDER
        self.bucket = settings.AWS_S3_BUCKET
        self._s3_client = None
    
    @property
    def s3_client(self):
        """Lazy load S3 client"""
        if self._s3_client is None and self.storage_provider == "s3":
            import boto3
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return self._s3_client
    
    async def generate_claim_pdf(self, claim_id: uuid.UUID, db: Session) -> str:
        """
        Generate comprehensive PDF report for a claim
        
        Args:
            claim_id: UUID of the claim
            db: Database session
            
        Returns:
            URL of the generated PDF (signed URL for S3, local path otherwise)
        """
        # Fetch claim data
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim with id {claim_id} not found")
        
        # Fetch farm data
        farm = db.query(Farm).filter(Farm.id == claim.farm_id).first()
        if not farm:
            raise ValueError(f"Farm with id {claim.farm_id} not found")
        
        # Generate PDF
        pdf_bytes = self._generate_pdf_content(claim, farm)
        
        # Upload PDF to storage
        pdf_url = await self._store_pdf(pdf_bytes, claim_id)
        
        return pdf_url
    
    def _generate_pdf_content(self, claim: Claim, farm: Farm) -> bytes:
        """Generate PDF content"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        # Title
        story.append(Paragraph("MavunoSure Claim Verification Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Claim ID and Date
        info_data = [
            ["Claim ID:", str(claim.id)],
            ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Claim Status:", claim.status.upper().replace("_", " ")]
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Farmer Information Section
        story.append(Paragraph("Farmer Information", heading_style))
        farmer_data = [
            ["Farmer Name:", farm.farmer_name],
            ["Farmer ID:", farm.farmer_id],
            ["Phone Number:", farm.phone_number],
            ["Crop Type:", farm.crop_type.title()],
            ["Farm GPS:", f"{float(farm.gps_lat):.6f}, {float(farm.gps_lng):.6f}"],
            ["Registration Date:", farm.registered_at.strftime("%Y-%m-%d")]
        ]
        farmer_table = Table(farmer_data, colWidths=[2*inch, 4*inch])
        farmer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(farmer_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Ground Truth Assessment Section
        story.append(Paragraph("Ground Truth Assessment", heading_style))
        
        # Add claim image if available
        story.append(self._add_claim_image(claim.image_url))
        story.append(Spacer(1, 0.2*inch))
        
        # Ground Truth data
        gt_data = [
            ["ML Classification:", claim.ml_class.replace("_", " ").title()],
            ["Confidence Score:", f"{claim.ml_confidence:.2%}"],
            ["Device Tilt:", f"{claim.device_tilt:.1f}°" if claim.device_tilt else "N/A"],
            ["Device Azimuth:", f"{claim.device_azimuth:.1f}°" if claim.device_azimuth else "N/A"],
            ["Capture GPS:", f"{float(claim.capture_gps_lat):.6f}, {float(claim.capture_gps_lng):.6f}" if claim.capture_gps_lat else "N/A"],
            ["Capture Time:", claim.created_at.strftime("%Y-%m-%d %H:%M:%S")]
        ]
        gt_table = Table(gt_data, colWidths=[2*inch, 4*inch])
        gt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(gt_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Top 3 Predicted Classes for Explainability
        if claim.top_three_classes:
            story.append(Paragraph("<b>Top 3 Predicted Classes (Explainability):</b>", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            top_classes_data = [["Rank", "Classification", "Confidence"]]
            for idx, (cls, conf) in enumerate(claim.top_three_classes[:3], 1):
                top_classes_data.append([
                    str(idx),
                    cls.replace("_", " ").title(),
                    f"{conf:.2%}"
                ])
            
            top_classes_table = Table(top_classes_data, colWidths=[0.8*inch, 3*inch, 1.5*inch])
            top_classes_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(top_classes_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Space Truth Assessment Section (if available)
        if claim.ndmi_value is not None:
            story.append(Paragraph("Space Truth Assessment (Satellite Data)", heading_style))
            
            st_data = [
                ["Current NDMI Value:", f"{claim.ndmi_value:.3f}"],
                ["14-Day Average NDMI:", f"{claim.ndmi_14day_avg:.3f}"],
                ["Satellite Verdict:", claim.satellite_verdict.replace("_", " ").title()],
                ["Observation Date:", claim.observation_date.strftime("%Y-%m-%d") if claim.observation_date else "N/A"],
                ["Cloud Cover:", f"{claim.cloud_cover_pct:.1f}%" if claim.cloud_cover_pct else "N/A"]
            ]
            st_table = Table(st_data, colWidths=[2*inch, 4*inch])
            st_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(st_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Add NDMI visualization chart
            story.append(self._create_ndmi_chart(claim.ndmi_value, claim.ndmi_14day_avg))
            story.append(Spacer(1, 0.3*inch))
        
        # Final Verification Result Section (if available)
        if claim.weighted_score is not None:
            story.append(Paragraph("Final Verification Result", heading_style))
            
            # Determine status color
            status_color = colors.green
            if claim.status == "rejected":
                status_color = colors.red
            elif claim.status == "flagged_for_review":
                status_color = colors.orange
            
            vr_data = [
                ["Weighted Score:", f"{claim.weighted_score:.2f}"],
                ["Ground Truth Confidence:", f"{claim.ground_truth_confidence:.2%}" if claim.ground_truth_confidence else "N/A"],
                ["Space Truth Confidence:", f"{claim.space_truth_confidence:.2%}" if claim.space_truth_confidence else "N/A"],
                ["Final Status:", claim.status.upper().replace("_", " ")],
            ]
            vr_table = Table(vr_data, colWidths=[2.5*inch, 3.5*inch])
            vr_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('BACKGROUND', (1, 3), (1, 3), status_color),
                ('TEXTCOLOR', (1, 3), (1, 3), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(vr_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Explanation
            if claim.verdict_explanation:
                story.append(Paragraph("<b>Explanation:</b>", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
                explanation_style = ParagraphStyle(
                    'Explanation',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    leftIndent=20,
                    rightIndent=20,
                    spaceAfter=10
                )
                story.append(Paragraph(claim.verdict_explanation, explanation_style))
        
        # Payment Information (if available)
        if claim.payout_amount:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("Payment Information", heading_style))
            
            payment_data = [
                ["Payout Amount:", f"KES {float(claim.payout_amount):,.2f}"],
                ["Payout Status:", claim.payout_status.upper() if claim.payout_status else "N/A"],
                ["Payout Reference:", claim.payout_reference if claim.payout_reference else "N/A"]
            ]
            payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
            payment_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(payment_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph(
            f"Generated by MavunoSure Platform | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    def _add_claim_image(self, image_url: str) -> RLImage:
        """Add claim image to PDF with proper sizing"""
        try:
            # For local development, handle local file paths
            if image_url.startswith("/uploads/"):
                image_path = image_url.replace("/uploads/", "uploads/")
                img = RLImage(image_path, width=4*inch, height=3*inch)
            else:
                # For S3 URLs, download the image
                import requests
                from PIL import Image as PILImage
                
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                
                # Load image and create ReportLab image
                pil_img = PILImage.open(io.BytesIO(response.content))
                
                # Calculate aspect ratio
                aspect = pil_img.width / pil_img.height
                
                # Set max dimensions
                max_width = 4 * inch
                max_height = 3 * inch
                
                if aspect > max_width / max_height:
                    width = max_width
                    height = max_width / aspect
                else:
                    height = max_height
                    width = max_height * aspect
                
                img = RLImage(io.BytesIO(response.content), width=width, height=height)
            
            return img
        except Exception as e:
            # Return placeholder text if image cannot be loaded
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            styles = getSampleStyleSheet()
            return Paragraph(f"[Image unavailable: {str(e)}]", styles['Normal'])
    
    def _create_ndmi_chart(self, current_ndmi: float, avg_ndmi: float) -> Drawing:
        """Create NDMI comparison bar chart"""
        drawing = Drawing(400, 200)
        
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.height = 125
        chart.width = 300
        chart.data = [[current_ndmi, avg_ndmi]]
        chart.categoryAxis.categoryNames = ['Current NDMI', '14-Day Average']
        chart.valueAxis.valueMin = min(current_ndmi, avg_ndmi, -0.3)
        chart.valueAxis.valueMax = max(current_ndmi, avg_ndmi, 0.3)
        chart.bars[0].fillColor = colors.HexColor('#1a5490')
        
        drawing.add(chart)
        return drawing
    
    async def _store_pdf(self, pdf_bytes: bytes, claim_id: uuid.UUID) -> str:
        """
        Store PDF in storage and return URL
        
        Args:
            pdf_bytes: PDF file content
            claim_id: Claim UUID
            
        Returns:
            URL to access the PDF
        """
        filename = f"reports/{claim_id}/{uuid.uuid4()}.pdf"
        
        if self.storage_provider == "s3":
            return self._upload_to_s3(pdf_bytes, filename)
        else:
            return self._upload_locally(pdf_bytes, filename)
    
    def _upload_to_s3(self, pdf_bytes: bytes, filename: str) -> str:
        """Upload PDF to S3 and return signed URL"""
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=pdf_bytes,
                ContentType='application/pdf'
            )
            
            # Generate signed URL valid for 7 days
            signed_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': filename},
                ExpiresIn=7 * 24 * 60 * 60  # 7 days in seconds
            )
            
            return signed_url
        except Exception as e:
            raise RuntimeError(f"Failed to upload PDF to S3: {str(e)}")
    
    def _upload_locally(self, pdf_bytes: bytes, filename: str) -> str:
        """Upload PDF to local filesystem (for development)"""
        from pathlib import Path
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        file_path = upload_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Return local URL
        return f"/uploads/{filename}"


# Singleton instance
report_service = ReportService()
