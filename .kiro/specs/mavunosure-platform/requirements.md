# Requirements Document

## Introduction

MavunoSure is a B2B2C claim verification platform that reduces the cost of verifying micro-insurance claims for smallholder farmers in Kenya. The system equips Village Agents with an AI-powered mobile tool that combines on-device Computer Vision (Ground Truth) and Satellite Data (Space Truth) to replace expensive expert field visits with a weighted verification system.

## Glossary

- **MavunoSure System**: The complete platform including mobile app, backend services, and web dashboard
- **Village Agent**: Insurance intermediary who visits farms and captures claim data using the mobile app
- **Ground Truth**: Physical data collected at the farm including photos and GPS coordinates
- **Space Truth**: Remote sensing data collected via Sentinel-2 satellite imagery
- **NDMI**: Normalized Difference Moisture Index, a satellite-derived metric for detecting water stress
- **TFLite Model**: TensorFlow Lite machine learning model running on-device for crop assessment
- **Claim Packet**: Encrypted JSON data structure containing all claim information and compressed images
- **Weighted Algorithm**: Backend logic that combines Ground Truth and Space Truth to produce verification scores
- **Smart Snap Camera**: Custom camera interface with anti-fraud checks and real-time ML inference

## Requirements

### Requirement 1: Agent Authentication

**User Story:** As a Village Agent, I want to securely log into the mobile app using my phone number, so that I can access farmer data and submit claims even with intermittent connectivity.

#### Acceptance Criteria

1. WHEN the Village Agent enters a valid phone number, THE MavunoSure System SHALL send an OTP via SMS
2. WHEN the Village Agent enters the correct OTP within 5 minutes, THE MavunoSure System SHALL authenticate the session
3. WHILE the Village Agent is offline, THE MavunoSure System SHALL maintain the authenticated session for at least 7 days
4. IF the OTP expires after 5 minutes, THEN THE MavunoSure System SHALL require the Village Agent to request a new OTP
5. THE MavunoSure System SHALL encrypt and store authentication tokens locally on the device

### Requirement 2: Farm Registration

**User Story:** As a Village Agent, I want to register a farmer's profile with accurate GPS coordinates, so that the system can verify claims against the correct farm location.

#### Acceptance Criteria

1. WHEN the Village Agent creates a farmer profile, THE MavunoSure System SHALL capture farmer name, ID number, phone number, and crop type
2. WHEN the Village Agent captures farm GPS coordinates, THE MavunoSure System SHALL record location with accuracy better than 10 meters
3. IF the GPS accuracy is greater than 20 meters, THEN THE MavunoSure System SHALL display a warning to move to open ground
4. THE MavunoSure System SHALL store farm GPS as either a polygon or center-point coordinate
5. WHERE the crop type is selected, THE MavunoSure System SHALL provide a dropdown limited to supported crops (Maize for MVP)

### Requirement 3: Smart Snap Camera with Real-Time Inference

**User Story:** As a Village Agent, I want to capture crop photos with instant AI assessment and anti-fraud protection, so that I can quickly verify legitimate claims while preventing manipulation.

#### Acceptance Criteria

1. WHEN the Village Agent opens the Smart Snap Camera, THE MavunoSure System SHALL display a custom camera interface with real-time viewfinder
2. WHILE the Village Agent captures an image, THE MavunoSure System SHALL run the TFLite model inference within 2 seconds
3. WHEN the TFLite model completes inference, THE MavunoSure System SHALL display classification result overlay showing one of: Healthy, Drought, Pest, or Other
4. IF the device tilt is less than 45 degrees, THEN THE MavunoSure System SHALL block the shutter and display guidance to adjust angle
5. IF the device GPS is more than 50 meters from the registered farm GPS, THEN THE MavunoSure System SHALL block the shutter and display location error

### Requirement 4: Anti-Fraud Metadata Collection

**User Story:** As an Insurance Provider, I want the system to collect tamper-proof metadata with each claim photo, so that I can detect fraudulent submissions.

#### Acceptance Criteria

1. WHEN the Village Agent captures a claim photo, THE MavunoSure System SHALL record device tilt angle in degrees
2. WHEN the Village Agent captures a claim photo, THE MavunoSure System SHALL record device azimuth bearing
3. WHEN the Village Agent captures a claim photo, THE MavunoSure System SHALL record GPS coordinates with timestamp
4. THE MavunoSure System SHALL prevent uploading images from the device gallery
5. THE MavunoSure System SHALL store images outside the public gallery to prevent tampering before upload

