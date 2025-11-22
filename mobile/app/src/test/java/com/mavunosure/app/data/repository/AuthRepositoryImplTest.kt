package com.mavunosure.app.data.repository

import com.mavunosure.app.data.local.TokenManager
import com.mavunosure.app.data.remote.AuthApi
import com.mavunosure.app.data.remote.dto.*
import kotlinx.coroutines.test.runTest
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.MockitoAnnotations
import retrofit2.Response
import java.time.Instant

class AuthRepositoryImplTest {

    @Mock
    private lateinit var authApi: AuthApi

    @Mock
    private lateinit var tokenManager: TokenManager

    private lateinit var authRepository: AuthRepositoryImpl

    @Before
    fun setup() {
        MockitoAnnotations.openMocks(this)
        authRepository = AuthRepositoryImpl(authApi, tokenManager)
    }

    @Test
    fun `sendOtp returns success when API call succeeds`() = runTest {
        val phoneNumber = "0712345678"
        val response = SendOtpResponse("OTP sent successfully")
        `when`(authApi.sendOtp(SendOtpRequest(phoneNumber)))
            .thenReturn(Response.success(response))

        val result = authRepository.sendOtp(phoneNumber)

        assertTrue(result.isSuccess)
        assertEquals("OTP sent successfully", result.getOrNull())
        verify(authApi).sendOtp(SendOtpRequest(phoneNumber))
    }

    @Test
    fun `sendOtp returns failure when API call fails`() = runTest {
        val phoneNumber = "0712345678"
        `when`(authApi.sendOtp(SendOtpRequest(phoneNumber)))
            .thenReturn(Response.error(400, "".toResponseBody()))

        val result = authRepository.sendOtp(phoneNumber)

        assertTrue(result.isFailure)
        verify(authApi).sendOtp(SendOtpRequest(phoneNumber))
    }

    @Test
    fun `verifyOtp returns success and saves tokens when API call succeeds`() = runTest {
        val phoneNumber = "0712345678"
        val otp = "123456"
        val response = VerifyOtpResponse(
            accessToken = "access_token_123",
            refreshToken = "refresh_token_123",
            tokenType = "Bearer"
        )
        `when`(authApi.verifyOtp(VerifyOtpRequest(phoneNumber, otp)))
            .thenReturn(Response.success(response))

        val result = authRepository.verifyOtp(phoneNumber, otp)

        assertTrue(result.isSuccess)
        val authToken = result.getOrNull()
        assertNotNull(authToken)
        assertEquals("access_token_123", authToken?.accessToken)
        assertEquals("refresh_token_123", authToken?.refreshToken)
        verify(tokenManager).saveTokens("access_token_123", "refresh_token_123")
    }

    @Test
    fun `verifyOtp returns failure when API call fails`() = runTest {
        val phoneNumber = "0712345678"
        val otp = "123456"
        `when`(authApi.verifyOtp(VerifyOtpRequest(phoneNumber, otp)))
            .thenReturn(Response.error(401, "".toResponseBody()))

        val result = authRepository.verifyOtp(phoneNumber, otp)

        assertTrue(result.isFailure)
        verify(tokenManager, never()).saveTokens(anyString(), anyString())
    }

    @Test
    fun `refreshToken returns success when API call succeeds`() = runTest {
        val oldRefreshToken = "old_refresh_token"
        val response = RefreshTokenResponse(
            accessToken = "new_access_token",
            refreshToken = "new_refresh_token",
            tokenType = "Bearer"
        )
        `when`(tokenManager.getRefreshToken()).thenReturn(oldRefreshToken)
        `when`(authApi.refreshToken(RefreshTokenRequest(oldRefreshToken)))
            .thenReturn(Response.success(response))

        val result = authRepository.refreshToken()

        assertTrue(result.isSuccess)
        verify(tokenManager).saveTokens("new_access_token", "new_refresh_token")
    }

    @Test
    fun `refreshToken returns failure when no refresh token available`() = runTest {
        `when`(tokenManager.getRefreshToken()).thenReturn(null)

        val result = authRepository.refreshToken()

        assertTrue(result.isFailure)
        verify(authApi, never()).refreshToken(any())
    }

    @Test
    fun `isSessionValid returns true when session is within 7 days`() {
        val currentTime = Instant.now().epochSecond
        val loginTime = currentTime - (3 * 24 * 60 * 60) // 3 days ago
        `when`(tokenManager.getAccessToken()).thenReturn("valid_token")
        `when`(tokenManager.getLastLoginTime()).thenReturn(loginTime)

        val result = authRepository.isSessionValid()

        assertTrue(result)
    }

    @Test
    fun `isSessionValid returns false when session is older than 7 days`() {
        val currentTime = Instant.now().epochSecond
        val loginTime = currentTime - (8 * 24 * 60 * 60) // 8 days ago
        `when`(tokenManager.getAccessToken()).thenReturn("valid_token")
        `when`(tokenManager.getLastLoginTime()).thenReturn(loginTime)

        val result = authRepository.isSessionValid()

        assertFalse(result)
    }

    @Test
    fun `isSessionValid returns false when no access token`() {
        `when`(tokenManager.getAccessToken()).thenReturn(null)
        `when`(tokenManager.getLastLoginTime()).thenReturn(Instant.now().epochSecond)

        val result = authRepository.isSessionValid()

        assertFalse(result)
    }
}
