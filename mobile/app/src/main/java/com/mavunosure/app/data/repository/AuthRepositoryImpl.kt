package com.mavunosure.app.data.repository

import com.mavunosure.app.data.local.TokenManager
import com.mavunosure.app.data.remote.AuthApi
import com.mavunosure.app.data.remote.dto.RefreshTokenRequest
import com.mavunosure.app.data.remote.dto.SendOtpRequest
import com.mavunosure.app.data.remote.dto.VerifyOtpRequest
import com.mavunosure.app.domain.model.AuthToken
import com.mavunosure.app.domain.repository.AuthRepository
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val authApi: AuthApi,
    private val tokenManager: TokenManager
) : AuthRepository {

    override suspend fun sendOtp(phoneNumber: String): Result<String> {
        return try {
            val response = authApi.sendOtp(SendOtpRequest(phoneNumber))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.message)
            } else {
                Result.failure(Exception("Failed to send OTP: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun verifyOtp(phoneNumber: String, otp: String): Result<AuthToken> {
        return try {
            val response = authApi.verifyOtp(VerifyOtpRequest(phoneNumber, otp))
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                tokenManager.saveTokens(body.accessToken, body.refreshToken)
                Result.success(AuthToken(body.accessToken, body.refreshToken))
            } else {
                Result.failure(Exception("Failed to verify OTP: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun refreshToken(): Result<AuthToken> {
        return try {
            val currentRefreshToken = tokenManager.getRefreshToken()
                ?: return Result.failure(Exception("No refresh token available"))

            val response = authApi.refreshToken(RefreshTokenRequest(currentRefreshToken))
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                tokenManager.saveTokens(body.accessToken, body.refreshToken)
                Result.success(AuthToken(body.accessToken, body.refreshToken))
            } else {
                Result.failure(Exception("Failed to refresh token: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override fun isSessionValid(): Boolean {
        val accessToken = tokenManager.getAccessToken()
        val lastLoginTime = tokenManager.getLastLoginTime()
        
        if (accessToken == null || lastLoginTime == 0L) {
            return false
        }

        // Check if session is within 7-day offline grace period
        val currentTime = Instant.now().epochSecond
        val daysSinceLogin = (currentTime - lastLoginTime) / (24 * 60 * 60)
        
        return daysSinceLogin < 7
    }
}