### Requirement 5: Offline Claim Queuing

**User Story:** As a Village Agent, I want to capture claims without internet connectivity, so that I can work efficiently in areas with poor network coverage.

#### Acceptance Criteria

1. WHEN the Village Agent captures a claim while offline, THE MavunoSure System SHALL create an encrypted Claim Packet locally
2. WHEN creating the Claim Packet, THE MavunoSure System SHALL compress the image to reduce storage and bandwidth requirements
3. WHILE the device is offline, THE MavunoSure System SHALL queue all Claim Packets in local encrypted storage
4. WHEN internet connectivity is restored, THE MavunoSure System SHALL automatically sync queued Claim Packets to the backend
5. WHEN sync completes successfully, THE MavunoSure System SHALL remove the local Claim Packet and update claim status

### Requirement 6: Satellite Data Verification

**User Story:** As the Backend System, I want to query satellite imagery for farm moisture levels, so that I can validate Ground Truth assessments with independent Space Truth data.

#### Acceptance Criteria

1. WHEN the MavunoSure System receives a Claim Packet with GPS coordinates, THE MavunoSure System SHALL query Google Earth Engine for Sentinel-2 Level-2A data
2. WHEN querying satellite data, THE MavunoSure System SHALL filter for images with cloud cover less than 20 percent
3. WHEN satellite data is retrieved, THE MavunoSure System SHALL calculate NDMI using B8A and B11 bands
4. WHEN NDMI is calculated, THE MavunoSure System SHALL compare current NDMI against the 14-day moving average
5. WHEN comparison completes, THE MavunoSure System SHALL output a Satellite Verdict of Severe Stress, Moderate, or Normal

### Requirement 7: Weighted Verification Algorithm

**User Story:** As the Backend System, I want to combine Ground Truth and Space Truth using weighted scoring, so that I can make accurate claim decisions with minimal human review.

#### Acceptance Criteria

1. WHEN both Ground Truth and Space Truth are available, THE MavunoSure System SHALL calculate a weighted score using the formula: Score = (Visual_Confidence * 0.6) + (Satellite_Confidence * 0.4)
2. IF the weighted score is greater than 0.8, THEN THE MavunoSure System SHALL set claim status to Auto-Approve
3. IF the weighted score is between 0.5 and 0.79, THEN THE MavunoSure System SHALL set claim status to Flag for Review
4. IF the weighted score is less than 0.5, THEN THE MavunoSure System SHALL set claim status to Reject
5. WHEN Ground Truth shows Drought with high confidence AND Space Truth shows low moisture (NDMI less than -0.2), THE MavunoSure System SHALL Auto-Approve the claim

### Requirement 8: Contextual Verification Rules

**User Story:** As the Backend System, I want to apply context-aware validation rules based on crop type and seasonality, so that I can detect anomalous claims that don't match expected patterns.

#### Acceptance Criteria

1. WHEN Ground Truth shows Drought with high confidence AND Space Truth shows normal moisture, THE MavunoSure System SHALL flag the claim for review due to possible localized drought or fraud
2. WHEN Ground Truth shows Disease (Blight) AND Space Truth shows normal moisture, THE MavunoSure System SHALL Auto-Approve because diseases may not appear on satellite immediately
3. WHEN Ground Truth shows Healthy crop AND Space Truth shows low moisture, THE MavunoSure System SHALL Reject because satellite may be reading bare soil
4. WHEN Ground Truth shows Weed or Other classification, THE MavunoSure System SHALL Reject due to invalid subject matter
5. WHERE the claim is submitted during historically dry harvest months (January or February), THE MavunoSure System SHALL apply stricter validation unless irrigation is documented

### Requirement 9: Mobile Money Payout Integration

**User Story:** As a Farmer, I want to receive automatic mobile money payment when my claim is approved, so that I can quickly access funds to purchase seeds for the next season.

#### Acceptance Criteria

1. WHEN a claim status changes to Approved, THE MavunoSure System SHALL trigger a mobile money payment API call
2. WHEN the payment API call succeeds, THE MavunoSure System SHALL send an SMS notification to the Farmer's phone number
3. WHEN sending the SMS, THE MavunoSure System SHALL include the claim amount in Kenya Shillings
4. IF the payment API call fails, THEN THE MavunoSure System SHALL retry up to 3 times with exponential backoff
5. IF all payment retries fail, THEN THE MavunoSure System SHALL flag the claim for manual payout processing

