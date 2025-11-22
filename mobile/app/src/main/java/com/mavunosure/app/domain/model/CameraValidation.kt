package com.mavunosure.app.domain.model

data class CameraValidation(
    val isTiltValid: Boolean,
    val isGpsValid: Boolean,
    val tiltAngle: Float,
    val distanceFromFarm: Float,
    val message: String = ""
) {
    val isValid: Boolean
        get() = isTiltValid && isGpsValid
}
