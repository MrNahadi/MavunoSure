# Implementation Plan

- [x] 1. Set up project structure and development environment





  - Create monorepo structure with separate directories for mobile app, backend, and web dashboard
  - Initialize Android project with Kotlin and Jetpack Compose
  - Initialize FastAPI backend project with Python 3.11+
  - Initialize React TypeScript project for web dashboard
  - Set up Docker Compose for local development with PostgreSQL and Redis
  - Configure environment variables and secrets management
  - _Requirements: 11.2, 11.3, 12.4_

- [x] 2. Implement backend authentication service




  - [x] 2.1 Create agent database schema and models


    - Write PostgreSQL migration for agents table
    - Create Pydantic models for agent data structures
    - Implement SQLAlchemy ORM models
    - _Requirements: 1.1, 1.2_
  - [x] 2.2 Implement OTP authentication endpoints


    - Create POST /api/v1/auth/send-otp endpoint with Africa's Talking SMS integration
    - Create POST /api/v1/auth/verify-otp endpoint with JWT token generation
    - Create POST /api/v1/auth/refresh-token endpoint
    - Implement JWT token validation middleware
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 2.3 Write authentication service tests



    - Write unit tests for OTP generation and validation logic
    - Write integration tests for authentication endpoints
    - _Requirements: 1.1, 1.2_

- [x] 3. Implement backend farm management service








  - [x] 3.1 Create farm database schema and models


    - Write PostgreSQL migration for farms table with GPS columns
    - Create Pydantic models for farm registration

    - Implement SQLAlchemy ORM models with spatial indexing


    - _Requirements: 2.1, 2.2, 2.4_
  - [x] 3.2 Implement farm registration endpoints

    - Create POST /api/v1/farms endpoint with GPS validation
    - Create GET /api/v1/farms/:id endpoint

    - Create GET /api/v1/farms/search endpoint with farmerId query parameter
    - Implement GPS accuracy validation (< 10m ideal, warn > 20m)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 3.3 Write farm service tests

    - Write unit tests for GPS validation logic
    - Write integration tests for farm CRUD operations
    - _Requirements: 2.1, 2.2_

- [x] 4. Implement satellite verification service





  - [x] 4.1 Set up Google Earth Engine integration


    - Configure GEE authentication with service account
    - Create GEE client wrapper with connection pooling
    - Implement error handling and retry logic for GEE API calls
    - _Requirements: 6.1, 6.2_
  - [x] 4.2 Implement NDMI calculation logic


    - Write function to query Sentinel-2 L2A collection with date and location filters
    - Implement cloud cover filtering (< 20%)
    - Calculate NDMI using (B8A - B11) / (B8A + B11) formula
    - Calculate 14-day moving average NDMI for baseline comparison
    - Generate satellite verdict (Severe Stress / Moderate / Normal)
    - _Requirements: 6.2, 6.3, 6.4, 6.5_
  - [x] 4.3 Implement satellite data caching

    - Create Redis cache layer for satellite queries (24-hour TTL)
    - Implement cache key generation based on GPS coordinates and date
    - _Requirements: 6.1_
  - [x] 4.4 Write satellite service tests


    - Write unit tests for NDMI calculation with mock GEE data
    - Write integration tests with GEE sandbox environment
    - _Requirements: 6.2, 6.3, 6.4_

- [-] 5. Implement weighted verification algorithm


  - [x] 5.1 Create weighted algorithm engine


    - Implement base weighted scoring: Score = (Visual_Confidence * 0.6) + (Satellite_Confidence * 0.4)
    - Implement threshold logic (> 0.8 Auto-Approve, 0.5-0.79 Flag, < 0.5 Reject)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [x] 5.2 Implement contextual verification rules

    - Implement Rule 1: Drought + Low Moisture (< -0.2) → Auto-Approve
    - Implement Rule 2: Drought + Normal Moisture → Flag for Review
    - Implement Rule 3: Disease + Normal Moisture → Auto-Approve
    - Implement Rule 4: Healthy + Low Moisture → Reject
    - Implement Rule 5: Weed/Other → Reject
    - _Requirements: 7.5, 8.1, 8.2, 8.3, 8.4_
  - [x] 5.3 Implement seasonality validation rules

    - Add hardcoded FEWS NET crop calendar data for Kenya
    - Implement logic to validate claim timing against historical patterns
    - Apply stricter validation for drought claims during dry harvest months
    - _Requirements: 8.5_
  - [x] 5.4 Add AI explainability features





    - Store individual Ground Truth and Space Truth confidence scores
    - Generate human-readable explanations for each verification decision
    - Include specific rule or threshold that triggered rejection/flagging
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_


  - [x] 5.5 Write weighted algorithm tests






    - Write unit tests for all contextual rules with various input combinations
    - Write unit tests for seasonality validation
    - Write unit tests for explainability output
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 13.4, 13.5_

