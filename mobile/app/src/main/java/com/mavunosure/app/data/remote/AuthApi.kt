package com.mavunosure.app.data.remote

import com.mavunosure.app.data.remote.dto.SendOtpRequest
import com.mavunosure.app.data.remote.dto.SendOtpResponse
import com.mavunosure.app.data.remote.dto.VerifyOtpRequest
import com.mavunosure.app.data.remote.dto.VerifyOtpResponse
import com.mavunosure.app.data.remote.dto.RefreshTokenRequest
import com.mavunosure.app.data.remote.dto.RefreshTokenResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApi {
    @POST("auth/send-otp")
    suspend fun sendOtp(@Body request: SendOtpRequest): Response<SendOtpResponse>

    @POST("auth/verify-otp")
    suspend fun verifyOtp(@Body request: VerifyOtpRequest): Response<VerifyOtpResponse>

    @POST("auth/refresh-token")
    suspend fun refreshToken(@Body request: RefreshTokenRequest): Response<RefreshTokenResponse>
}
