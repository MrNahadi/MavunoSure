package com.mavunosure.app.ui.camera

import android.graphics.Bitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mavunosure.app.data.camera.MetadataCollector
import com.mavunosure.app.domain.camera.AntiFraudValidator
import com.mavunosure.app.domain.model.CameraValidation
import com.mavunosure.app.domain.model.CaptureMetadata
import com.mavunosure.app.domain.model.InferenceResult
import com.mavunosure.app.domain.usecase.ClassifyImageUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class CameraUiState {
    object Idle : CameraUiState()
    object Capturing : CameraUiState()
    data class CaptureSuccess(
        val bitmap: Bitmap,
        val inferenceResult: InferenceResult,
        val metadata: CaptureMetadata
    ) : CameraUiState()
    data class Error(val message: String) : CameraUiState()
}

@HiltViewModel
class SmartCameraViewModel @Inject constructor(
    private val classifyImageUseCase: ClassifyImageUseCase,
    private val antiFraudValidator: AntiFraudValidator,
    private val metadataCollector: MetadataCollector
) : ViewModel() {

    private val _uiState = MutableStateFlow<CameraUiState>(CameraUiState.Idle)
    val uiState: StateFlow<CameraUiState> = _uiState.asStateFlow()

    private val _validationState = MutableStateFlow(
        CameraValidation(
            isTiltValid = false,
            isGpsValid = false,
            tiltAngle = 0f,
            distanceFromFarm = 0f
        )
    )
    val validationState: StateFlow<CameraValidation> = _validationState.asStateFlow()

    private var farmLatitude: Double = 0.0
    private var farmLongitude: Double = 0.0

    init {
        metadataCollector.startListening()
    }

    fun setFarmLocation(latitude: Double, longitude: Double) {
        farmLatitude = latitude
        farmLongitude = longitude
    }

    fun updateValidation(currentLat: Double, currentLng: Double) {
        val tilt = metadataCollector.getCurrentTilt()
        val validation = antiFraudValidator.validate(
            tiltAngle = tilt,
            currentLat = currentLat,
            currentLng = currentLng,
            farmLat = farmLatitude,
            farmLng = farmLongitude
        )
        _validationState.value = validation
    }

    fun captureAndClassify(bitmap: Bitmap) {
        viewModelScope.launch {
            _uiState.value = CameraUiState.Capturing
            
            classifyImageUseCase(bitmap).fold(
                onSuccess = { inferenceResult ->
                    val metadata = metadataCollector.collectMetadata(inferenceResult)
                    _uiState.value = CameraUiState.CaptureSuccess(
                        bitmap = bitmap,
                        inferenceResult = inferenceResult,
                        metadata = metadata
                    )
                },
                onFailure = { error ->
                    _uiState.value = CameraUiState.Error(
                        error.message ?: "Failed to classify image"
                    )
                }
            )
        }
    }

    fun resetState() {
        _uiState.value = CameraUiState.Idle
    }

    override fun onCleared() {
        super.onCleared()
        metadataCollector.stopListening()
    }
}