- [x] 6. Implement claim processing service





  - [x] 6.1 Create claim database schema and models


    - Write PostgreSQL migration for claims table with all Ground Truth and Space Truth fields
    - Create Pydantic models for claim creation and responses
    - Implement SQLAlchemy ORM models with proper relationships
    - Add database indexes for agent_id, farm_id, status, and created_at
    - _Requirements: 5.1, 5.2, 6.1_

  - [x] 6.2 Implement claim submission endpoint

    - Create POST /api/v1/claims endpoint
    - Implement image upload to S3/Cloud Storage
    - Store claim data in PostgreSQL
    - Enqueue async task for satellite verification
    - Return claim_id immediately to client
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 6.3 Implement claim retrieval endpoints

    - Create GET /api/v1/claims/:id endpoint with full claim details
    - Create GET /api/v1/claims endpoint with filtering by agentId and status
    - Implement pagination for claims list
    - _Requirements: 10.1, 10.2_
  - [x] 6.4 Implement async claim processing workflow


    - Create Celery task for satellite verification
    - Create Celery task for weighted algorithm execution
    - Chain tasks: upload → satellite → weighted algorithm → payment
    - Implement error handling and retry logic for each task
    - _Requirements: 5.4, 6.1, 7.1_

  - [x] 6.5 Write claim service tests



    - Write integration tests for claim submission flow
    - Write integration tests for claim retrieval with filters
    - Write unit tests for async task chaining
    - _Requirements: 5.1, 5.2, 6.1, 7.1_

- [-] 7. Implement payment service




  - [x] 7.1 Create mobile money API integration


    - Implement mobile money API client (simulated for MVP)
    - Add payment transaction logging to database
    - _Requirements: 9.1_

  - [x] 7.2 Implement payout workflow




    - Create payment trigger logic when claim status changes to Approved
    - Implement retry logic with exponential backoff (up to 3 attempts)
    - Flag claims for manual processing after failed retries
    - Update claim payout_status in database
    - _Requirements: 9.1, 9.4, 9.5_
  - [x] 7.3 Implement SMS notification service





    - Integrate Africa's Talking SMS API
    - Send SMS to farmer on successful payment with amount in KES
    - _Requirements: 9.2, 9.3_
  - [x] 7.4 Write payment service tests




    - Write unit tests for retry logic with mock API failures
    - Write integration tests for SMS sending
    - _Requirements: 9.1, 9.4_

- [x] 8. Implement PDF report generation service






  - [x] 8.1 Create report generation endpoint

    - Create GET /api/v1/reports/:claimId/pdf endpoint
    - Implement authentication and authorization checks
    - _Requirements: 14.1_

  - [x] 8.2 Implement PDF generation logic

    - Use ReportLab to generate PDF documents
    - Include claim photo with proper sizing
    - Include GPS coordinates and timestamps
    - Include Ground Truth section with ML classification and confidence scores
    - Include top 3 predicted classes for explainability
    - Include Space Truth section with NDMI values and satellite observation date
    - Include satellite data visualization (NDMI chart or map)
    - Include final verification result with weighted score and explanation
    - _Requirements: 14.2, 14.3, 14.4_

  - [x] 8.3 Implement PDF storage and download


    - Store generated PDFs in S3/Cloud Storage
    - Generate signed download URLs valid for 7 days
    - Return download link in API response
    - _Requirements: 14.5_

  - [x] 8.4 Write report service tests

    - Write integration tests for PDF generation with sample claim data
    - Verify PDF contains all required sections
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [x] 9. Implement Android mobile app authentication






  - [x] 9.1 Set up Android project structure

    - Configure Gradle with Kotlin, Jetpack Compose, and required dependencies
    - Set up dependency injection with Hilt
    - Configure Room database for local storage
    - Set up Retrofit for API communication
    - _Requirements: 11.2_
  - [x] 9.2 Implement authentication repository


    - Create AuthRepository interface and implementation
    - Implement sendOTP() function calling backend API
    - Implement verifyOTP() function with JWT token storage in Android Keystore
    - Implement refreshToken() function
    - Implement isSessionValid() function checking 7-day offline grace period
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 9.3 Create login UI screens

    - Create phone number input screen with validation
    - Create OTP input screen with countdown timer
    - Implement navigation between login screens
    - Show loading states and error messages
    - _Requirements: 1.1, 1.2_
  - [x] 9.4 Write authentication tests


    - Write unit tests for AuthRepository logic
    - Write UI tests for login flow with Espresso
    - _Requirements: 1.1, 1.2_

