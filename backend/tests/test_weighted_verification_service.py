"""Tests for weighted verification service with AI explainability features"""

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


@pytest.fixture
def sample_ground_truth_drought():
    """Sample Ground Truth data for drought condition"""
    return GroundTruth(
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


@pytest.fixture
def sample_space_truth_severe():
    """Sample Space Truth data for severe stress"""
    return SpaceTruth(
        ndmi_value=-0.25,
        ndmi_14day_avg=-0.10,
        observation_date=datetime(2024, 6, 14, 0, 0, 0),
        cloud_cover_pct=5.0,
        verdict=SatelliteVerdict.SEVERE_STRESS
    )


@pytest.fixture
def sample_space_truth_normal():
    """Sample Space Truth data for normal conditions"""
    return SpaceTruth(
        ndmi_value=0.15,
        ndmi_14day_avg=0.12,
        observation_date=datetime(2024, 6, 14, 0, 0, 0),
        cloud_cover_pct=8.0,
        verdict=SatelliteVerdict.NORMAL
    )


class TestExplainabilityFeatures:
    """Test AI explainability features (Requirements 13.1-13.5)"""
    
    def test_explanation_includes_top_three_classes(
        self,
        verification_service,
        sample_ground_truth_drought,
        sample_space_truth_severe
    ):
        """Test that explanation includes top 3 predicted classes (Requirement 13.2)"""
        result = verification_service.verify(
            ground_truth=sample_ground_truth_drought,
            space_truth=sample_space_truth_severe
        )
        
        # Check that explanation includes top 3 predictions
        assert "Top 3 Predictions:" in result.explanation
        assert "drought_stress" in result.explanation
        assert "85.0%" in result.explanation or "85%" in result.explanation
    
    def test_explanation_includes_confidence_scores(
        self,
        verification_service,
        sample_ground_truth_drought,
        sample_space_truth_severe
    ):
        """Test that explanation includes GT and ST confidence scores (Requirement 13.3)"""
        result = verification_service.verify(
            ground_truth=sample_ground_truth_drought,
            space_truth=sample_space_truth_severe
        )
        
        # Check that individual confidence scores are stored
        assert result.ground_truth_confidence == 0.85
        assert result.space_truth_confidence == 0.9
        
        # Check that explanation includes confidence details
        assert "Ground Truth Confidence:" in result.explanation
        assert "Space Truth Confidence:" in result.explanation
    
    def test_explanation_includes_rule_applied(
        self,
        verification_service,
        sample_ground_truth_drought,
        sample_space_truth_severe
    ):
        """Test that explanation includes specific rule applied (Requirement 13.5)"""
        result = verification_service.verify(
            ground_truth=sample_ground_truth_drought,
            space_truth=sample_space_truth_severe
        )
        
        # Check that rule is tracked
        assert result.rule_applied is not None
        assert result.rule_applied == "rule_1_drought_low_moisture"
        
        # Check that explanation includes rule information
        assert "Rule Applied:" in result.explanation
    
    def test_explanation_includes_satellite_details(
        self,
        verification_service,
        sample_ground_truth_drought,
        sample_space_truth_severe
    ):
        """Test that explanation includes satellite analysis details"""
        result = verification_service.verify(
            ground_truth=sample_ground_truth_drought,
            space_truth=sample_space_truth_severe
        )
        
        # Check that explanation includes satellite details
        assert "Satellite Analysis:" in result.explanation
        assert "NDMI Value:" in result.explanation
        assert "-0.250" in result.explanation
        assert "Observation Date:" in result.explanation
        assert "Cloud Cover:" in result.explanation
    
    def test_disagreement_detection_and_explanation(
        self,
        verification_service,
        sample_ground_truth_drought,
        sample_space_truth_normal
    ):
        """Test disagreement detection and explanation (Requirement 13.4)"""
        result = verification_service.verify(
            ground_truth=sample_ground_truth_drought,
            space_truth=sample_space_truth_normal
        )
        
        # Check that disagreement is detected
        assert "Disagreement Detected" in result.explanation
        
        # Check that explanation provides context
        assert "visual assessment" in result.explanation.lower()
        assert "satellite data" in result.explanation.lower()
    
    def test_rejection_includes_specific_threshold(
        self,
        verification_service
    ):
        """Test that rejection explanation includes specific threshold (Requirement 13.5)"""
        # Create low confidence ground truth
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.HEALTHY,
            ml_confidence=0.30,
            top_three_classes=[
                (CropCondition.HEALTHY, 0.30),
                (CropCondition.DROUGHT, 0.25),
                (CropCondition.OTHER, 0.20)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth
        )
        
        # Check that status is rejected or flagged
        assert result.status in [ClaimStatus.REJECTED, ClaimStatus.FLAGGED_FOR_REVIEW]
        
        # Check that explanation includes threshold information
        assert "Decision Threshold:" in result.explanation
        assert "0.5" in result.explanation or "0.8" in result.explanation


class TestContextualRulesExplainability:
    """Test explainability for contextual rules"""
    
    def test_rule_1_drought_low_moisture_explanation(
        self,
        verification_service,
        sample_ground_truth_drought,
        sample_space_truth_severe
    ):
        """Test Rule 1: Drought + Low Moisture explanation"""
        result = verification_service.verify(
            ground_truth=sample_ground_truth_drought,
            space_truth=sample_space_truth_severe
        )
        
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score == 0.95
        assert "Double confirmation" in result.explanation
        assert "rule_1_drought_low_moisture" == result.rule_applied
    
    def test_rule_2_drought_normal_moisture_explanation(
        self,
        verification_service,
        sample_ground_truth_drought,
        sample_space_truth_normal
    ):
        """Test Rule 2: Drought + Normal Moisture explanation"""
        result = verification_service.verify(
            ground_truth=sample_ground_truth_drought,
            space_truth=sample_space_truth_normal
        )
        
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.score == 0.65
        assert "localized drought" in result.explanation.lower() or "fraud" in result.explanation.lower()
        assert "rule_2_drought_normal_moisture" == result.rule_applied
    
    def test_rule_5_invalid_subject_explanation(
        self,
        verification_service,
        sample_space_truth_normal
    ):
        """Test Rule 5: Invalid subject matter explanation"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.OTHER,
            ml_confidence=0.75,
            top_three_classes=[
                (CropCondition.OTHER, 0.75),
                (CropCondition.HEALTHY, 0.15),
                (CropCondition.DROUGHT, 0.10)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=sample_space_truth_normal
        )
        
        assert result.status == ClaimStatus.REJECTED
        assert result.score == 0.0
        assert "Invalid subject matter" in result.explanation
        assert "rule_5_invalid_subject" == result.rule_applied


class TestWeightedScoreExplainability:
    """Test explainability for weighted score calculations"""
    
    def test_weighted_score_calculation_details(
        self,
        verification_service
    ):
        """Test that weighted score calculation is explained"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.90,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.90),
                (CropCondition.DISEASE_BLIGHT, 0.07),
                (CropCondition.HEALTHY, 0.03)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth
        )
        
        # Check that explanation includes weight information
        assert "Weighted Score:" in result.explanation
        assert "GT weight: 0.6" in result.explanation
        assert "ST weight: 0.4" in result.explanation
        
        # Verify the calculation
        expected_score = (0.90 * 0.6) + (0.6 * 0.4)
        assert abs(result.score - expected_score) < 0.01


