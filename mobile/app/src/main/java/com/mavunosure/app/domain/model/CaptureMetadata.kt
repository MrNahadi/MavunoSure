package com.mavunosure.app.domain.model

import java.time.Instant

/**
 * Metadata collected at the moment of photo capture for anti-fraud verification
 */
data class CaptureMetadata(
    val deviceTilt: Float,
    val deviceAzimuth: Float,
    val gpsLatitude: Double,
    val gpsLongitude: Double,
    val gpsAccuracy: Float,
    val timestamp: Instant,
    val inferenceResult: InferenceResult
)
