"""Weighted verification algorithm service"""

import logging
from datetime import datetime
from typing import Optional

from app.schemas.verification import (
    CropCondition,
    ClaimStatus,
    GroundTruth,
    WeightedVerificationResult
)
from app.services.satellite_service import SpaceTruth, SatelliteVerdict

logger = logging.getLogger(__name__)


class WeightedVerificationService:
    """
    Service for weighted verification combining Ground Truth and Space Truth
    
    Implements the weighted verification matrix from requirements 7.1-7.5 and 8.1-8.5
    Provides AI explainability features per requirements 13.1-13.5
    """
    
    # Weights for Ground Truth and Space Truth
    GROUND_TRUTH_WEIGHT = 0.6
    SPACE_TRUTH_WEIGHT = 0.4
    
    # Thresholds for decision making
    AUTO_APPROVE_THRESHOLD = 0.8
    FLAG_THRESHOLD = 0.5
    
    def _format_top_classes_explanation(self, top_three_classes) -> str:
        """
        Format top 3 predicted classes for human-readable explanation
        
        Implements requirement 13.2 - provide confidence scores for top 3 classes
        
        Args:
            top_three_classes: List of tuples (CropCondition, confidence)
            
        Returns:
            Formatted string with top 3 predictions
        """
        if not top_three_classes or len(top_three_classes) == 0:
            return "No alternative classifications available"
        
        formatted = []
        for i, (condition, confidence) in enumerate(top_three_classes[:3], 1):
            formatted.append(f"{i}. {condition.value}: {confidence:.1%}")
        
        return " | ".join(formatted)
    
    def _build_detailed_explanation(
        self,
        status: ClaimStatus,
        score: float,
        ground_truth: GroundTruth,
        space_truth: SpaceTruth,
        rule_applied: str,
        base_explanation: str
    ) -> str:
        """
        Build detailed explanation with AI explainability features
        
        Implements requirements 13.3, 13.4, 13.5:
        - Include individual GT and ST confidence scores
        - Provide human-readable explanation
        - Include specific rule/threshold that triggered decision
        
        Args:
            status: Final claim status
            score: Weighted verification score
            ground_truth: Ground Truth data
            space_truth: Space Truth data
            rule_applied: Name of the rule that was applied
            base_explanation: Base explanation text
            
        Returns:
            Detailed explanation string
        """
        # Start with base explanation
        explanation_parts = [base_explanation]
        
        # Add AI model details (Requirement 13.1, 13.2)
        explanation_parts.append(
            f"\n\nAI Classification Details:\n"
            f"Primary: {ground_truth.ml_class.value} ({ground_truth.ml_confidence:.1%} confidence)\n"
            f"Top 3 Predictions: {self._format_top_classes_explanation(ground_truth.top_three_classes)}"
        )
        
        # Add satellite details
        explanation_parts.append(
            f"\n\nSatellite Analysis:\n"
            f"NDMI Value: {space_truth.ndmi_value:.3f} (14-day avg: {space_truth.ndmi_14day_avg:.3f})\n"
            f"Verdict: {space_truth.verdict.value}\n"
            f"Observation Date: {space_truth.observation_date.strftime('%Y-%m-%d')}\n"
            f"Cloud Cover: {space_truth.cloud_cover_pct:.1f}%"
        )
        
        # Add decision logic details (Requirement 13.3, 13.5)
        gt_conf = ground_truth.ml_confidence
        st_conf = self._satellite_confidence(space_truth)
        
        explanation_parts.append(
            f"\n\nVerification Logic:\n"
            f"Ground Truth Confidence: {gt_conf:.1%}\n"
            f"Space Truth Confidence: {st_conf:.1%}\n"
            f"Weighted Score: {score:.2f} (GT weight: {self.GROUND_TRUTH_WEIGHT}, ST weight: {self.SPACE_TRUTH_WEIGHT})\n"
            f"Rule Applied: {rule_applied}\n"
            f"Decision Threshold: "
        )
        
        # Add threshold explanation based on status
        if status == ClaimStatus.AUTO_APPROVED:
            explanation_parts.append(f"Auto-approve (score > {self.AUTO_APPROVE_THRESHOLD})")
        elif status == ClaimStatus.FLAGGED_FOR_REVIEW:
            explanation_parts.append(
                f"Flag for review (score between {self.FLAG_THRESHOLD} and {self.AUTO_APPROVE_THRESHOLD})"
            )
        elif status == ClaimStatus.REJECTED:
            explanation_parts.append(f"Reject (score < {self.FLAG_THRESHOLD})")
        else:
            explanation_parts.append("N/A")
        
        # Add disagreement explanation if GT and ST disagree (Requirement 13.4)
        if self._check_disagreement(ground_truth, space_truth):
            explanation_parts.append(
                f"\n\n⚠️ Ground Truth and Space Truth Disagreement Detected:\n"
                f"The visual assessment ({ground_truth.ml_class.value}) and satellite data "
                f"({space_truth.verdict.value}) show different conditions. This may indicate:\n"
                f"- Localized conditions not visible from satellite\n"
                f"- Recent changes not yet reflected in satellite imagery\n"
                f"- Potential data quality issues requiring manual review"
            )
        
        return "".join(explanation_parts)
    
    def _check_disagreement(self, ground_truth: GroundTruth, space_truth: SpaceTruth) -> bool:
        """
        Check if Ground Truth and Space Truth significantly disagree
        
        Args:
            ground_truth: Ground Truth data
            space_truth: Space Truth data
            
        Returns:
            True if there's significant disagreement
        """
        # Drought should correlate with low moisture
        if ground_truth.ml_class == CropCondition.DROUGHT:
            if space_truth.verdict == SatelliteVerdict.NORMAL:
                return True
        
        # Healthy should not correlate with severe stress
        if ground_truth.ml_class == CropCondition.HEALTHY:
            if space_truth.verdict == SatelliteVerdict.SEVERE_STRESS:
                return True
        
        return False
    
    def verify(
        self,
        ground_truth: GroundTruth,
        space_truth: SpaceTruth,
        claim_date: Optional[datetime] = None
    ) -> WeightedVerificationResult:
        """
        Perform weighted verification combining Ground Truth and Space Truth
        
        Args:
            ground_truth: Ground Truth data from mobile app
            space_truth: Space Truth data from satellite
            claim_date: Date of claim submission (for seasonality validation)
            
        Returns:
            WeightedVerificationResult with score, status, and explanation
        """
        logger.info(
            f"Starting weighted verification: GT class={ground_truth.ml_class}, "
            f"GT confidence={ground_truth.ml_confidence:.2f}, "
            f"NDMI={space_truth.ndmi_value:.3f}, "
            f"Satellite verdict={space_truth.verdict}"
        )
        
        # Apply contextual rules first (Requirements 7.5, 8.1-8.4)
        contextual_result = self._apply_contextual_rules(ground_truth, space_truth)
        if contextual_result:
            logger.info(f"Contextual rule applied: {contextual_result.rule_applied}")
            return contextual_result
        
        # Apply seasonality validation if claim_date provided (Requirement 8.5)
        if claim_date:
            seasonality_result = self._apply_seasonality_validation(
                ground_truth, space_truth, claim_date
            )
            if seasonality_result:
                logger.info(f"Seasonality rule applied: {seasonality_result.rule_applied}")
                return seasonality_result
        
        # Calculate weighted score (Requirements 7.1-7.4)
        gt_confidence = ground_truth.ml_confidence
        st_confidence = self._satellite_confidence(space_truth)
        
        score = (gt_confidence * self.GROUND_TRUTH_WEIGHT) + \
                (st_confidence * self.SPACE_TRUTH_WEIGHT)
        
        # Apply threshold logic
        if score > self.AUTO_APPROVE_THRESHOLD:
            status = ClaimStatus.AUTO_APPROVED
            base_explanation = (
                f"High confidence from both Ground Truth and Space Truth. "
                f"The claim meets the auto-approval threshold."
            )
        elif score >= self.FLAG_THRESHOLD:
            status = ClaimStatus.FLAGGED_FOR_REVIEW
            base_explanation = (
                f"Moderate confidence detected. The weighted score falls in the review range, "
                f"indicating uncertainty that requires human judgment."
            )
        else:
            status = ClaimStatus.REJECTED
            base_explanation = (
                f"Low confidence score. The combined assessment from visual and satellite data "
                f"does not meet the minimum threshold for claim approval."
            )
        
        # Build detailed explanation with AI explainability features (Requirements 13.1-13.5)
        detailed_explanation = self._build_detailed_explanation(
            status=status,
            score=score,
            ground_truth=ground_truth,
            space_truth=space_truth,
            rule_applied="weighted_score",
            base_explanation=base_explanation
        )
        
        logger.info(f"Weighted verification result: status={status}, score={score:.2f}")
        
        return WeightedVerificationResult(
            score=score,
            status=status,
            explanation=detailed_explanation,
            ground_truth_confidence=gt_confidence,
            space_truth_confidence=st_confidence,
            rule_applied="weighted_score"
        )
    
    def _satellite_confidence(self, space_truth: SpaceTruth) -> float:
        """
        Convert satellite verdict to confidence score
        
        Args:
            space_truth: Space Truth data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if space_truth.verdict == SatelliteVerdict.SEVERE_STRESS:
            return 0.9
        elif space_truth.verdict == SatelliteVerdict.MODERATE_STRESS:
            return 0.6
        else:  # NORMAL
            return 0.3
    
    def _apply_contextual_rules(
        self,
        ground_truth: GroundTruth,
        space_truth: SpaceTruth
    ) -> Optional[WeightedVerificationResult]:
        """
        Apply contextual verification rules based on crop condition and satellite data
        
        Implements requirements 7.5, 8.1-8.4
        
        Args:
            ground_truth: Ground Truth data
            space_truth: Space Truth data
            
        Returns:
            WeightedVerificationResult if a rule applies, None otherwise
        """
        gt_class = ground_truth.ml_class
        gt_conf = ground_truth.ml_confidence
        ndmi = space_truth.ndmi_value
        st_verdict = space_truth.verdict
        
        # Rule 1: Drought + Low Moisture (< -0.2) → Auto-Approve (Requirement 7.5)
        if gt_class == CropCondition.DROUGHT and ndmi < -0.2:
            base_explanation = (
                "Double confirmation: Visual drought stress matches severe satellite "
                "moisture deficit. High confidence in claim validity."
            )
            detailed_explanation = self._build_detailed_explanation(
                status=ClaimStatus.AUTO_APPROVED,
                score=0.95,
                ground_truth=ground_truth,
                space_truth=space_truth,
                rule_applied="rule_1_drought_low_moisture",
                base_explanation=base_explanation
            )
            return WeightedVerificationResult(
                score=0.95,
                status=ClaimStatus.AUTO_APPROVED,
                explanation=detailed_explanation,
                ground_truth_confidence=gt_conf,
                space_truth_confidence=0.9,
                rule_applied="rule_1_drought_low_moisture"
            )
        
        # Rule 2: Drought + Normal Moisture → Flag for Review (Requirement 8.1)
        if gt_class == CropCondition.DROUGHT and st_verdict == SatelliteVerdict.NORMAL:
            base_explanation = (
                "Possible localized drought or camera fraud - satellite shows normal "
                "moisture but ground assessment indicates drought. Manual review required."
            )
            detailed_explanation = self._build_detailed_explanation(
                status=ClaimStatus.FLAGGED_FOR_REVIEW,
                score=0.65,
                ground_truth=ground_truth,
                space_truth=space_truth,
                rule_applied="rule_2_drought_normal_moisture",
                base_explanation=base_explanation
            )
            return WeightedVerificationResult(
                score=0.65,
                status=ClaimStatus.FLAGGED_FOR_REVIEW,
                explanation=detailed_explanation,
                ground_truth_confidence=gt_conf,
                space_truth_confidence=0.3,
                rule_applied="rule_2_drought_normal_moisture"
            )
        
        # Rule 3: Disease + Normal Moisture → Auto-Approve (Requirement 8.2)
        if gt_class in [CropCondition.DISEASE_BLIGHT, CropCondition.DISEASE_RUST]:
            base_explanation = (
                f"Disease detected ({gt_class.value}). "
                "Satellite may not show immediate moisture impact for disease conditions. "
                "Claim approved based on visual assessment."
            )
            detailed_explanation = self._build_detailed_explanation(
                status=ClaimStatus.AUTO_APPROVED,
                score=0.85,
                ground_truth=ground_truth,
                space_truth=space_truth,
                rule_applied="rule_3_disease_normal_moisture",
                base_explanation=base_explanation
            )
            return WeightedVerificationResult(
                score=0.85,
                status=ClaimStatus.AUTO_APPROVED,
                explanation=detailed_explanation,
                ground_truth_confidence=gt_conf,
                space_truth_confidence=0.5,
                rule_applied="rule_3_disease_normal_moisture"
            )
        
        # Rule 4: Healthy + Low Moisture → Reject (Requirement 8.3)
        if gt_class == CropCondition.HEALTHY and ndmi < -0.1:
            base_explanation = (
                "Contradiction: Crop appears healthy in photo but satellite shows "
                "moisture stress. Possible bare soil reading or invalid photo. Claim rejected."
            )
            detailed_explanation = self._build_detailed_explanation(
                status=ClaimStatus.REJECTED,
                score=0.2,
                ground_truth=ground_truth,
                space_truth=space_truth,
                rule_applied="rule_4_healthy_low_moisture",
                base_explanation=base_explanation
            )
            return WeightedVerificationResult(
                score=0.2,
                status=ClaimStatus.REJECTED,
                explanation=detailed_explanation,
                ground_truth_confidence=gt_conf,
                space_truth_confidence=0.9,
                rule_applied="rule_4_healthy_low_moisture"
            )
        
        # Rule 5: Weed/Other → Reject (Requirement 8.4)
        if gt_class == CropCondition.OTHER:
            base_explanation = (
                "Invalid subject matter - photo does not show a valid crop condition. "
                "Claim rejected."
            )
            detailed_explanation = self._build_detailed_explanation(
                status=ClaimStatus.REJECTED,
                score=0.0,
                ground_truth=ground_truth,
                space_truth=space_truth,
                rule_applied="rule_5_invalid_subject",
                base_explanation=base_explanation
            )
            return WeightedVerificationResult(
                score=0.0,
                status=ClaimStatus.REJECTED,
                explanation=detailed_explanation,
                ground_truth_confidence=gt_conf,
                space_truth_confidence=0.0,
                rule_applied="rule_5_invalid_subject"
            )
        
        # No contextual rule applies
        return None
    
    def _apply_seasonality_validation(
        self,
        ground_truth: GroundTruth,
        space_truth: SpaceTruth,
        claim_date: datetime
    ) -> Optional[WeightedVerificationResult]:
        """
        Apply seasonality validation rules based on FEWS NET crop calendar
        
        Implements requirement 8.5
        
        Args:
            ground_truth: Ground Truth data
            space_truth: Space Truth data
            claim_date: Date of claim submission
            
        Returns:
            WeightedVerificationResult if seasonality rule applies, None otherwise
        """
        # FEWS NET crop calendar for Kenya maize
        # Dry harvest months: January (1), February (2)
        # These are historically dry months when drought claims should be scrutinized
        
        claim_month = claim_date.month
        
        # Apply stricter validation for drought claims during dry harvest months
        if ground_truth.ml_class == CropCondition.DROUGHT and claim_month in [1, 2]:
            # During dry harvest months, require strong satellite confirmation
            if space_truth.ndmi_value >= -0.1:
                # Satellite shows normal/adequate moisture during dry season
                base_explanation = (
                    f"Drought claim submitted during historically dry harvest month "
                    f"({claim_date.strftime('%B')}), but satellite shows adequate moisture. "
                    "Claim rejected due to seasonality mismatch unless irrigation is documented."
                )
                detailed_explanation = self._build_detailed_explanation(
                    status=ClaimStatus.REJECTED,
                    score=0.45,
                    ground_truth=ground_truth,
                    space_truth=space_truth,
                    rule_applied="seasonality_dry_harvest_rejection",
                    base_explanation=base_explanation
                )
                return WeightedVerificationResult(
                    score=0.45,
                    status=ClaimStatus.REJECTED,
                    explanation=detailed_explanation,
                    ground_truth_confidence=ground_truth.ml_confidence,
                    space_truth_confidence=0.3,
                    rule_applied="seasonality_dry_harvest_rejection"
                )
        
        # No seasonality rule applies
        return None


# Singleton instance
weighted_verification_service = WeightedVerificationService()