class TestWeightedScoreExplainability:
    """Test explainability for weighted score calculations"""
    
    def test_weighted_score_calculation_details(
        self,
        verification_service
    ):
        """Test that weighted score calculation is explained"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.90,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.90),
                (CropCondition.DISEASE_BLIGHT, 0.07),
                (CropCondition.HEALTHY, 0.03)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth
        )
        
        # Check that explanation includes weight information
        assert "Weighted Score:" in result.explanation
        assert "GT weight: 0.6" in result.explanation
        assert "ST weight: 0.4" in result.explanation
        
        # Verify the calculation
        expected_score = (0.90 * 0.6) + (0.6 * 0.4)
        assert abs(result.score - expected_score) < 0.01



class TestContextualRules:
    """Test all contextual verification rules with various input combinations"""
    
    def test_rule_1_drought_severe_stress_variations(self, verification_service):
        """Test Rule 1: Drought + Low Moisture with different confidence levels"""
        # High confidence drought + severe stress
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.95,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.95),
                (CropCondition.DISEASE_BLIGHT, 0.03),
                (CropCondition.HEALTHY, 0.02)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.30,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score == 0.95
        assert result.rule_applied == "rule_1_drought_low_moisture"

    
    def test_rule_1_drought_boundary_ndmi(self, verification_service):
        """Test Rule 1 at NDMI boundary (-0.2)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.80,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.80),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.HEALTHY, 0.08)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Test just below threshold
        space_truth_below = SpaceTruth(
            ndmi_value=-0.21,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth_below)
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.rule_applied == "rule_1_drought_low_moisture"
        
        # Test just above threshold (should not trigger Rule 1)
        space_truth_above = SpaceTruth(
            ndmi_value=-0.19,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth_above)
        assert result.rule_applied != "rule_1_drought_low_moisture"

    
    def test_rule_2_drought_normal_moisture_variations(self, verification_service):
        """Test Rule 2: Drought + Normal Moisture with different scenarios"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.75,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.75),
                (CropCondition.DISEASE_BLIGHT, 0.15),
                (CropCondition.HEALTHY, 0.10)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.score == 0.65
        assert result.rule_applied == "rule_2_drought_normal_moisture"
        assert "localized" in result.explanation.lower() or "fraud" in result.explanation.lower()

    
    def test_rule_3_disease_blight_variations(self, verification_service):
        """Test Rule 3: Disease (Blight) with various moisture levels"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DISEASE_BLIGHT,
            ml_confidence=0.88,
            top_three_classes=[
                (CropCondition.DISEASE_BLIGHT, 0.88),
                (CropCondition.DROUGHT, 0.08),
                (CropCondition.HEALTHY, 0.04)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Test with normal moisture
        space_truth_normal = SpaceTruth(
            ndmi_value=0.15,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth_normal)
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score == 0.85
        assert result.rule_applied == "rule_3_disease_normal_moisture"
        
        # Test with low moisture (should still auto-approve)
        space_truth_low = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth_low)
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.rule_applied == "rule_3_disease_normal_moisture"

    
    def test_rule_3_disease_rust_variations(self, verification_service):
        """Test Rule 3: Disease (Rust) with various moisture levels"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DISEASE_RUST,
            ml_confidence=0.82,
            top_three_classes=[
                (CropCondition.DISEASE_RUST, 0.82),
                (CropCondition.DISEASE_BLIGHT, 0.10),
                (CropCondition.DROUGHT, 0.08)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
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
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score == 0.85
        assert result.rule_applied == "rule_3_disease_normal_moisture"

    
    def test_rule_4_healthy_low_moisture_variations(self, verification_service):
        """Test Rule 4: Healthy + Low Moisture (contradiction)"""
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
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Test at boundary (-0.1)
        space_truth_boundary = SpaceTruth(
            ndmi_value=-0.11,
            ndmi_14day_avg=-0.05,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth_boundary)
        assert result.status == ClaimStatus.REJECTED
        assert result.score == 0.2
        assert result.rule_applied == "rule_4_healthy_low_moisture"
        assert "Contradiction" in result.explanation
        
        # Test with severe stress
        space_truth_severe = SpaceTruth(
            ndmi_value=-0.25,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth_severe)
        assert result.status == ClaimStatus.REJECTED
        assert result.rule_applied == "rule_4_healthy_low_moisture"

    
    def test_rule_5_other_classification_variations(self, verification_service):
        """Test Rule 5: Other/Invalid subject matter"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.OTHER,
            ml_confidence=0.92,
            top_three_classes=[
                (CropCondition.OTHER, 0.92),
                (CropCondition.HEALTHY, 0.05),
                (CropCondition.DROUGHT, 0.03)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Test with various satellite conditions
        for ndmi_value, verdict in [
            (-0.25, SatelliteVerdict.SEVERE_STRESS),
            (-0.15, SatelliteVerdict.MODERATE_STRESS),
            (0.15, SatelliteVerdict.NORMAL)
        ]:
            space_truth = SpaceTruth(
                ndmi_value=ndmi_value,
                ndmi_14day_avg=-0.10,
                observation_date=datetime(2024, 6, 14, 0, 0, 0),
                cloud_cover_pct=5.0,
                verdict=verdict
            )
            
            result = verification_service.verify(ground_truth, space_truth)
            assert result.status == ClaimStatus.REJECTED
            assert result.score == 0.0
            assert result.rule_applied == "rule_5_invalid_subject"
            assert "Invalid subject matter" in result.explanation

    
    def test_pest_classification_no_special_rule(self, verification_service):
        """Test that pest classification uses weighted score (no special rule)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.PEST_ARMYWORM,
            ml_confidence=0.85,
            top_three_classes=[
                (CropCondition.PEST_ARMYWORM, 0.85),
                (CropCondition.DISEASE_BLIGHT, 0.10),
                (CropCondition.DROUGHT, 0.05)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        
        # Should use weighted score, not a contextual rule
        assert result.rule_applied == "weighted_score"
        # Expected: (0.85 * 0.6) + (0.3 * 0.4) = 0.51 + 0.12 = 0.63
        expected_score = (0.85 * 0.6) + (0.3 * 0.4)
        assert abs(result.score - expected_score) < 0.01



class TestSeasonalityValidation:
    """Test seasonality validation rules (Requirement 8.5)"""
    
    def test_drought_claim_january_with_normal_moisture_rejected(self, verification_service):
        """Test drought claim in January (dry harvest month) with normal moisture triggers Rule 2"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.80,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.80),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.HEALTHY, 0.08)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.05,
            ndmi_14day_avg=-0.03,
            observation_date=datetime(2024, 1, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth,
            claim_date=datetime(2024, 1, 15)
        )
        
        # Rule 2 (Drought + Normal Moisture) triggers before seasonality check
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.rule_applied == "rule_2_drought_normal_moisture"

    
    def test_drought_claim_february_with_normal_moisture_rejected(self, verification_service):
        """Test drought claim in February (dry harvest month) with normal moisture triggers Rule 2"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.75,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.75),
                (CropCondition.DISEASE_BLIGHT, 0.15),
                (CropCondition.HEALTHY, 0.10)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 2, 20, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.05,
            ndmi_14day_avg=0.08,
            observation_date=datetime(2024, 2, 19, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth,
            claim_date=datetime(2024, 2, 20)
        )
        
        # Rule 2 (Drought + Normal Moisture) triggers before seasonality check
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.rule_applied == "rule_2_drought_normal_moisture"

    
    def test_drought_claim_january_with_low_moisture_approved(self, verification_service):
        """Test drought claim in January with low moisture is approved (legitimate drought)"""
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
            capture_timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=-0.25,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 1, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth,
            claim_date=datetime(2024, 1, 15)
        )
        
        # Should trigger Rule 1 (Drought + Low Moisture) before seasonality check
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.rule_applied == "rule_1_drought_low_moisture"

    
    def test_drought_claim_june_with_normal_moisture_flagged(self, verification_service):
        """Test drought claim in June (not dry harvest month) with normal moisture is flagged"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.80,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.80),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.HEALTHY, 0.08)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth,
            claim_date=datetime(2024, 6, 15)
        )
        
        # Should trigger Rule 2 (Drought + Normal Moisture) - flagged for review
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.rule_applied == "rule_2_drought_normal_moisture"

    
    def test_disease_claim_january_not_affected_by_seasonality(self, verification_service):
        """Test that disease claims in January are not affected by seasonality rules"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DISEASE_BLIGHT,
            ml_confidence=0.88,
            top_three_classes=[
                (CropCondition.DISEASE_BLIGHT, 0.88),
                (CropCondition.DROUGHT, 0.08),
                (CropCondition.HEALTHY, 0.04)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 1, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth,
            claim_date=datetime(2024, 1, 15)
        )
        
        # Should trigger Rule 3 (Disease) regardless of month
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.rule_applied == "rule_3_disease_normal_moisture"

    
    def test_seasonality_boundary_ndmi_values(self, verification_service):
        """Test seasonality rule at NDMI boundary (-0.1)"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.80,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.80),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.HEALTHY, 0.08)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        # Test at boundary (triggers Rule 2 since verdict is NORMAL)
        space_truth_boundary = SpaceTruth(
            ndmi_value=-0.09,
            ndmi_14day_avg=-0.05,
            observation_date=datetime(2024, 1, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(
            ground_truth=ground_truth,
            space_truth=space_truth_boundary,
            claim_date=datetime(2024, 1, 15)
        )
        
        # Rule 2 (Drought + Normal Moisture) triggers before seasonality check
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.rule_applied == "rule_2_drought_normal_moisture"



class TestWeightedScoreThresholds:
    """Test weighted score calculation and threshold logic (Requirements 7.1-7.4)"""
    
    def test_auto_approve_threshold_boundary(self, verification_service):
        """Test weighted score at auto-approve threshold (0.8)"""
        # Create scenario that results in score just above 0.8
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.90,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.90),
                (CropCondition.DISEASE_BLIGHT, 0.07),
                (CropCondition.HEALTHY, 0.03)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Moderate stress gives 0.6 confidence
        # Score = (0.90 * 0.6) + (0.6 * 0.4) = 0.54 + 0.24 = 0.78 (below threshold)
        space_truth_below = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth_below)
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.score < 0.8

    
    def test_flag_threshold_boundary(self, verification_service):
        """Test weighted score at flag threshold (0.5)"""
        # Create scenario that results in score around 0.5
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.60,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.60),
                (CropCondition.DISEASE_BLIGHT, 0.25),
                (CropCondition.HEALTHY, 0.15)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Moderate stress gives 0.6 confidence
        # Score = (0.60 * 0.6) + (0.6 * 0.4) = 0.36 + 0.24 = 0.60 (above flag threshold)
        space_truth = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert 0.5 <= result.score < 0.8

    
    def test_rejection_below_threshold(self, verification_service):
        """Test weighted score below rejection threshold (< 0.5)"""
        # Create low confidence scenario - but this triggers Rule 2 first
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.40,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.40),
                (CropCondition.HEALTHY, 0.35),
                (CropCondition.OTHER, 0.25)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Normal verdict gives 0.3 confidence
        # This triggers Rule 2 (Drought + Normal Moisture) before weighted score
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        # Rule 2 triggers, resulting in flagged status
        assert result.status == ClaimStatus.FLAGGED_FOR_REVIEW
        assert result.rule_applied == "rule_2_drought_normal_moisture"

    
    def test_high_confidence_both_sources(self, verification_service):
        """Test high confidence from both GT and ST results in auto-approval"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.DROUGHT,
            ml_confidence=0.95,
            top_three_classes=[
                (CropCondition.DROUGHT, 0.95),
                (CropCondition.DISEASE_BLIGHT, 0.03),
                (CropCondition.HEALTHY, 0.02)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Severe stress gives 0.9 confidence
        # Score = (0.95 * 0.6) + (0.9 * 0.4) = 0.57 + 0.36 = 0.93 (well above 0.8)
        space_truth = SpaceTruth(
            ndmi_value=-0.30,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        # Should trigger Rule 1, but verify high score
        assert result.status == ClaimStatus.AUTO_APPROVED
        assert result.score >= 0.8

    
    def test_satellite_confidence_mapping(self, verification_service):
        """Test that satellite verdicts map to correct confidence scores"""
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.PEST_ARMYWORM,
            ml_confidence=0.80,
            top_three_classes=[
                (CropCondition.PEST_ARMYWORM, 0.80),
                (CropCondition.DISEASE_BLIGHT, 0.12),
                (CropCondition.DROUGHT, 0.08)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Test SEVERE_STRESS -> 0.9 confidence
        space_truth_severe = SpaceTruth(
            ndmi_value=-0.30,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        result = verification_service.verify(ground_truth, space_truth_severe)
        assert result.space_truth_confidence == 0.9
        expected_score = (0.80 * 0.6) + (0.9 * 0.4)
        assert abs(result.score - expected_score) < 0.01
        
        # Test MODERATE_STRESS -> 0.6 confidence
        space_truth_moderate = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=5.0,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        result = verification_service.verify(ground_truth, space_truth_moderate)
        assert result.space_truth_confidence == 0.6
        expected_score = (0.80 * 0.6) + (0.6 * 0.4)
        assert abs(result.score - expected_score) < 0.01
        
        # Test NORMAL -> 0.3 confidence
        space_truth_normal = SpaceTruth(
            ndmi_value=0.15,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        result = verification_service.verify(ground_truth, space_truth_normal)
        assert result.space_truth_confidence == 0.3
        expected_score = (0.80 * 0.6) + (0.3 * 0.4)
        assert abs(result.score - expected_score) < 0.01

    
    def test_true_rejection_below_threshold(self, verification_service):
        """Test weighted score below rejection threshold without triggering contextual rules"""
        # Use PEST classification to avoid contextual rules
        ground_truth = GroundTruth(
            image_url="https://example.com/image.jpg",
            ml_class=CropCondition.PEST_ARMYWORM,
            ml_confidence=0.35,
            top_three_classes=[
                (CropCondition.PEST_ARMYWORM, 0.35),
                (CropCondition.HEALTHY, 0.30),
                (CropCondition.OTHER, 0.25)
            ],
            device_tilt=60.0,
            device_azimuth=180.0,
            capture_gps_lat=-1.2921,
            capture_gps_lng=36.8219,
            capture_timestamp=datetime(2024, 6, 15, 10, 30, 0)
        )
        
        # Normal verdict gives 0.3 confidence
        # Score = (0.35 * 0.6) + (0.3 * 0.4) = 0.21 + 0.12 = 0.33 (below 0.5)
        space_truth = SpaceTruth(
            ndmi_value=0.10,
            ndmi_14day_avg=0.12,
            observation_date=datetime(2024, 6, 14, 0, 0, 0),
            cloud_cover_pct=8.0,
            verdict=SatelliteVerdict.NORMAL
        )
        
        result = verification_service.verify(ground_truth, space_truth)
        assert result.status == ClaimStatus.REJECTED
        assert result.score < 0.5
        assert result.rule_applied == "weighted_score"
