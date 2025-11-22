package com.mavunosure.app.domain.location

import org.junit.Assert.*
import org.junit.Test

class LocationManagerTest {

    @Test
    fun `getAccuracyStatus returns Ideal when accuracy is less than 10m`() {
        // Arrange
        val locationManager = TestLocationManager()
        val accuracy = 5f

        // Act
        val status = locationManager.getAccuracyStatus(accuracy)

        // Assert
        assertTrue(status is LocationAccuracyStatus.Ideal)
    }

    @Test
    fun `getAccuracyStatus returns Acceptable when accuracy is between 10m and 20m`() {
        // Arrange
        val locationManager = TestLocationManager()
        val accuracy = 15f

        // Act
        val status = locationManager.getAccuracyStatus(accuracy)

        // Assert
        assertTrue(status is LocationAccuracyStatus.Acceptable)
    }

    @Test
    fun `getAccuracyStatus returns Warning when accuracy is greater than 20m`() {
        // Arrange
        val locationManager = TestLocationManager()
        val accuracy = 25f

        // Act
        val status = locationManager.getAccuracyStatus(accuracy)

        // Assert
        assertTrue(status is LocationAccuracyStatus.Warning)
        assertEquals(25f, (status as LocationAccuracyStatus.Warning).accuracy)
    }

    @Test
    fun `getAccuracyStatus boundary test at 10m returns Acceptable`() {
        // Arrange
        val locationManager = TestLocationManager()
        val accuracy = 10f

        // Act
        val status = locationManager.getAccuracyStatus(accuracy)

        // Assert
        assertTrue(status is LocationAccuracyStatus.Acceptable)
    }

    @Test
    fun `getAccuracyStatus boundary test at 20m returns Warning`() {
        // Arrange
        val locationManager = TestLocationManager()
        val accuracy = 20f

        // Act
        val status = locationManager.getAccuracyStatus(accuracy)

        // Assert
        assertTrue(status is LocationAccuracyStatus.Warning)
    }

    // Test implementation of LocationManager for testing
    private class TestLocationManager : LocationManager {
        override suspend fun getCurrentLocation(): Result<LocationResult> {
            throw NotImplementedError()
        }

        override suspend fun getLastKnownLocation(): Result<LocationResult> {
            throw NotImplementedError()
        }

        override fun getAccuracyStatus(accuracy: Float): LocationAccuracyStatus {
            return when {
                accuracy < 10f -> LocationAccuracyStatus.Ideal
                accuracy < 20f -> LocationAccuracyStatus.Acceptable
                else -> LocationAccuracyStatus.Warning(accuracy)
            }
        }

        override fun isLocationEnabled(): Boolean {
            throw NotImplementedError()
        }
    }
}
