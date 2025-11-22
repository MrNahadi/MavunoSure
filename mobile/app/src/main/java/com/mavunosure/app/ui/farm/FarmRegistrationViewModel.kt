package com.mavunosure.app.ui.farm

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mavunosure.app.domain.location.LocationAccuracyStatus
import com.mavunosure.app.domain.location.LocationManager
import com.mavunosure.app.domain.location.LocationResult
import com.mavunosure.app.domain.model.CropType
import com.mavunosure.app.domain.model.Farm
import com.mavunosure.app.domain.model.GeoPoint
import com.mavunosure.app.domain.repository.FarmRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.Instant
import java.util.UUID
import javax.inject.Inject

data class FarmRegistrationUiState(
    val farmerName: String = "",
    val farmerId: String = "",
    val phoneNumber: String = "",
    val cropType: CropType = CropType.MAIZE,
    val location: LocationResult? = null,
    val accuracyStatus: LocationAccuracyStatus? = null,
    val isCapturingLocation: Boolean = false,
    val isRegistering: Boolean = false,
    val error: String? = null,
    val registrationSuccess: Boolean = false,
    val validationErrors: Map<String, String> = emptyMap()
)

@HiltViewModel
class FarmRegistrationViewModel @Inject constructor(
    private val farmRepository: FarmRepository,
    private val locationManager: LocationManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(FarmRegistrationUiState())
    val uiState: StateFlow<FarmRegistrationUiState> = _uiState.asStateFlow()

    fun updateFarmerName(name: String) {
        _uiState.update { it.copy(farmerName = name) }
        clearValidationError("farmerName")
    }

    fun updateFarmerId(id: String) {
        _uiState.update { it.copy(farmerId = id) }
        clearValidationError("farmerId")
    }

    fun updatePhoneNumber(phone: String) {
        _uiState.update { it.copy(phoneNumber = phone) }
        clearValidationError("phoneNumber")
    }

    fun updateCropType(cropType: CropType) {
        _uiState.update { it.copy(cropType = cropType) }
    }

    fun captureLocation() {
        viewModelScope.launch {
            _uiState.update { it.copy(isCapturingLocation = true, error = null) }

            if (!locationManager.isLocationEnabled()) {
                _uiState.update {
                    it.copy(
                        isCapturingLocation = false,
                        error = "Location services are disabled. Please enable GPS."
                    )
                }
                return@launch
            }

            locationManager.getCurrentLocation()
                .onSuccess { locationResult ->
                    val accuracyStatus = locationManager.getAccuracyStatus(locationResult.accuracy)
                    _uiState.update {
                        it.copy(
                            location = locationResult,
                            accuracyStatus = accuracyStatus,
                            isCapturingLocation = false,
                            error = null
                        )
                    }
                }
                .onFailure { exception ->
                    _uiState.update {
                        it.copy(
                            isCapturingLocation = false,
                            error = "Failed to capture location: ${exception.message}"
                        )
                    }
                }
        }
    }

    fun registerFarm() {
        if (!validateForm()) {
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isRegistering = true, error = null) }

            val currentState = _uiState.value
            val location = currentState.location ?: run {
                _uiState.update {
                    it.copy(
                        isRegistering = false,
                        error = "Please capture GPS location first"
                    )
                }
                return@launch
            }

            val farm = Farm(
                id = UUID.randomUUID().toString(),
                farmerName = currentState.farmerName.trim(),
                farmerId = currentState.farmerId.trim(),
                phoneNumber = currentState.phoneNumber.trim(),
                cropType = currentState.cropType,
                gpsCoordinates = location.location,
                gpsAccuracy = location.accuracy,
                registeredAt = Instant.now()
            )

            farmRepository.registerFarm(farm)
                .onSuccess {
                    _uiState.update {
                        it.copy(
                            isRegistering = false,
                            registrationSuccess = true,
                            error = null
                        )
                    }
                }
                .onFailure { exception ->
                    _uiState.update {
                        it.copy(
                            isRegistering = false,
                            error = "Failed to register farm: ${exception.message}"
                        )
                    }
                }
        }
    }

    private fun validateForm(): Boolean {
        val errors = mutableMapOf<String, String>()
        val currentState = _uiState.value

        if (currentState.farmerName.isBlank()) {
            errors["farmerName"] = "Farmer name is required"
        }

        if (currentState.farmerId.isBlank()) {
            errors["farmerId"] = "Farmer ID is required"
        }

        if (currentState.phoneNumber.isBlank()) {
            errors["phoneNumber"] = "Phone number is required"
        } else if (!isValidPhoneNumber(currentState.phoneNumber)) {
            errors["phoneNumber"] = "Invalid phone number format"
        }

        if (currentState.location == null) {
            errors["location"] = "GPS location is required"
        }

        _uiState.update { it.copy(validationErrors = errors) }
        return errors.isEmpty()
    }

    private fun isValidPhoneNumber(phone: String): Boolean {
        // Basic validation for Kenyan phone numbers
        val cleaned = phone.replace(Regex("[^0-9+]"), "")
        return cleaned.length >= 10
    }

    private fun clearValidationError(field: String) {
        _uiState.update {
            it.copy(validationErrors = it.validationErrors - field)
        }
    }

    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }

    fun resetForm() {
        _uiState.value = FarmRegistrationUiState()
    }
}