- [x] 10. Implement Android farm registration




  - [x] 10.1 Create farm data models and repository


    - Create Farm data class with all required fields
    - Create Room entity for local farm storage
    - Create FarmRepository interface and implementation
    - Implement registerFarm() function with API sync
    - Implement getFarmById() and searchFarmsByFarmerId() functions
    - _Requirements: 2.1, 2.4_

  - [x] 10.2 Implement GPS capture logic

    - Set up FusedLocationProviderClient
    - Request location permissions with proper rationale
    - Implement location accuracy checks (< 10m ideal, warn > 20m)
    - Cache last known location for faster subsequent captures
    - _Requirements: 2.2, 2.3_

  - [x] 10.3 Create farm registration UI

    - Create farmer information input form (name, ID, phone, crop type)
    - Add GPS capture button with real-time accuracy display
    - Show warning when GPS accuracy > 20m
    - Implement form validation
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 10.4 Write farm registration tests

    - Write unit tests for GPS validation logic
    - Write UI tests for farm registration flow
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 11. Implement Android Smart Snap Camera




  - [x] 11.1 Set up TFLite model integration


    - Add maize_disease_v1.tflite model to assets folder
    - Create TFLite interpreter wrapper class
    - Implement image preprocessing (resize to 224x224, normalize)
    - Load model on app startup with GPU delegate if available
    - _Requirements: 3.2, 11.1_

  - [x] 11.2 Implement camera controller

    - Set up CameraX API for camera preview
    - Create SmartCameraController interface and implementation
    - Implement real-time viewfinder display
    - _Requirements: 3.1_

  - [x] 11.3 Implement anti-fraud validation checks

    - Use SensorManager to get device tilt angle
    - Block shutter if tilt < 45 degrees with guidance message
    - Calculate haversine distance between device GPS and farm GPS
    - Block shutter if distance > 50m with location error message
    - Prevent gallery picker access (force real-time capture only)
    - _Requirements: 3.4, 3.5, 4.1, 4.2, 4.3, 4.4_

  - [x] 11.4 Implement real-time ML inference

    - Run TFLite inference on captured image in background thread
    - Display classification result overlay (Healthy, Drought, Pest, Other)
    - Show confidence score for primary classification
    - Ensure inference completes within 2 seconds
    - _Requirements: 3.2, 3.3, 11.1, 13.1_

  - [x] 11.5 Implement metadata collection

    - Capture device tilt angle at moment of photo
    - Capture device azimuth bearing
    - Capture GPS coordinates with timestamp
    - Store top 3 classification results with confidence scores
    - _Requirements: 4.1, 4.2, 4.3, 13.2_
  - [x] 11.6 Create Smart Snap Camera UI


    - Create full-screen camera viewfinder
    - Add guidance text overlay ("Point at the most affected leaf. Hold steady.")
    - Add validation indicator (GREEN when tilt/GPS valid, RED when invalid)
    - Show classification result popup after capture
    - Add "Proceed" button to confirm and save claim
    - _Requirements: 3.1, 3.3, 3.4, 3.5_

  - [x] 11.7 Write camera tests

    - Write unit tests for anti-fraud validation logic
    - Write unit tests for TFLite inference preprocessing
    - Write integration tests for camera capture flow
    - _Requirements: 3.4, 3.5, 4.1, 4.2_

