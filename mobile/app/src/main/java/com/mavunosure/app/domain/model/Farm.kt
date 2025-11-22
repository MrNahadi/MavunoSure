package com.mavunosure.app.domain.model

import java.time.Instant

data class Farm(
    val id: String,
    val farmerName: String,
    val farmerId: String,
    val phoneNumber: String,
    val cropType: CropType,
    val gpsCoordinates: GeoPoint,
    val gpsAccuracy: Float,
    val registeredAt: Instant,
    val registeredBy: String? = null
)

data class GeoPoint(
    val latitude: Double,
    val longitude: Double
)

enum class CropType {
    MAIZE,
    // Additional crops can be added in future
}
