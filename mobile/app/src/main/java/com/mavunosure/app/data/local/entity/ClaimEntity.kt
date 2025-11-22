package com.mavunosure.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.mavunosure.app.domain.model.*

@Entity(tableName = "claims")
data class ClaimEntity(
    @PrimaryKey
    val claimId: String,
    val agentId: String,
    val farmId: String,
    val farmGpsLatitude: Double,
    val farmGpsLongitude: Double,
    val timestamp: Long,
    
    // Ground Truth Data
    val mlClass: String,
    val mlConfidence: Float,
    val topThreeClassesJson: String, // JSON serialized list
    val deviceTilt: Float,
    val deviceAzimuth: Float,
    val captureGpsLatitude: Double,
    val captureGpsLongitude: Double,
    
    // Image and sync
    val imageUri: String,
    val syncStatus: String,
    val claimStatus: String = "PENDING"
)

fun ClaimEntity.toDomain(): ClaimPacket {
    // Parse top three classes from JSON
    val topThreeClasses = parseTopThreeClasses(topThreeClassesJson)
    
    return ClaimPacket(
        claimId = claimId,
        agentId = agentId,
        farmId = farmId,
        farmGps = GeoPoint(farmGpsLatitude, farmGpsLongitude),
        timestamp = java.time.Instant.ofEpochMilli(timestamp),
        groundTruth = GroundTruthData(
            mlClass = CropCondition.valueOf(mlClass),
            mlConfidence = mlConfidence,
            topThreeClasses = topThreeClasses,
            deviceTilt = deviceTilt,
            deviceAzimuth = deviceAzimuth,
            captureGps = GeoPoint(captureGpsLatitude, captureGpsLongitude)
        ),
        imageUri = imageUri,
        syncStatus = SyncStatus.valueOf(syncStatus),
        claimStatus = ClaimStatus.valueOf(claimStatus)
    )
}

fun ClaimPacket.toEntity(): ClaimEntity {
    return ClaimEntity(
        claimId = claimId,
        agentId = agentId,
        farmId = farmId,
        farmGpsLatitude = farmGps.latitude,
        farmGpsLongitude = farmGps.longitude,
        timestamp = timestamp.toEpochMilli(),
        mlClass = groundTruth.mlClass.name,
        mlConfidence = groundTruth.mlConfidence,
        topThreeClassesJson = serializeTopThreeClasses(groundTruth.topThreeClasses),
        deviceTilt = groundTruth.deviceTilt,
        deviceAzimuth = groundTruth.deviceAzimuth,
        captureGpsLatitude = groundTruth.captureGps.latitude,
        captureGpsLongitude = groundTruth.captureGps.longitude,
        imageUri = imageUri,
        syncStatus = syncStatus.name,
        claimStatus = claimStatus.name
    )
}

private fun parseTopThreeClasses(json: String): List<Pair<CropCondition, Float>> {
    return try {
        val gson = com.google.gson.Gson()
        val type = object : com.google.gson.reflect.TypeToken<List<Map<String, Any>>>() {}.type
        val list: List<Map<String, Any>> = gson.fromJson(json, type)
        list.map { 
            val condition = CropCondition.valueOf(it["condition"] as String)
            val confidence = (it["confidence"] as Double).toFloat()
            condition to confidence
        }
    } catch (e: Exception) {
        emptyList()
    }
}

private fun serializeTopThreeClasses(classes: List<Pair<CropCondition, Float>>): String {
    val gson = com.google.gson.Gson()
    val list = classes.map { 
        mapOf("condition" to it.first.name, "confidence" to it.second)
    }
    return gson.toJson(list)
}
