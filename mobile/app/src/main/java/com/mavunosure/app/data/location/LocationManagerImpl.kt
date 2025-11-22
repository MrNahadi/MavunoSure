package com.mavunosure.app.data.location

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager as AndroidLocationManager
import androidx.core.content.ContextCompat
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import com.mavunosure.app.domain.location.LocationAccuracyStatus
import com.mavunosure.app.domain.location.LocationManager
import com.mavunosure.app.domain.location.LocationResult
import com.mavunosure.app.domain.model.GeoPoint
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.tasks.await
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LocationManagerImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fusedLocationClient: FusedLocationProviderClient
) : LocationManager {

    companion object {
        private const val IDEAL_ACCURACY_THRESHOLD = 10f // meters
        private const val ACCEPTABLE_ACCURACY_THRESHOLD = 20f // meters
    }

    private var cachedLocation: LocationResult? = null

    override suspend fun getCurrentLocation(): Result<LocationResult> {
        return try {
            if (!hasLocationPermission()) {
                return Result.failure(SecurityException("Location permission not granted"))
            }

            if (!isLocationEnabled()) {
                return Result.failure(IllegalStateException("Location services are disabled"))
            }

            // Request high accuracy location
            val cancellationToken = CancellationTokenSource()
            val location = fusedLocationClient.getCurrentLocation(
                Priority.PRIORITY_HIGH_ACCURACY,
                cancellationToken.token
            ).await()

            if (location != null) {
                val result = LocationResult(
                    location = GeoPoint(location.latitude, location.longitude),
                    accuracy = location.accuracy,
                    timestamp = location.time
                )
                // Cache the location for faster subsequent captures
                cachedLocation = result
                Result.success(result)
            } else {
                // Fallback to last known location
                getLastKnownLocation()
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getLastKnownLocation(): Result<LocationResult> {
        return try {
            if (!hasLocationPermission()) {
                return Result.failure(SecurityException("Location permission not granted"))
            }

            // Return cached location if available and recent (< 5 minutes)
            cachedLocation?.let { cached ->
                val age = System.currentTimeMillis() - cached.timestamp
                if (age < 5 * 60 * 1000) { // 5 minutes
                    return Result.success(cached)
                }
            }

            val location = fusedLocationClient.lastLocation.await()

            if (location != null) {
                val result = LocationResult(
                    location = GeoPoint(location.latitude, location.longitude),
                    accuracy = location.accuracy,
                    timestamp = location.time
                )
                cachedLocation = result
                Result.success(result)
            } else {
                Result.failure(IllegalStateException("No last known location available"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override fun getAccuracyStatus(accuracy: Float): LocationAccuracyStatus {
        return when {
            accuracy < IDEAL_ACCURACY_THRESHOLD -> LocationAccuracyStatus.Ideal
            accuracy < ACCEPTABLE_ACCURACY_THRESHOLD -> LocationAccuracyStatus.Acceptable
            else -> LocationAccuracyStatus.Warning(accuracy)
        }
    }

    override fun isLocationEnabled(): Boolean {
        val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as AndroidLocationManager
        return locationManager.isProviderEnabled(AndroidLocationManager.GPS_PROVIDER) ||
                locationManager.isProviderEnabled(AndroidLocationManager.NETWORK_PROVIDER)
    }

    private fun hasLocationPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
    }
}
