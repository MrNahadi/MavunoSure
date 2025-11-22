package com.mavunosure.app.domain.camera

import com.mavunosure.app.domain.model.CameraValidation
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

@Singleton
class AntiFraudValidator @Inject constructor() {

    companion object {
        const val MIN_TILT_ANGLE_DEGREES = 45f
        const val MAX_DISTANCE_FROM_FARM_METERS = 50f
        private const val EARTH_RADIUS_METERS = 6371000.0
    }

    /**
     * Validate device tilt angle
     * Blocks capture if tilt < 45 degrees to prevent photographing screens or printed images
     */
    fun validateTilt(tiltAngle: Float): Pair<Boolean, String> {
        return if (tiltAngle >= MIN_TILT_ANGLE_DEGREES) {
            true to "Tilt angle valid"
        } else {
            false to "Point device downward at 45° or more (currently ${tiltAngle.toInt()}°)"
        }
    }

    /**
     * Validate GPS distance from registered farm location
     * Blocks capture if distance > 50 meters to prevent remote fraud
     */
    fun validateGpsProximity(
        currentLat: Double,
        currentLng: Double,
        farmLat: Double,
        farmLng: Double
    ): Pair<Boolean, String> {
        val distance = calculateHaversineDistance(currentLat, currentLng, farmLat, farmLng)
        
        return if (distance <= MAX_DISTANCE_FROM_FARM_METERS) {
            true to "Location valid (${distance.toInt()}m from farm)"
        } else {
            false to "Move closer to farm location (${distance.toInt()}m away, max ${MAX_DISTANCE_FROM_FARM_METERS.toInt()}m)"
        }
    }

    /**
     * Perform complete validation check
     */
    fun validate(
        tiltAngle: Float,
        currentLat: Double,
        currentLng: Double,
        farmLat: Double,
        farmLng: Double
    ): CameraValidation {
        val (isTiltValid, tiltMessage) = validateTilt(tiltAngle)
        val (isGpsValid, gpsMessage) = validateGpsProximity(currentLat, currentLng, farmLat, farmLng)
        val distance = calculateHaversineDistance(currentLat, currentLng, farmLat, farmLng)
        
        val message = when {
            !isTiltValid && !isGpsValid -> "$tiltMessage. $gpsMessage"
            !isTiltValid -> tiltMessage
            !isGpsValid -> gpsMessage
            else -> "Ready to capture"
        }
        
        return CameraValidation(
            isTiltValid = isTiltValid,
            isGpsValid = isGpsValid,
            tiltAngle = tiltAngle,
            distanceFromFarm = distance,
            message = message
        )
    }

    /**
     * Calculate haversine distance between two GPS coordinates in meters
     */
    private fun calculateHaversineDistance(
        lat1: Double,
        lon1: Double,
        lat2: Double,
        lon2: Double
    ): Float {
        val dLat = Math.toRadians(lat2 - lat1)
        val dLon = Math.toRadians(lon2 - lon1)
        
        val a = sin(dLat / 2) * sin(dLat / 2) +
                cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) *
                sin(dLon / 2) * sin(dLon / 2)
        
        val c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return (EARTH_RADIUS_METERS * c).toFloat()
    }
}
