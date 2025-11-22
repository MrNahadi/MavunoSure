package com.mavunosure.app.data.camera

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import com.google.android.gms.location.FusedLocationProviderClient
import com.mavunosure.app.domain.model.CaptureMetadata
import com.mavunosure.app.domain.model.InferenceResult
import kotlinx.coroutines.tasks.await
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs

/**
 * Collects device sensor and location metadata at the moment of capture
 */
@Singleton
class MetadataCollector @Inject constructor(
    private val sensorManager: SensorManager,
    private val locationClient: FusedLocationProviderClient
) : SensorEventListener {

    private val accelerometerReading = FloatArray(3)
    private val magnetometerReading = FloatArray(3)
    private val rotationMatrix = FloatArray(9)
    private val orientationAngles = FloatArray(3)
    
    private var currentTilt = 0f
    private var currentAzimuth = 0f
    private var isListening = false

    /**
     * Start listening to sensors
     */
    fun startListening() {
        if (isListening) return
        
        sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.also { accelerometer ->
            sensorManager.registerListener(
                this,
                accelerometer,
                SensorManager.SENSOR_DELAY_NORMAL
            )
        }
        
        sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)?.also { magneticField ->
            sensorManager.registerListener(
                this,
                magneticField,
                SensorManager.SENSOR_DELAY_NORMAL
            )
        }
        
        isListening = true
    }

    /**
     * Stop listening to sensors
     */
    fun stopListening() {
        if (!isListening) return
        sensorManager.unregisterListener(this)
        isListening = false
    }

    /**
     * Collect all metadata at the moment of capture
     */
    suspend fun collectMetadata(inferenceResult: InferenceResult): CaptureMetadata {
        val location = getCurrentLocation()
        
        return CaptureMetadata(
            deviceTilt = currentTilt,
            deviceAzimuth = currentAzimuth,
            gpsLatitude = location.latitude,
            gpsLongitude = location.longitude,
            gpsAccuracy = location.accuracy,
            timestamp = Instant.now(),
            inferenceResult = inferenceResult
        )
    }

    /**
     * Get current device location
     */
    private suspend fun getCurrentLocation(): Location {
        return try {
            locationClient.lastLocation.await() ?: Location("").apply {
                latitude = 0.0
                longitude = 0.0
                accuracy = 0f
            }
        } catch (e: Exception) {
            Location("").apply {
                latitude = 0.0
                longitude = 0.0
                accuracy = 0f
            }
        }
    }

    /**
     * Get current tilt angle
     */
    fun getCurrentTilt(): Float = currentTilt

    /**
     * Get current azimuth bearing
     */
    fun getCurrentAzimuth(): Float = currentAzimuth

    override fun onSensorChanged(event: SensorEvent?) {
        event ?: return
        
        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                System.arraycopy(event.values, 0, accelerometerReading, 0, accelerometerReading.size)
            }
            Sensor.TYPE_MAGNETIC_FIELD -> {
                System.arraycopy(event.values, 0, magnetometerReading, 0, magnetometerReading.size)
            }
        }
        
        updateOrientationAngles()
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // Not needed for this implementation
    }

    private fun updateOrientationAngles() {
        val success = SensorManager.getRotationMatrix(
            rotationMatrix,
            null,
            accelerometerReading,
            magnetometerReading
        )
        
        if (success) {
            SensorManager.getOrientation(rotationMatrix, orientationAngles)
            
            // Azimuth (rotation around Z axis) - 0 to 360 degrees
            currentAzimuth = Math.toDegrees(orientationAngles[0].toDouble()).toFloat()
            if (currentAzimuth < 0) {
                currentAzimuth += 360f
            }
            
            // Pitch (rotation around X axis) - tilt angle
            val pitch = Math.toDegrees(orientationAngles[1].toDouble()).toFloat()
            currentTilt = abs(pitch)
        }
    }
}
