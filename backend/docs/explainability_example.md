# AI Explainability Features - Example Output

This document demonstrates the enhanced AI explainability features implemented in the weighted verification service.

## Requirements Implemented

- **13.1**: TFLite model generates confidence scores (0-1) for predicted class
- **13.2**: Top 3 predicted classes with confidence scores
- **13.3**: Store individual Ground Truth and Space Truth confidence scores
- **13.4**: Human-readable explanation when Ground Truth and Space Truth disagree
- **13.5**: Include specific rule or threshold that triggered rejection/flagging

## Example 1: Auto-Approved Claim (Drought + Low Moisture)

```
Double confirmation: Visual drought stress matches severe satellite moisture deficit. High confidence in claim validity.

AI Classification Details:
Primary: drought_stress (85.0% confidence)
Top 3 Predictions: 1. drought_stress: 85.0% | 2. northern_leaf_blight: 10.0% | 3. healthy: 5.0%

Satellite Analysis:
NDMI Value: -0.250 (14-day avg: -0.100)
Verdict: severe_stress
Observation Date: 2024-06-14
Cloud Cover: 5.0%

Verification Logic:
Ground Truth Confidence: 85.0%
Space Truth Confidence: 90.0%
Weighted Score: 0.95 (GT weight: 0.6, ST weight: 0.4)
Rule Applied: rule_1_drought_low_moisture
Decision Threshold: Auto-approve (score > 0.8)
```

## Example 2: Flagged for Review (Drought + Normal Moisture with Disagreement)

```
Possible localized drought or camera fraud - satellite shows normal moisture but ground assessment indicates drought. Manual review required.

AI Classification Details:
Primary: drought_stress (85.0% confidence)
Top 3 Predictions: 1. drought_stress: 85.0% | 2. northern_leaf_blight: 10.0% | 3. healthy: 5.0%

Satellite Analysis:
NDMI Value: 0.150 (14-day avg: 0.120)
Verdict: normal
Observation Date: 2024-06-14
Cloud Cover: 8.0%

Verification Logic:
Ground Truth Confidence: 85.0%
Space Truth Confidence: 30.0%
Weighted Score: 0.65 (GT weight: 0.6, ST weight: 0.4)
Rule Applied: rule_2_drought_normal_moisture
Decision Threshold: Flag for review (score between 0.5 and 0.8)

⚠️ Ground Truth and Space Truth Disagreement Detected:
The visual assessment (drought_stress) and satellite data (normal) show different conditions. This may indicate:
- Localized conditions not visible from satellite
- Recent changes not yet reflected in satellite imagery
- Potential data quality issues requiring manual review
```

## Example 3: Rejected Claim (Invalid Subject Matter)

```
Invalid subject matter - photo does not show a valid crop condition. Claim rejected.

AI Classification Details:
Primary: other (75.0% confidence)
Top 3 Predictions: 1. other: 75.0% | 2. healthy: 15.0% | 3. drought_stress: 10.0%

Satellite Analysis:
NDMI Value: 0.150 (14-day avg: 0.120)
Verdict: normal
Observation Date: 2024-06-14
Cloud Cover: 8.0%

Verification Logic:
Ground Truth Confidence: 75.0%
Space Truth Confidence: 0.0%
Weighted Score: 0.00 (GT weight: 0.6, ST weight: 0.4)
Rule Applied: rule_5_invalid_subject
Decision Threshold: Reject (score < 0.5)
```

## Example 4: Weighted Score Decision (Moderate Confidence)

```
Moderate confidence detected. The weighted score falls in the review range, indicating uncertainty that requires human judgment.

AI Classification Details:
Primary: drought_stress (70.0% confidence)
Top 3 Predictions: 1. drought_stress: 70.0% | 2. northern_leaf_blight: 20.0% | 3. healthy: 10.0%

Satellite Analysis:
NDMI Value: -0.080 (14-day avg: -0.050)
Verdict: moderate_stress
Observation Date: 2024-06-14
Cloud Cover: 12.0%

Verification Logic:
Ground Truth Confidence: 70.0%
Space Truth Confidence: 60.0%
Weighted Score: 0.66 (GT weight: 0.6, ST weight: 0.4)
Rule Applied: weighted_score
Decision Threshold: Flag for review (score between 0.5 and 0.8)
```

## Key Features

### 1. Transparency
Every decision includes:
- The exact confidence scores from both Ground Truth and Space Truth
- The weighted calculation formula and weights used
- The specific rule or threshold that triggered the decision

### 2. Explainability
- Top 3 AI predictions show alternative classifications considered
- Satellite data details provide context for Space Truth assessment
- Human-readable explanations describe why decisions were made

### 3. Disagreement Detection
- Automatically detects when Ground Truth and Space Truth disagree
- Provides possible explanations for disagreements
- Flags potential data quality issues

### 4. Audit Trail
- Rule names are tracked for every decision
- All confidence scores are stored in the database
- Complete explanation text is available for review and reporting

## Benefits

1. **Regulatory Compliance**: Detailed audit trail for insurance regulators
2. **Farmer Trust**: Transparent explanations build confidence in the system
3. **Quality Improvement**: Disagreement detection helps identify system issues
4. **Manual Review Efficiency**: Reviewers have all context needed for decisions
5. **Model Debugging**: Top 3 predictions help identify model weaknesses
