package com.mavunosure.app.domain.model

data class GroundTruthData(
    val mlClass: CropCondition,
    val mlConfidence: Float,
    val topThreeClasses: List<Pair<CropCondition, Float>>,
    val deviceTilt: Float,
    val deviceAzimuth: Float,
    val captureGps: GeoPoint
)
