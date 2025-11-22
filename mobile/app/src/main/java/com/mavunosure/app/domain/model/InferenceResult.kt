package com.mavunosure.app.domain.model

data class InferenceResult(
    val primaryClass: CropCondition,
    val confidence: Float,
    val topThreeClasses: List<Pair<CropCondition, Float>>,
    val inferenceTimeMs: Long
)
