package com.mavunosure.app.domain.location

import android.Manifest

object LocationPermissionHandler {
    val REQUIRED_PERMISSIONS = arrayOf(
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.ACCESS_COARSE_LOCATION
    )

    const val PERMISSION_RATIONALE = "MavunoSure needs access to your location to accurately " +
            "register farm GPS coordinates. This ensures claims are verified against the correct " +
            "farm location and helps prevent fraud."
}
