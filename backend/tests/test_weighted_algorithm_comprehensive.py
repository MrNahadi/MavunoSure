"""Comprehensive tests for weighted verification algorithm
Tests for Requirements 7.1-7.5, 8.1-8.5, 13.1-13.5
"""

import pytest
from datetime import datetime
from app.services.weighted_verification_service import WeightedVerificationService
from app.schemas.verification import (
    CropCondition,
    ClaimStatus,
    GroundTruth
)
from app.services.satellite_service import SpaceTruth, SatelliteVerdict


@pytest.fixture
def verification_service():
    """Create a WeightedVerificationService instance"""
    return WeightedVerificationService()


class TestContextualRules:
    """Test all contextual rules with various input combinations (Requirements 7.5, 8.1-8.4)"""
    
    def test_rule_1_drought_severe_stress_auto_approve(self, verification_service):
        """Test Rule 1: Drought + NDMI < -0.2 → Auto-Approve"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.85,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.85),
                (CropCondition.DISEASE_BLIGHT, 0.10),
                (CropCondition.HEALTHY, 0.05)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.25,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score == 0.95
        assert result.rule_applied == "rule_1_drought_low_moisture"
        assert "Double confirmation" in result.explanation
    
    def test_rule_1_drought_exact_threshold(self, verification_service):
        """Test Rule 1 at exact threshold: NDMI = -0.2"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.80,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.80),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.HEALTHY, 0.08)
            ],
            device_tilt=55.0,
            device_azimuth=90.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.20,
            ndmi_14day_avg=-0.08,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=10.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # At exactly -0.2, should NOT trigger Rule 1 (requires < -0.2)
        assert result.rule_applied != "rule_1_drought_low_moisture"
    
    def test_rule_2_drought_normal_moisture_flag(self, verification_service):
        """Test Rule 2: Drought + Normal Moisture → Flag for Review"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.75,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.75),
                (CropCondition.DISEASE_BLIGHT, 0.15),
                (CropCondition.HEALTHY, 0.10)
            ],
            device_tilt=50.0,
            device_azimuth=270.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.15,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.score == 0.65
        assert result.rule_applied == "rule_2_drought_normal_moisture"
        assert "localized drought" in result.explanation.lower() or "fraud" in result.explanation.lower()
    
    def test_rule_3_disease_blight_auto_approve(self, verification_service):
        """Test Rule 3: Disease (Blight) → Auto-Approve"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DISEASE_BLIGHT,
            ml_confidence=0.88,
            top_three_classes=[
                (CropCondition.DISEASE_BLIGHT, 0.88),
                (CropCondition.DROUGHT, 0.08),
                (CropCondition.HEALTHY, 0.04)
            ],
            device_tilt=65.0,
            device_azimuth=45.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=12.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score == 0.85
        assert result.rule_applied == "rule_3_disease_normal_moisture"
        assert "Disease detected" in result.explanation
    
    def test_rule_3_disease_rust_auto_approve(self, verification_service):
        """Test Rule 3: Disease (Rust) → Auto-Approve"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DISEASE_RUST,
            ml_confidence=0.82,
            top_three_classes=[
                (CropCondition.DISEASE_RUST, 0.82),
                (CropCondition.DISEASE_BLIGHT, 0.10),
                (CropCondition.DROUGHT, 0.08)
            ],
            device_tilt=70.0,
            device_azimuth=135.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.05,
            ndmi_14day_avg=0.08,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=15.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score == 0.85
        assert result.rule_applied == "rule_3_disease_normal_moisture"
        assert "common_rust" in result.explanation
    
    def test_rule_4_healthy_low_moisture_reject(self, verification_service):
        """Test Rule 4: Healthy + Low Moisture → Reject"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.HEALTHY,
            ml_confidence=0.78,
            top_three_classes=[
                (CropCondition.HEALTHY, 0.78),
                (CropCondition.DROUGHT, 0.12),
                (CropCondition.DISEASE_BLIGHT, 0.10)
            ],
            device_tilt=55.0,
            device_azimuth=200.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.05,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=7.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.REJECTED
        assert result.score == 0.2
        assert result.rule_applied == "rule_4_healthy_low_moisture"
        assert "Contradiction" in result.explanation
    
    def test_rule_4_healthy_severe_stress_reject(self, verification_service):
        """Test Rule 4: Healthy + Severe Stress → Reject"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.HEALTHY,
            ml_confidence=0.85,
            top_three_classes=[
                (CropCondition.HEALTHY, 0.85),
                (CropCondition.DROUGHT, 0.10),
                (CropCondition.OTHER, 0.05)
            ],
            device_tilt=60.0,
            device_azimuth=315.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.30,
            ndmi_14day_avg=-0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.REJECTED
        assert result.score == 0.2
        assert result.rule_applied == "rule_4_healthy_low_moisture"
        assert "bare soil" in result.explanation.lower()
    
    def test_rule_5_other_reject(self, verification_service):
        """Test Rule 5: Other/Weed → Reject"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.OTHER,
            ml_confidence=0.92,
            top_three_classes=[
                (CropCondition.OTHER, 0.92),
                (CropCondition.HEALTHY, 0.05),
                (CropCondition.DROUGHT, 0.03)
            ],
            device_tilt=48.0,
            device_azimuth=100.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.20,
            ndmi_14day_avg=0.18,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=10.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.REJECTED
        assert result.score == 0.0
        assert result.rule_applied == "rule_5_invalid_subject"
        assert "Invalid subject matter" in result.explanation
    
    def test_pest_condition_uses_weighted_score(self, verification_service):
        """Test that pest condition uses weighted score (no specific rule)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.PEST_ARMYWORM,
            ml_confidence=0.87,
            top_three_classes=[
                (CropCondition.PEST_ARMYWORM, 0.87),
                (CropCondition.DISEASE_BLIGHT, 0.08),
                (CropCondition.DROUGHT, 0.05)
            ],
            device_tilt=62.0,
            device_azimuth=220.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.08,
            ndmi_14day_avg=0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=12.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Should use weighted score, not a contextual rule
        assert result.rule_applied == "weighted_score"
        # Score = (0.87 * 0.6) + (0.3 * 0.4) = 0.522 + 0.12 = 0.642
        expected_score = (0.87 * 0.6) + (0.3 * 0.4)
        assert abs(result.score - expected_score) < 0.01



class TestSeasonalityValidation:
    """Test seasonality validation rules (Requirement 8.5)"""
    
    def test_drought_claim_january_with_normal_moisture_rejected(self, verification_service):
        """Test drought claim in January (dry harvest month) with normal moisture is rejected"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.80,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.80),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.HEALTHY, 0.08)
            ],
            device_tilt=55.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.05,
            ndmi_14day_avg=0.08,
            observation_date=datetime(2024, 1, 14, 0, 0, 0),
            cloud_cover_pct=10.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        claim_date = datetime(2024, 1, 15, 10, 30, 0)
        result = verification_service.verify(ground_truth, space_truth, claim_date)
        
        assert result.status == ClaimStatus.REJECTED
        assert result.score == 0.45
        assert result.rule_applied == "seasonality_dry_harvest_rejection"
        assert "January" in result.explanation
        assert "dry harvest month" in result.explanation.lower()
    
    def test_drought_claim_february_with_normal_moisture_rejected(self, verification_service):
        """Test drought claim in February (dry harvest month) with normal moisture is rejected"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.75,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.75),
                (CropCondition.DISEASE_BLIGHT, 0.15),
                (CropCondition.HEALTHY, 0.10)
            ],
            device_tilt=50.0,
            device_azimuth=90.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 2, 20, 14, 15, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 2, 19, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        claim_date = datetime(2024, 2, 20, 14, 15, 0)
        result = verification_service.verify(ground_truth, space_truth, claim_date)
        
        assert result.status == ClaimStatus.REJECTED
        assert result.score == 0.45
        assert result.rule_applied == "seasonality_dry_harvest_rejection"
        assert "February" in result.explanation
        assert "irrigation" in result.explanation.lower()
    
    def test_drought_claim_january_with_low_moisture_approved(self, verification_service):
        """Test drought claim in January with low moisture is approved (satellite confirms)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.82,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.82),
                (CropCondition.DISEASE_BLIGHT, 0.10),
                (CropCondition.HEALTHY, 0.08)
            ],
            device_tilt=58.0,
            device_azimuth=270.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 1, 25, 11, 0, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.22,
            ndmi_14day_avg=-0.15,
            observation_date=datetime(2024, 1, 24, 0, 0, 0),
            cloud_cover_pct=6.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        claim_date = datetime(2024, 1, 25, 11, 0, 0)
        result = verification_service.verify(ground_truth, space_truth, claim_date)
        
        # Should trigger Rule 1 (drought + low moisture) before seasonality check
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.rule_applied == "rule_1_drought_low_moisture"
    
    def test_disease_claim_january_not_affected_by_seasonality(self, verification_service):
        """Test disease claim in January is not affected by seasonality rules"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DISEASE_BLIGHT,
            ml_confidence=0.88,
            top_three_classes=[
                (CropCondition.DISEASE_BLIGHT, 0.88),
                (CropCondition.DROUGHT, 0.08),
                (CropCondition.HEALTHY, 0.04)
            ],
            device_tilt=65.0,
            device_azimuth=45.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 1, 10, 9, 45, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.08,
            ndmi_14day_avg=0.10,
            observation_date=datetime(2024, 1, 9, 0, 0, 0),
            cloud_cover_pct=12.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        claim_date = datetime(2024, 1, 10, 9, 45, 0)
        result = verification_service.verify(ground_truth, space_truth, claim_date)
        
        # Should trigger Rule 3 (disease), not seasonality
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.rule_applied == "rule_3_disease_normal_moisture"
    
    def test_drought_claim_june_not_affected_by_seasonality(self, verification_service):
        """Test drought claim in June (not dry harvest month) uses normal rules"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.78,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.78),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.HEALTHY, 0.10)
            ],
            device_tilt=52.0,
            device_azimuth=135.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.12,
            ndmi_14day_avg=0.14,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=9.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        claim_date = datetime(2024, 6, 15, 10, 30, 0)
        result = verification_service.verify(ground_truth, space_truth, claim_date)
        
        # Should trigger Rule 2 (drought + normal moisture), not seasonality
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.rule_applied == "rule_2_drought_normal_moisture"



