package com.mavunosure.app.ui.auth

import androidx.compose.runtime.*
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun AuthScreen(
    onAuthSuccess: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val phoneNumber by viewModel.phoneNumber.collectAsState()
    val otp by viewModel.otp.collectAsState()

    LaunchedEffect(uiState) {
        if (uiState is AuthUiState.Authenticated) {
            onAuthSuccess()
        }
    }

    when (uiState) {
        is AuthUiState.Initial, is AuthUiState.Loading, is AuthUiState.Error -> {
            PhoneNumberScreen(
                phoneNumber = phoneNumber,
                onPhoneNumberChange = viewModel::updatePhoneNumber,
                onSendOtp = viewModel::sendOtp,
                isLoading = uiState is AuthUiState.Loading,
                errorMessage = (uiState as? AuthUiState.Error)?.message,
                onErrorDismiss = viewModel::resetError
            )
        }
        is AuthUiState.OtpSent -> {
            OtpScreen(
                phoneNumber = phoneNumber,
                otp = otp,
                onOtpChange = viewModel::updateOtp,
                onVerifyOtp = viewModel::verifyOtp,
                onResendOtp = viewModel::sendOtp,
                isLoading = uiState is AuthUiState.Loading,
                errorMessage = (uiState as? AuthUiState.Error)?.message,
                onErrorDismiss = viewModel::resetError
            )
        }
        is AuthUiState.Authenticated -> {
            // Navigation handled by LaunchedEffect
        }
    }
}
