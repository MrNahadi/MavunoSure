package com.mavunosure.app.domain.repository

import com.mavunosure.app.domain.model.AuthToken

interface AuthRepository {
    suspend fun sendOtp(phoneNumber: String): Result<String>
    suspend fun verifyOtp(phoneNumber: String, otp: String): Result<AuthToken>
    suspend fun refreshToken(): Result<AuthToken>
    fun isSessionValid(): Boolean
}