- [x] 12. Implement Android offline queue


  - [x] 12.1 Create claim data models and Room entities


    - Create ClaimPacket data class with all required fields
    - Create GroundTruthData data class
    - Create Room entities for local claim storage
    - Add SyncStatus enum (PENDING, SYNCING, SYNCED, FAILED)
    - _Requirements: 5.1, 5.2_

  - [x] 12.2 Implement offline queue repository

    - Create OfflineQueueRepository interface and implementation
    - Implement enqueueClaim() function with AES-256 encryption
    - Implement image compression (JPEG 80% quality, max 1024px)
    - Implement getPendingClaims() function
    - Implement syncClaim() function calling backend API
    - Implement markSynced() function to update local status
    - _Requirements: 5.1, 5.2, 5.3, 12.1, 12.2, 12.3_


  - [x] 12.3 Implement auto-sync with WorkManager

    - Create SyncWorker with network constraint
    - Schedule periodic sync every 15 minutes when online
    - Implement exponential backoff for failed sync attempts
    - Update claim status in local database after successful sync

    - _Requirements: 5.4, 11.3_
  - [x] 12.4 Implement image security

    - Store images in app-private directory (not public gallery)
    - Encrypt image files using AES-256 with key from Android Keystore
    - Delete local images after successful sync
    - _Requirements: 4.5, 12.1_

  - [x] 12.5 Write offline queue tests

    - Write unit tests for encryption/decryption logic
    - Write unit tests for image compression
    - Write integration tests for sync workflow
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [-] 13. Implement Android agent dashboard




  - [x] 13.1 Create dashboard UI






    - Create main dashboard screen with "New Verification" button
    - Create claims list with status indicators (Pending=yellow, Approved/Paid=green, Rejected=red)
    - Implement pull-to-refresh for claims list
    - Add navigation to claim detail screen
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - [x] 13.2 Implement claims list repository







    - Create function to fetch claims from local database
    - Implement filtering by status
    - Implement sorting by created_at descending
    - Sync claims from backend API when online
    - _Requirements: 10.2_
  - [x] 13.3 Write dashboard tests





    - Write UI tests for dashboard navigation
    - Write unit tests for claims filtering logic
    - _Requirements: 10.1, 10.2_

- [-] 14. Implement web dashboard authentication


  - [x] 14.1 Set up React project structure


    - Configure Vite with React and TypeScript
    - Set up React Router for navigation
    - Configure TanStack Query for server state management
    - Set up Zustand for UI state management
    - Configure shadcn/ui component library
    - _Requirements: 11.5_

  - [x] 14.2 Implement authentication flow

    - Create login page with phone number and OTP inputs
    - Implement authentication context with JWT token management
    - Create protected route wrapper component
    - Store auth tokens in localStorage with expiration
    - _Requirements: 1.1, 1.2_

  - [ ] 14.3 Write authentication tests
    - Write unit tests for auth context logic
    - Write integration tests for login flow
    - _Requirements: 1.1, 1.2_

- [ ] 15. Implement web dashboard claims interface
  - [ ] 15.1 Create claims list page
    - Create paginated claims table with columns: ID, Farmer, Status, Date, Score
    - Implement status filters (All, Pending, Approved, Flagged, Rejected, Paid)
    - Implement search by farmer name or ID
    - Add sorting by date, score, status
    - Show status badges with color coding
    - _Requirements: 10.2, 10.3, 10.4, 10.5_
  - [ ] 15.2 Create claim detail page
    - Display farmer information section
    - Display claim photo with zoom capability
    - Display Ground Truth section with ML classification and confidence scores
    - Display top 3 predicted classes for explainability
    - Display Space Truth section with NDMI values and satellite data
    - Display final verification result with weighted score and explanation
    - Add map showing farm location with GPS coordinates
    - _Requirements: 13.3, 13.4, 13.5, 14.2, 14.3, 14.4_
  - [ ] 15.3 Create review interface for flagged claims
    - Create review page for claims with status "Flagged for Review"
    - Display all claim details side-by-side (Ground Truth vs Space Truth)
    - Add manual approval/rejection buttons
    - Add text area for reviewer notes
    - Implement PATCH /api/v1/claims/:id/status endpoint call
    - _Requirements: 7.3, 8.1, 13.4, 13.5_
  - [ ] 15.4 Write claims interface tests
    - Write integration tests for claims list filtering
    - Write integration tests for claim detail display
    - _Requirements: 10.2, 13.3_

