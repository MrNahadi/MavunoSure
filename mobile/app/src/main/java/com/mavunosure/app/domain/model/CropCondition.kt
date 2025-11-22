package com.mavunosure.app.domain.model

enum class CropCondition(val displayName: String) {
    HEALTHY("Healthy"),
    DROUGHT("Drought Stress"),
    DISEASE_BLIGHT("Northern Leaf Blight"),
    DISEASE_RUST("Common Rust"),
    PEST_ARMYWORM("Fall Armyworm"),
    OTHER("Other");

    companion object {
        fun fromIndex(index: Int): CropCondition {
            return entries.getOrNull(index) ?: OTHER
        }
    }
}
