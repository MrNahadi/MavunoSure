package com.mavunosure.app.domain.camera

import android.graphics.Bitmap
import com.mavunosure.app.domain.model.CameraValidation
import com.mavunosure.app.domain.model.InferenceResult
import kotlinx.coroutines.flow.StateFlow

interface SmartCameraController {
    val validationState: StateFlow<CameraValidation>
    
    fun startPreview()
    fun validateCaptureConditions(farmLat: Double, farmLng: Double): CameraValidation
    suspend fun captureAndInfer(): Result<Pair<Bitmap, InferenceResult>>
    fun stopPreview()
    fun release()
}