- [ ] 16. Implement web dashboard PDF export
  - [ ] 16.1 Create PDF export UI
    - Add "Export PDF" button on claim detail page
    - Show loading spinner during PDF generation
    - Display download link when PDF is ready
    - Implement error handling for failed generation
    - _Requirements: 14.1, 14.5_
  - [ ] 16.2 Integrate with backend report service
    - Call GET /api/v1/reports/:claimId/pdf endpoint
    - Handle PDF download with proper MIME type
    - Implement client-side PDF preview (optional)
    - _Requirements: 14.1, 14.5_
  - [ ] 16.3 Write PDF export tests
    - Write integration tests for PDF download flow
    - _Requirements: 14.1, 14.5_

- [ ] 17. Implement satellite data visualization
  - [ ] 17.1 Create map component
    - Integrate Leaflet or Mapbox for map display
    - Display farm location marker with GPS coordinates
    - Add satellite imagery base layer
    - _Requirements: 14.4_
  - [ ] 17.2 Add NDMI visualization
    - Create NDMI value chart showing current vs 14-day average
    - Add color-coded NDMI overlay on map (red=stress, green=healthy)
    - Display observation date and cloud cover percentage
    - _Requirements: 6.5, 14.4_
  - [ ] 17.3 Write visualization tests
    - Write unit tests for NDMI chart data transformation
    - _Requirements: 14.4_

- [ ] 18. Implement API security and rate limiting
  - [ ] 18.1 Add authentication middleware
    - Implement JWT token validation middleware for all protected endpoints
    - Add Bearer token extraction from Authorization header
    - Return 401 Unauthorized for invalid/expired tokens
    - _Requirements: 11.5, 12.4_
  - [ ] 18.2 Implement rate limiting
    - Add rate limiting middleware using slowapi or similar
    - Set limits: 100 requests per minute per IP for general endpoints
    - Set limits: 10 requests per minute for claim submission
    - Return 429 Too Many Requests when limit exceeded
    - _Requirements: 11.5_
  - [ ] 18.3 Add input validation and sanitization
    - Validate all request bodies against Pydantic schemas
    - Sanitize string inputs to prevent injection attacks
    - Validate file uploads (size, type, content)
    - _Requirements: 12.4_
  - [ ] 18.4 Write security tests
    - Write tests for authentication middleware with invalid tokens
    - Write tests for rate limiting behavior
    - Write tests for input validation edge cases
    - _Requirements: 11.5, 12.4_

- [ ] 19. Set up deployment and monitoring
  - [ ] 19.1 Create Docker containers
    - Create Dockerfile for FastAPI backend
    - Create Dockerfile for React web dashboard
    - Create docker-compose.yml for local development
    - Configure environment variables for production
    - _Requirements: 11.3_
  - [ ] 19.2 Set up error tracking
    - Integrate Sentry for backend error tracking
    - Integrate Sentry for mobile app crash reporting
    - Configure error alerting for critical issues
    - _Requirements: 11.5_
  - [ ] 19.3 Set up logging
    - Implement structured JSON logging in backend
    - Log all API requests with request ID
    - Log all satellite API calls and responses
    - Log all payment transactions
    - Anonymize PII in logs
    - _Requirements: 12.5_
  - [ ] 19.4 Create deployment documentation
    - Document environment variables and configuration
    - Document deployment steps for backend and web dashboard
    - Document mobile app build and release process
    - _Requirements: 11.3_

- [ ] 20. Integration and end-to-end testing
  - [ ] 20.1 Create test data and fixtures
    - Create test farms with known GPS coordinates in Kenya
    - Create sample images for each crop condition (Healthy, Drought, Disease, Pest)
    - Create mock satellite data for predictable test results
    - _Requirements: 11.1, 11.2, 11.3_
  - [ ] 20.2 Test critical user flows
    - Test flow: Agent login → Farm registration → Claim capture → Auto-approval → Payment
    - Test flow: Claim flagged for review → Manual approval → Payment
    - Test flow: Offline claim capture → Sync when online → Processing
    - Test flow: Export PDF report for approved claim
    - _Requirements: 1.1, 2.1, 3.1, 5.1, 7.1, 9.1, 14.1_
  - [ ] 20.3 Perform load testing
    - Simulate 100 concurrent claim submissions
    - Test database query performance under load
    - Test file upload handling with large images
    - _Requirements: 11.1, 11.2_
