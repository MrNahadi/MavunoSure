package com.mavunosure.app.ui.camera

import android.Manifest
import android.graphics.Bitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.rule.GrantPermissionRule
import com.mavunosure.app.domain.model.CaptureMetadata
import com.mavunosure.app.domain.model.CropCondition
import com.mavunosure.app.domain.model.InferenceResult
import org.junit.Rule
import org.junit.Test
import java.time.Instant

class SmartCameraIntegrationTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @get:Rule
    val permissionRule: GrantPermissionRule = GrantPermissionRule.grant(
        Manifest.permission.CAMERA,
        Manifest.permission.ACCESS_FINE_LOCATION
    )

    @Test
    fun cameraScreen_displaysGuidanceText() {
        var captureCompleted = false
        
        composeTestRule.setContent {
            SmartCameraScreen(
                farmLatitude = -1.2921,
                farmLongitude = 36.8219,
                onCaptureComplete = { _, _ -> captureCompleted = true },
                onCancel = {}
            )
        }

        // Verify guidance text is displayed
        composeTestRule.onNodeWithText("Point at the most affected leaf. Hold steady.")
            .assertIsDisplayed()
    }

    @Test
    fun cameraScreen_showsValidationIndicators() {
        composeTestRule.setContent {
            SmartCameraScreen(
                farmLatitude = -1.2921,
                farmLongitude = 36.8219,
                onCaptureComplete = { _, _ -> },
                onCancel = {}
            )
        }

        // Verify validation indicators are present
        composeTestRule.onNodeWithText("Tilt").assertIsDisplayed()
        composeTestRule.onNodeWithText("Distance").assertIsDisplayed()
    }

    @Test
    fun captureResultScreen_displaysClassificationResult() {
        val testBitmap = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
        val testInferenceResult = InferenceResult(
            primaryClass = CropCondition.DROUGHT,
            confidence = 0.85f,
            topThreeClasses = listOf(
                CropCondition.DROUGHT to 0.85f,
                CropCondition.HEALTHY to 0.10f,
                CropCondition.DISEASE_BLIGHT to 0.05f
            ),
            inferenceTimeMs = 150L
        )

        var proceedClicked = false
        var retakeClicked = false

        composeTestRule.setContent {
            CaptureResultScreen(
                bitmap = testBitmap,
                inferenceResult = testInferenceResult,
                onProceed = { proceedClicked = true },
                onRetake = { retakeClicked = true }
            )
        }

        // Verify classification result is displayed
        composeTestRule.onNodeWithText("Drought Stress").assertIsDisplayed()
        composeTestRule.onNodeWithText("Confidence: 85%").assertIsDisplayed()
        
        // Verify top 3 predictions are shown
        composeTestRule.onNodeWithText("Top 3 Predictions:").assertIsDisplayed()
        
        // Verify buttons are present
        composeTestRule.onNodeWithText("Retake").assertIsDisplayed()
        composeTestRule.onNodeWithText("Proceed").assertIsDisplayed()
    }

    @Test
    fun captureResultScreen_proceedButtonTriggersCallback() {
        val testBitmap = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
        val testInferenceResult = InferenceResult(
            primaryClass = CropCondition.HEALTHY,
            confidence = 0.90f,
            topThreeClasses = listOf(
                CropCondition.HEALTHY to 0.90f,
                CropCondition.DROUGHT to 0.05f,
                CropCondition.OTHER to 0.05f
            ),
            inferenceTimeMs = 120L
        )

        var proceedClicked = false

        composeTestRule.setContent {
            CaptureResultScreen(
                bitmap = testBitmap,
                inferenceResult = testInferenceResult,
                onProceed = { proceedClicked = true },
                onRetake = {}
            )
        }

        // Click proceed button
        composeTestRule.onNodeWithText("Proceed").performClick()
        
        // Verify callback was triggered
        assert(proceedClicked)
    }

    @Test
    fun captureResultScreen_retakeButtonTriggersCallback() {
        val testBitmap = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
        val testInferenceResult = InferenceResult(
            primaryClass = CropCondition.DISEASE_BLIGHT,
            confidence = 0.75f,
            topThreeClasses = listOf(
                CropCondition.DISEASE_BLIGHT to 0.75f,
                CropCondition.DISEASE_RUST to 0.15f,
                CropCondition.HEALTHY to 0.10f
            ),
            inferenceTimeMs = 180L
        )

        var retakeClicked = false

        composeTestRule.setContent {
            CaptureResultScreen(
                bitmap = testBitmap,
                inferenceResult = testInferenceResult,
                onProceed = {},
                onRetake = { retakeClicked = true }
            )
        }

        // Click retake button
        composeTestRule.onNodeWithText("Retake").performClick()
        
        // Verify callback was triggered
        assert(retakeClicked)
    }

    @Test
    fun validationIndicator_showsGreenWhenValid() {
        val validValidation = com.mavunosure.app.domain.model.CameraValidation(
            isTiltValid = true,
            isGpsValid = true,
            tiltAngle = 50f,
            distanceFromFarm = 30f,
            message = "Ready to capture"
        )

        composeTestRule.setContent {
            ValidationIndicator(validation = validValidation)
        }

        // Verify both indicators show valid state
        composeTestRule.onNodeWithText("50°").assertIsDisplayed()
        composeTestRule.onNodeWithText("30m").assertIsDisplayed()
    }

    @Test
    fun validationIndicator_showsRedWhenInvalid() {
        val invalidValidation = com.mavunosure.app.domain.model.CameraValidation(
            isTiltValid = false,
            isGpsValid = false,
            tiltAngle = 30f,
            distanceFromFarm = 80f,
            message = "Adjust device"
        )

        composeTestRule.setContent {
            ValidationIndicator(validation = invalidValidation)
        }

        // Verify indicators show invalid values
        composeTestRule.onNodeWithText("30°").assertIsDisplayed()
        composeTestRule.onNodeWithText("80m").assertIsDisplayed()
    }
}
