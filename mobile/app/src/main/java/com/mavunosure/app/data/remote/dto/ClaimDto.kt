package com.mavunosure.app.data.remote.dto

import com.google.gson.annotations.SerializedName

data class ClaimCreateRequest(
    @SerializedName("agent_id")
    val agentId: String,
    
    @SerializedName("farm_id")
    val farmId: String,
    
    @SerializedName("farm_gps")
    val farmGps: GpsDto,
    
    @SerializedName("timestamp_created")
    val timestampCreated: String, // ISO 8601 format
    
    @SerializedName("ground_truth")
    val groundTruth: GroundTruthDto,
    
    @SerializedName("image_data")
    val imageData: String // Base64 encoded
)

data class GpsDto(
    @SerializedName("lat")
    val latitude: Double,
    
    @SerializedName("lng")
    val longitude: Double
)

data class GroundTruthDto(
    @SerializedName("image_url")
    val imageUrl: String? = null,
    
    @SerializedName("ml_class")
    val mlClass: String,
    
    @SerializedName("ml_confidence")
    val mlConfidence: Float,
    
    @SerializedName("top_three_classes")
    val topThreeClasses: List<ClassificationDto>,
    
    @SerializedName("device_tilt")
    val deviceTilt: Float,
    
    @SerializedName("device_azimuth")
    val deviceAzimuth: Float,
    
    @SerializedName("capture_gps")
    val captureGps: GpsDto
)

data class ClassificationDto(
    @SerializedName("class")
    val className: String,
    
    @SerializedName("confidence")
    val confidence: Float
)

data class ClaimCreateResponse(
    @SerializedName("claim_id")
    val claimId: String,
    
    @SerializedName("status")
    val status: String
)

data class ClaimListResponse(
    @SerializedName("claims")
    val claims: List<ClaimSummaryDto>
)

data class ClaimSummaryDto(
    @SerializedName("id")
    val id: String,
    
    @SerializedName("agent_id")
    val agentId: String,
    
    @SerializedName("farm_id")
    val farmId: String,
    
    @SerializedName("status")
    val status: String,
    
    @SerializedName("created_at")
    val createdAt: String,
    
    @SerializedName("updated_at")
    val updatedAt: String
)

data class ClaimDetailResponse(
    @SerializedName("id")
    val id: String,
    
    @SerializedName("agent_id")
    val agentId: String,
    
    @SerializedName("farm_id")
    val farmId: String,
    
    @SerializedName("status")
    val status: String,
    
    @SerializedName("created_at")
    val createdAt: String,
    
    @SerializedName("updated_at")
    val updatedAt: String,
    
    @SerializedName("image_url")
    val imageUrl: String,
    
    @SerializedName("ml_class")
    val mlClass: String,
    
    @SerializedName("ml_confidence")
    val mlConfidence: Float,
    
    @SerializedName("top_three_classes")
    val topThreeClasses: List<ClassificationDto>,
    
    @SerializedName("device_tilt")
    val deviceTilt: Float,
    
    @SerializedName("device_azimuth")
    val deviceAzimuth: Float,
    
    @SerializedName("capture_gps_lat")
    val captureGpsLat: Double,
    
    @SerializedName("capture_gps_lng")
    val captureGpsLng: Double,
    
    @SerializedName("farm_gps_lat")
    val farmGpsLat: Double,
    
    @SerializedName("farm_gps_lng")
    val farmGpsLng: Double,
    
    @SerializedName("ndmi_value")
    val ndmiValue: Float?,
    
    @SerializedName("ndmi_14day_avg")
    val ndmi14DayAvg: Float?,
    
    @SerializedName("satellite_verdict")
    val satelliteVerdict: String?,
    
    @SerializedName("weighted_score")
    val weightedScore: Float?,
    
    @SerializedName("verdict_explanation")
    val verdictExplanation: String?,
    
    @SerializedName("payout_amount")
    val payoutAmount: Float?,
    
    @SerializedName("payout_status")
    val payoutStatus: String?
)