### Requirement 10: Agent Dashboard

**User Story:** As a Village Agent, I want to view my recent claims and their statuses, so that I can track my work and follow up on pending verifications.

#### Acceptance Criteria

1. WHEN the Village Agent opens the dashboard, THE MavunoSure System SHALL display a prominent button to start a new verification
2. WHEN the Village Agent views the dashboard, THE MavunoSure System SHALL display a list of recent claims with status indicators
3. WHERE a claim status is Pending, THE MavunoSure System SHALL display a yellow indicator icon
4. WHERE a claim status is Approved or Paid, THE MavunoSure System SHALL display a green indicator icon
5. WHERE a claim status is Rejected, THE MavunoSure System SHALL display a red indicator icon

### Requirement 11: Performance and Reliability

**User Story:** As a Village Agent with a mid-range Android device and limited data connectivity, I want the app to run quickly and work offline, so that I can efficiently process claims in rural areas.

#### Acceptance Criteria

1. WHEN the TFLite model processes an image on a mid-range Android device, THE MavunoSure System SHALL complete inference within 2 seconds
2. THE MavunoSure System SHALL maintain a total APK size of less than 40 megabytes
3. WHILE the device is offline, THE MavunoSure System SHALL provide 100 percent functionality for data collection
4. WHEN the Village Agent captures GPS coordinates, THE MavunoSure System SHALL handle GPS drift gracefully
5. THE MavunoSure System SHALL protect all backend API endpoints with Bearer Token authentication

### Requirement 12: Data Integrity and Security

**User Story:** As an Insurance Provider, I want claim data to be tamper-proof and securely transmitted, so that I can trust the verification results and protect farmer privacy.

#### Acceptance Criteria

1. WHEN the MavunoSure System stores claim images on the device, THE MavunoSure System SHALL prevent access from the public gallery
2. WHEN the MavunoSure System transmits Claim Packets, THE MavunoSure System SHALL encrypt data in transit using TLS 1.2 or higher
3. WHEN the MavunoSure System stores Claim Packets locally, THE MavunoSure System SHALL encrypt data at rest
4. THE MavunoSure System SHALL require Bearer Token authentication for all backend API endpoints
5. WHEN the MavunoSure System stores farmer personal data, THE MavunoSure System SHALL comply with Kenya Data Protection Act requirements

### Requirement 13: AI Explainability and Transparency

**User Story:** As an Insurance Provider, I want to understand why the AI made specific classification decisions, so that I can audit the system and explain decisions to farmers and regulators.

#### Acceptance Criteria

1. WHEN the TFLite model classifies a crop image, THE MavunoSure System SHALL generate a confidence score between 0 and 1 for the predicted class
2. WHEN the TFLite model classifies a crop image, THE MavunoSure System SHALL provide confidence scores for the top 3 predicted classes
3. WHEN the Weighted Algorithm calculates a final score, THE MavunoSure System SHALL store the individual Ground Truth confidence and Space Truth confidence values
4. WHEN a claim is flagged for review, THE MavunoSure System SHALL provide a human-readable explanation of why Ground Truth and Space Truth disagreed
5. WHERE the claim status is Reject, THE MavunoSure System SHALL include the specific rule or threshold that triggered the rejection

### Requirement 14: PDF Report Generation and Export

**User Story:** As an Insurance Provider, I want to generate and export PDF reports for claims, so that I can maintain audit trails and share documentation with stakeholders.

#### Acceptance Criteria

1. WHEN an Insurance Provider requests a claim report, THE MavunoSure System SHALL generate a PDF document containing all claim details
2. WHEN generating the PDF report, THE MavunoSure System SHALL include the claim photo, GPS coordinates, timestamps, and verification scores
3. WHEN generating the PDF report, THE MavunoSure System SHALL include the AI classification results with confidence scores and explainability data
4. WHEN generating the PDF report, THE MavunoSure System SHALL include the satellite data visualization showing NDMI values and observation dates
5. WHEN the PDF is generated, THE MavunoSure System SHALL provide a download link valid for 7 days or allow immediate export to the user's device
