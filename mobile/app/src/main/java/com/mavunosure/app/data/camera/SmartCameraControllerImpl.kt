package com.mavunosure.app.data.camera

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import com.google.android.gms.location.FusedLocationProviderClient
import com.mavunosure.app.data.ml.TFLiteClassifier
import com.mavunosure.app.domain.camera.SmartCameraController
import com.mavunosure.app.domain.model.CameraValidation
import com.mavunosure.app.domain.model.InferenceResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.tasks.await
import java.io.File
import javax.inject.Inject
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

class SmartCameraControllerImpl @Inject constructor(
    private val context: Context,
    private val tfliteClassifier: TFLiteClassifier,
    private val locationClient: FusedLocationProviderClient,
    private val sensorManager: SensorManager
) : SmartCameraController, SensorEventListener {

    private var cameraProvider: ProcessCameraProvider? = null
    private var imageCapture: ImageCapture? = null
    private var preview: Preview? = null
    
    private val _validationState = MutableStateFlow(
        CameraValidation(
            isTiltValid = false,
            isGpsValid = false,
            tiltAngle = 0f,
            distanceFromFarm = 0f
        )
    )
    override val validationState: StateFlow<CameraValidation> = _validationState.asStateFlow()
    
    private var currentTilt = 0f
    private var currentLat = 0.0
    private var currentLng = 0.0
    
    private val accelerometerReading = FloatArray(3)
    private val magnetometerReading = FloatArray(3)
    private val rotationMatrix = FloatArray(9)
    private val orientationAngles = FloatArray(3)
    
    companion object {
        private const val MIN_TILT_ANGLE = 45f
        private const val MAX_DISTANCE_METERS = 50f
    }

    init {
        // Register sensor listeners
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
    }

    override fun startPreview() {
        // Preview will be started when bound to lifecycle
    }

    suspend fun bindToLifecycle(
        lifecycleOwner: LifecycleOwner,
        previewView: androidx.camera.view.PreviewView
    ) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
        cameraProvider = cameraProviderFuture.await()
        
        // Set up preview
        preview = Preview.Builder().build().also {
            it.setSurfaceProvider(previewView.surfaceProvider)
        }
        
        // Set up image capture
        imageCapture = ImageCapture.Builder()
            .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
            .build()
        
        // Select back camera
        val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
        
        try {
            // Unbind all use cases before rebinding
            cameraProvider?.unbindAll()
            
            // Bind use cases to camera
            cameraProvider?.bindToLifecycle(
                lifecycleOwner,
                cameraSelector,
                preview,
                imageCapture
            )
        } catch (e: Exception) {
            throw e
        }
    }

    override fun validateCaptureConditions(farmLat: Double, farmLng: Double): CameraValidation {
        val isTiltValid = currentTilt >= MIN_TILT_ANGLE
        val distance = calculateDistance(currentLat, currentLng, farmLat, farmLng)
        val isGpsValid = distance <= MAX_DISTANCE_METERS
        
        val message = when {
            !isTiltValid && !isGpsValid -> "Adjust device angle (${currentTilt.toInt()}°) and move closer to farm (${distance.toInt()}m away)"
            !isTiltValid -> "Point device downward at 45° or more (currently ${currentTilt.toInt()}°)"
            !isGpsValid -> "Move closer to farm location (${distance.toInt()}m away, max 50m)"
            else -> "Ready to capture"
        }
        
        val validation = CameraValidation(
            isTiltValid = isTiltValid,
            isGpsValid = isGpsValid,
            tiltAngle = currentTilt,
            distanceFromFarm = distance,
            message = message
        )
        
        _validationState.value = validation
        return validation
    }

    override suspend fun captureAndInfer(): Result<Pair<Bitmap, InferenceResult>> {
        return try {
            val bitmap = captureImage()
            val inferenceResult = tfliteClassifier.classify(bitmap)
            Result.success(bitmap to inferenceResult)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private suspend fun captureImage(): Bitmap = suspendCancellableCoroutine { continuation ->
        val imageCapture = imageCapture ?: run {
            continuation.resumeWithException(IllegalStateException("Camera not initialized"))
            return@suspendCancellableCoroutine
        }
        
        val photoFile = File.createTempFile("claim_", ".jpg", context.cacheDir)
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()
        
        imageCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(context),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    try {
                        val bitmap = BitmapFactory.decodeFile(photoFile.absolutePath)
                        val rotatedBitmap = rotateBitmap(bitmap, 90f) // Adjust rotation as needed
                        photoFile.delete()
                        continuation.resume(rotatedBitmap)
                    } catch (e: Exception) {
                        continuation.resumeWithException(e)
                    }
                }
                
                override fun onError(exception: ImageCaptureException) {
                    photoFile.delete()
                    continuation.resumeWithException(exception)
                }
            }
        )
    }

    private fun rotateBitmap(bitmap: Bitmap, degrees: Float): Bitmap {
        val matrix = Matrix().apply { postRotate(degrees) }
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    override fun stopPreview() {
        cameraProvider?.unbindAll()
    }

    override fun release() {
        stopPreview()
        sensorManager.unregisterListener(this)
        cameraProvider = null
        imageCapture = null
        preview = null
    }

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
        SensorManager.getRotationMatrix(
            rotationMatrix,
            null,
            accelerometerReading,
            magnetometerReading
        )
        
        SensorManager.getOrientation(rotationMatrix, orientationAngles)
        
        // Calculate tilt angle (pitch)
        val pitch = Math.toDegrees(orientationAngles[1].toDouble()).toFloat()
        currentTilt = abs(pitch)
    }

    suspend fun updateCurrentLocation() {
        try {
            val location = locationClient.lastLocation.await()
            location?.let {
                currentLat = it.latitude
                currentLng = it.longitude
            }
        } catch (e: Exception) {
            // Handle location error
        }
    }

    /**
     * Calculate haversine distance between two GPS coordinates
     */
    private fun calculateDistance(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Float {
        val earthRadius = 6371000.0 // meters
        
        val dLat = Math.toRadians(lat2 - lat1)
        val dLon = Math.toRadians(lon2 - lon1)
        
        val a = sin(dLat / 2) * sin(dLat / 2) +
                cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) *
                sin(dLon / 2) * sin(dLon / 2)
        
        val c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return (earthRadius * c).toFloat()
    }
}