class TestExplainabilityOutput:
    """Test AI explainability features (Requirements 13.1-13.5)"""
    
    def test_explanation_includes_ml_confidence_score(self, verification_service):
        """Test explanation includes ML confidence score (Requirement 13.1)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.87,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.87),
                (CropCondition.DISEASE_BLIGHT, 0.09),
                (CropCondition.HEALTHY, 0.04)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.18,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=7.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Check confidence score is stored
        assert result.ground_truth_confidence == 0.87
        
        # Check explanation includes confidence
        assert "87.0%" in result.explanation or "87%" in result.explanation
        assert "drought_stress" in result.explanation
    
    def test_explanation_includes_top_three_predictions(self, verification_service):
        """Test explanation includes top 3 predicted classes (Requirement 13.2)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.72,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.72),
                (CropCondition.DISEASE_BLIGHT, 0.18),
                (CropCondition.HEALTHY, 0.10)
            ],
            device_tilt=55.0,
            device_azimuth=90.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.12,
            ndmi_14day_avg=-0.08,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=10.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Check explanation includes all three predictions
        assert "Top 3 Predictions:" in result.explanation
        assert "drought_stress" in result.explanation
        assert "northern_leaf_blight" in result.explanation
        assert "healthy" in result.explanation
        assert "72.0%" in result.explanation or "72%" in result.explanation
        assert "18.0%" in result.explanation or "18%" in result.explanation
        assert "10.0%" in result.explanation or "10%" in result.explanation
    
    def test_explanation_stores_individual_confidences(self, verification_service):
        """Test individual GT and ST confidence scores are stored (Requirement 13.3)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DISEASE_BLIGHT,
            ml_confidence=0.91,
            top_three_classes=[
                (CropCondition.DISEASE_BLIGHT, 0.91),
                (CropCondition.DROUGHT, 0.06),
                (CropCondition.HEALTHY, 0.03)
            ],
            device_tilt=68.0,
            device_azimuth=270.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.15,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Check individual confidences are stored
        assert result.ground_truth_confidence == 0.91
        assert result.space_truth_confidence == 0.5  # Disease rule uses 0.5 for ST
        
        # Check explanation includes both
        assert "Ground Truth Confidence:" in result.explanation
        assert "Space Truth Confidence:" in result.explanation
        assert "91.0%" in result.explanation or "91%" in result.explanation
    
    def test_explanation_includes_disagreement_details(self, verification_service):
        """Test explanation includes disagreement details when GT and ST conflict (Requirement 13.4)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.83,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.83),
                (CropCondition.DISEASE_BLIGHT, 0.11),
                (CropCondition.HEALTHY, 0.06)
            ],
            device_tilt=57.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.18,
            ndmi_14day_avg=0.15,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=9.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Check disagreement is detected and explained
        assert "Disagreement Detected" in result.explanation
        assert "visual assessment" in result.explanation.lower()
        assert "satellite data" in result.explanation.lower()
        assert "drought_stress" in result.explanation
        assert "normal" in result.explanation.lower()
    
    def test_rejection_includes_specific_rule_and_threshold(self, verification_service):
        """Test rejection explanation includes specific rule/threshold (Requirement 13.5)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.OTHER,
            ml_confidence=0.88,
            top_three_classes=[
                (CropCondition.OTHER, 0.88),
                (CropCondition.HEALTHY, 0.08),
                (CropCondition.DROUGHT, 0.04)
            ],
            device_tilt=50.0,
            device_azimuth=45.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=11.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Check rejection includes rule
        assert result.status == ClaimStatus.REJECTED
        assert result.rule_applied == "rule_5_invalid_subject"
        
        # Check explanation includes rule information
        assert "Rule Applied:" in result.explanation
        assert "rule_5_invalid_subject" in result.explanation
        assert "Invalid subject matter" in result.explanation
    
    def test_weighted_score_threshold_explanation(self, verification_service):
        """Test weighted score includes threshold explanation"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.PEST_ARMYWORM,
            ml_confidence=0.76,
            top_three_classes=[
                (CropCondition.PEST_ARMYWORM, 0.76),
                (CropCondition.DISEASE_BLIGHT, 0.14),
                (CropCondition.DROUGHT, 0.10)
            ],
            device_tilt=62.0,
            device_azimuth=315.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.05,
            ndmi_14day_avg=-0.03,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=13.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Check explanation includes threshold details
        assert "Decision Threshold:" in result.explanation
        assert "Weighted Score:" in result.explanation
        assert "GT weight: 0.6" in result.explanation
        assert "ST weight: 0.4" in result.explanation
        
        # Check threshold explanation based on status
        if result.status == ClaimStatus.AUTO_APPROVED:
            assert "0.8" in result.explanation
        elif result.status == ClaimStatus.FLAGGED_FOR_REVIEW:
            assert "0.5" in result.explanation
            assert "0.8" in result.explanation
        elif result.status == ClaimStatus.REJECTED:
            assert "0.5" in result.explanation
    
    def test_explanation_includes_satellite_details(self, verification_service):
        """Test explanation includes comprehensive satellite analysis details"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.85,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.85),
                (CropCondition.DISEASE_BLIGHT, 0.10),
                (CropCondition.HEALTHY, 0.05)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.23,
            ndmi_14day_avg=-0.11,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=6.5,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Check satellite details are included
        assert "Satellite Analysis:" in result.explanation
        assert "NDMI Value:" in result.explanation
        assert "-0.230" in result.explanation
        assert "14-day avg:" in result.explanation
        assert "-0.110" in result.explanation
        assert "Verdict:" in result.explanation
        assert "severe_stress" in result.explanation
        assert "Observation Date:" in result.explanation
        assert "2024-06-14" in result.explanation
        assert "Cloud Cover:" in result.explanation
        assert "6.5%" in result.explanation



class TestWeightedScoreCalculations:
    """Test weighted score calculations (Requirements 7.1-7.4)"""
    
    def test_auto_approve_threshold(self, verification_service):
        """Test score > 0.8 results in auto-approval (Requirement 7.2)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.95,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.95),
                (CropCondition.DISEASE_BLIGHT, 0.03),
                (CropCondition.HEALTHY, 0.02)
            ],
            device_tilt=65.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.18,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=7.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Score = (0.95 * 0.6) + (0.6 * 0.4) = 0.57 + 0.24 = 0.81
        expected_score = (0.95 * 0.6) + (0.6 * 0.4)
        assert abs(result.score - expected_score) < 0.01
        assert result.score > 0.8
        assert result.status == ClaimStatus.AUTO_APPROVED
    
    def test_flag_for_review_threshold(self, verification_service):
        """Test score between 0.5 and 0.79 results in flag for review (Requirement 7.3)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.PEST_ARMYWORM,
            ml_confidence=0.70,
            top_three_classes=[
                (CropCondition.PEST_ARMYWORM, 0.70),
                (CropCondition.DISEASE_BLIGHT, 0.20),
                (CropCondition.DROUGHT, 0.10)
            ],
            device_tilt=58.0,
            device_azimuth=90.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.12,
            ndmi_14day_avg=-0.08,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=10.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Score = (0.70 * 0.6) + (0.6 * 0.4) = 0.42 + 0.24 = 0.66
        expected_score = (0.70 * 0.6) + (0.6 * 0.4)
        assert abs(result.score - expected_score) < 0.01
        assert 0.5 <= result.score < 0.8
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
    
    def test_reject_threshold(self, verification_service):
        """Test score < 0.5 results in rejection (Requirement 7.4)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.HEALTHY,
            ml_confidence=0.45,
            top_three_classes=[
                (CropCondition.HEALTHY, 0.45),
                (CropCondition.DROUGHT, 0.30),
                (CropCondition.OTHER, 0.25)
            ],
            device_tilt=52.0,
            device_azimuth=270.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.18,
            ndmi_14day_avg=0.15,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=9.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Score = (0.45 * 0.6) + (0.3 * 0.4) = 0.27 + 0.12 = 0.39
        expected_score = (0.45 * 0.6) + (0.3 * 0.4)
        assert abs(result.score - expected_score) < 0.01
        assert result.score < 0.5
        assert result.status == ClaimStatus.REJECTED
