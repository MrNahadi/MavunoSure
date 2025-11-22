package com.mavunosure.app.domain.model

data class AuthToken(
    val accessToken: String,
    val refreshToken: String
)
