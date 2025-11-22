package com.mavunosure.app.data.remote.dto

import com.google.gson.annotations.SerializedName

data class SendOtpRequest(
    @SerializedName("phone_number")
    val phoneNumber: String
)

data class SendOtpResponse(
    val message: String
)

data class VerifyOtpRequest(
    @SerializedName("phone_number")
    val phoneNumber: String,
    val otp: String
)

data class VerifyOtpResponse(
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("refresh_token")
    val refreshToken: String,
    @SerializedName("token_type")
    val tokenType: String
)

data class RefreshTokenRequest(
    @SerializedName("refresh_token")
    val refreshToken: String
)

data class RefreshTokenResponse(
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("refresh_token")
    val refreshToken: String,
    @SerializedName("token_type")
    val tokenType: String
)
