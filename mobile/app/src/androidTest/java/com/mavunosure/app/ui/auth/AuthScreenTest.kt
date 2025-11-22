package com.mavunosure.app.ui.auth

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.mavunosure.app.ui.theme.MavunoSureTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AuthScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun phoneNumberScreen_displaysCorrectly() {
        composeTestRule.setContent {
            MavunoSureTheme {
                PhoneNumberScreen(
                    phoneNumber = "",
                    onPhoneNumberChange = {},
                    onSendOtp = {},
                    isLoading = false,
                    errorMessage = null,
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("MavunoSure").assertIsDisplayed()
        composeTestRule.onNodeWithText("Enter your phone number").assertIsDisplayed()
        composeTestRule.onNodeWithText("Send OTP").assertIsDisplayed()
    }

    @Test
    fun phoneNumberScreen_sendButtonDisabledWhenPhoneInvalid() {
        composeTestRule.setContent {
            MavunoSureTheme {
                PhoneNumberScreen(
                    phoneNumber = "123",
                    onPhoneNumberChange = {},
                    onSendOtp = {},
                    isLoading = false,
                    errorMessage = null,
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Send OTP").assertIsNotEnabled()
    }

    @Test
    fun phoneNumberScreen_sendButtonEnabledWhenPhoneValid() {
        composeTestRule.setContent {
            MavunoSureTheme {
                PhoneNumberScreen(
                    phoneNumber = "0712345678",
                    onPhoneNumberChange = {},
                    onSendOtp = {},
                    isLoading = false,
                    errorMessage = null,
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Send OTP").assertIsEnabled()
    }

    @Test
    fun phoneNumberScreen_showsLoadingState() {
        composeTestRule.setContent {
            MavunoSureTheme {
                PhoneNumberScreen(
                    phoneNumber = "0712345678",
                    onPhoneNumberChange = {},
                    onSendOtp = {},
                    isLoading = true,
                    errorMessage = null,
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Send OTP").assertIsNotEnabled()
    }

    @Test
    fun phoneNumberScreen_displaysErrorMessage() {
        composeTestRule.setContent {
            MavunoSureTheme {
                PhoneNumberScreen(
                    phoneNumber = "0712345678",
                    onPhoneNumberChange = {},
                    onSendOtp = {},
                    isLoading = false,
                    errorMessage = "Failed to send OTP",
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Failed to send OTP").assertIsDisplayed()
    }

    @Test
    fun otpScreen_displaysCorrectly() {
        composeTestRule.setContent {
            MavunoSureTheme {
                OtpScreen(
                    phoneNumber = "0712345678",
                    otp = "",
                    onOtpChange = {},
                    onVerifyOtp = {},
                    onResendOtp = {},
                    isLoading = false,
                    errorMessage = null,
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Verify OTP").assertIsDisplayed()
        composeTestRule.onNodeWithText("0712345678").assertIsDisplayed()
        composeTestRule.onNodeWithText("Verify").assertIsDisplayed()
    }

    @Test
    fun otpScreen_verifyButtonDisabledWhenOtpInvalid() {
        composeTestRule.setContent {
            MavunoSureTheme {
                OtpScreen(
                    phoneNumber = "0712345678",
                    otp = "123",
                    onOtpChange = {},
                    onVerifyOtp = {},
                    onResendOtp = {},
                    isLoading = false,
                    errorMessage = null,
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Verify").assertIsNotEnabled()
    }

    @Test
    fun otpScreen_verifyButtonEnabledWhenOtpValid() {
        composeTestRule.setContent {
            MavunoSureTheme {
                OtpScreen(
                    phoneNumber = "0712345678",
                    otp = "123456",
                    onOtpChange = {},
                    onVerifyOtp = {},
                    onResendOtp = {},
                    isLoading = false,
                    errorMessage = null,
                    onErrorDismiss = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Verify").assertIsEnabled()
    }
}
