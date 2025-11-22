package com.mavunosure.app.domain.location

import com.mavunosure.app.domain.model.GeoPoint

data class LocationResult(
    val location: GeoPoint,
    val accuracy: Float,
    val timestamp: Long
)

sealed class LocationAccuracyStatus {
    object Ideal : LocationAccuracyStatus() // < 10m
    object Acceptable : LocationAccuracyStatus() // 10-20m
    data class Warning(val accuracy: Float) : LocationAccuracyStatus() // > 20m
}

interface LocationManager {
    suspend fun getCurrentLocation(): Result<LocationResult>
    suspend fun getLastKnownLocation(): Result<LocationResult>
    fun getAccuracyStatus(accuracy: Float): LocationAccuracyStatus
    fun isLocationEnabled(): Boolean
}
