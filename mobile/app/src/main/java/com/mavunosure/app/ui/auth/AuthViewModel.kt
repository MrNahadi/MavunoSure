package com.mavunosure.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mavunosure.app.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.Initial)
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    private val _phoneNumber = MutableStateFlow("")
    val phoneNumber: StateFlow<String> = _phoneNumber.asStateFlow()

    private val _otp = MutableStateFlow("")
    val otp: StateFlow<String> = _otp.asStateFlow()

    fun updatePhoneNumber(phone: String) {
        _phoneNumber.value = phone
    }

    fun updateOtp(otpValue: String) {
        _otp.value = otpValue
    }

    fun sendOtp() {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            val result = authRepository.sendOtp(_phoneNumber.value)
            _uiState.value = if (result.isSuccess) {
                AuthUiState.OtpSent
            } else {
                AuthUiState.Error(result.exceptionOrNull()?.message ?: "Failed to send OTP")
            }
        }
    }

    fun verifyOtp() {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            val result = authRepository.verifyOtp(_phoneNumber.value, _otp.value)
            _uiState.value = if (result.isSuccess) {
                AuthUiState.Authenticated
            } else {
                AuthUiState.Error(result.exceptionOrNull()?.message ?: "Failed to verify OTP")
            }
        }
    }

    fun resetError() {
        if (_uiState.value is AuthUiState.Error) {
            _uiState.value = AuthUiState.Initial
        }
    }

    fun checkSession(): Boolean {
        return authRepository.isSessionValid()
    }
}

sealed class AuthUiState {
    object Initial : AuthUiState()
    object Loading : AuthUiState()
    object OtpSent : AuthUiState()
    object Authenticated : AuthUiState()
    data class Error(val message: String) : AuthUiState()
}
