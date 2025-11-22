package com.mavunosure.app.domain.camera

import com.mavunosure.app.domain.model.CameraValidation
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class AntiFraudValidatorTest {

    private lateinit var validator: AntiFraudValidator

    @Before
    fun setup() {
        validator = AntiFraudValidator()
    }

    @Test
    fun `validateTilt returns true when tilt is 45 degrees or more`() {
        val (isValid, _) = validator.validateTilt(45f)
        assertTrue(isValid)
    }

    @Test
    fun `validateTilt returns true when tilt is greater than 45 degrees`() {
        val (isValid, _) = validator.validateTilt(60f)
        assertTrue(isValid)
    }

    @Test
    fun `validateTilt returns false when tilt is less than 45 degrees`() {
        val (isValid, message) = validator.validateTilt(30f)
        assertFalse(isValid)
        assertTrue(message.contains("45°"))
    }

    @Test
    fun `validateGpsProximity returns true when within 50 meters`() {
        // Same location
        val (isValid, _) = validator.validateGpsProximity(
            currentLat = -1.2921,
            currentLng = 36.8219,
            farmLat = -1.2921,
            farmLng = 36.8219
        )
        assertTrue(isValid)
    }

    @Test
    fun `validateGpsProximity returns false when beyond 50 meters`() {
        // Approximately 100m apart
        val (isValid, message) = validator.validateGpsProximity(
            currentLat = -1.2921,
            currentLng = 36.8219,
            farmLat = -1.2930,
            farmLng = 36.8219
        )
        assertFalse(isValid)
        assertTrue(message.contains("50m"))
    }

    @Test
    fun `validate returns valid when both tilt and GPS are valid`() {
        val validation = validator.validate(
            tiltAngle = 50f,
            currentLat = -1.2921,
            currentLng = 36.8219,
            farmLat = -1.2921,
            farmLng = 36.8219
        )
        
        assertTrue(validation.isValid)
        assertTrue(validation.isTiltValid)
        assertTrue(validation.isGpsValid)
        assertEquals("Ready to capture", validation.message)
    }

    @Test
    fun `validate returns invalid when tilt is invalid`() {
        val validation = validator.validate(
            tiltAngle = 30f,
            currentLat = -1.2921,
            currentLng = 36.8219,
            farmLat = -1.2921,
            farmLng = 36.8219
        )
        
        assertFalse(validation.isValid)
        assertFalse(validation.isTiltValid)
        assertTrue(validation.isGpsValid)
    }

    @Test
    fun `validate returns invalid when GPS is invalid`() {
        val validation = validator.validate(
            tiltAngle = 50f,
            currentLat = -1.2921,
            currentLng = 36.8219,
            farmLat = -1.3000,
            farmLng = 36.8219
        )
        
        assertFalse(validation.isValid)
        assertTrue(validation.isTiltValid)
        assertFalse(validation.isGpsValid)
    }

    @Test
    fun `validate returns invalid when both tilt and GPS are invalid`() {
        val validation = validator.validate(
            tiltAngle = 20f,
            currentLat = -1.2921,
            currentLng = 36.8219,
            farmLat = -1.3000,
            farmLng = 36.8219
        )
        
        assertFalse(validation.isValid)
        assertFalse(validation.isTiltValid)
        assertFalse(validation.isGpsValid)
    }

    @Test
    fun `haversine distance calculation is accurate`() {
        // Test known distance: Nairobi to approximately 100m north
        val validation = validator.validate(
            tiltAngle = 50f,
            currentLat = -1.2921,
            currentLng = 36.8219,
            farmLat = -1.2930,
            farmLng = 36.8219
        )
        
        // Distance should be approximately 100 meters
        assertTrue(validation.distanceFromFarm > 90f)
        assertTrue(validation.distanceFromFarm < 110f)
    }
}
