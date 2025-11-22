package com.mavunosure.app.ui.farm

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.mavunosure.app.domain.location.LocationAccuracyStatus
import com.mavunosure.app.domain.location.LocationManager
import com.mavunosure.app.domain.location.LocationResult
import com.mavunosure.app.domain.model.CropType
import com.mavunosure.app.domain.model.Farm
import com.mavunosure.app.domain.model.GeoPoint
import com.mavunosure.app.domain.repository.FarmRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.*

@OptIn(ExperimentalCoroutinesApi::class)
class FarmRegistrationViewModelTest {

    @get:Rule
    val instantTaskExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = StandardTestDispatcher()

    private lateinit var farmRepository: FarmRepository
    private lateinit var locationManager: LocationManager
    private lateinit var viewModel: FarmRegistrationViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        farmRepository = mock()
        locationManager = mock()
        viewModel = FarmRegistrationViewModel(farmRepository, locationManager)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `updateFarmerName updates state correctly`() = runTest {
        // Act
        viewModel.updateFarmerName("John Doe")
        advanceUntilIdle()

        // Assert
        assertEquals("John Doe", viewModel.uiState.value.farmerName)
    }

    @Test
    fun `updateFarmerId updates state correctly`() = runTest {
        // Act
        viewModel.updateFarmerId("12345678")
        advanceUntilIdle()

        // Assert
        assertEquals("12345678", viewModel.uiState.value.farmerId)
    }

    @Test
    fun `updatePhoneNumber updates state correctly`() = runTest {
        // Act
        viewModel.updatePhoneNumber("+254712345678")
        advanceUntilIdle()

        // Assert
        assertEquals("+254712345678", viewModel.uiState.value.phoneNumber)
    }

    @Test
    fun `captureLocation success updates state with location`() = runTest {
        // Arrange
        val mockLocation = LocationResult(
            location = GeoPoint(-1.2921, 36.8219),
            accuracy = 8f,
            timestamp = System.currentTimeMillis()
        )
        whenever(locationManager.isLocationEnabled()).thenReturn(true)
        whenever(locationManager.getCurrentLocation()).thenReturn(Result.success(mockLocation))
        whenever(locationManager.getAccuracyStatus(8f)).thenReturn(LocationAccuracyStatus.Ideal)

        // Act
        viewModel.captureLocation()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertNotNull(state.location)
        assertEquals(mockLocation, state.location)
        assertTrue(state.accuracyStatus is LocationAccuracyStatus.Ideal)
        assertFalse(state.isCapturingLocation)
        assertNull(state.error)
    }

    @Test
    fun `captureLocation with disabled location services shows error`() = runTest {
        // Arrange
        whenever(locationManager.isLocationEnabled()).thenReturn(false)

        // Act
        viewModel.captureLocation()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertNull(state.location)
        assertFalse(state.isCapturingLocation)
        assertEquals("Location services are disabled. Please enable GPS.", state.error)
    }

    @Test
    fun `captureLocation failure shows error`() = runTest {
        // Arrange
        whenever(locationManager.isLocationEnabled()).thenReturn(true)
        whenever(locationManager.getCurrentLocation())
            .thenReturn(Result.failure(Exception("GPS timeout")))

        // Act
        viewModel.captureLocation()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertNull(state.location)
        assertFalse(state.isCapturingLocation)
        assertTrue(state.error?.contains("GPS timeout") == true)
    }

    @Test
    fun `registerFarm with valid data succeeds`() = runTest {
        // Arrange
        val mockLocation = LocationResult(
            location = GeoPoint(-1.2921, 36.8219),
            accuracy = 8f,
            timestamp = System.currentTimeMillis()
        )
        val mockFarm = Farm(
            id = "test-id",
            farmerName = "John Doe",
            farmerId = "12345678",
            phoneNumber = "+254712345678",
            cropType = CropType.MAIZE,
            gpsCoordinates = mockLocation.location,
            gpsAccuracy = mockLocation.accuracy,
            registeredAt = java.time.Instant.now()
        )

        whenever(farmRepository.registerFarm(any())).thenReturn(Result.success(mockFarm))

        viewModel.updateFarmerName("John Doe")
        viewModel.updateFarmerId("12345678")
        viewModel.updatePhoneNumber("+254712345678")
        
        // Simulate location capture
        whenever(locationManager.isLocationEnabled()).thenReturn(true)
        whenever(locationManager.getCurrentLocation()).thenReturn(Result.success(mockLocation))
        whenever(locationManager.getAccuracyStatus(8f)).thenReturn(LocationAccuracyStatus.Ideal)
        viewModel.captureLocation()
        advanceUntilIdle()

        // Act
        viewModel.registerFarm()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertTrue(state.registrationSuccess)
        assertFalse(state.isRegistering)
        assertNull(state.error)
        verify(farmRepository).registerFarm(any())
    }

    @Test
    fun `registerFarm without location shows validation error`() = runTest {
        // Arrange
        viewModel.updateFarmerName("John Doe")
        viewModel.updateFarmerId("12345678")
        viewModel.updatePhoneNumber("+254712345678")

        // Act
        viewModel.registerFarm()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertFalse(state.registrationSuccess)
        assertTrue(state.validationErrors.containsKey("location"))
        verifyNoInteractions(farmRepository)
    }

    @Test
    fun `registerFarm with empty fields shows validation errors`() = runTest {
        // Act
        viewModel.registerFarm()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertFalse(state.registrationSuccess)
        assertTrue(state.validationErrors.containsKey("farmerName"))
        assertTrue(state.validationErrors.containsKey("farmerId"))
        assertTrue(state.validationErrors.containsKey("phoneNumber"))
        assertTrue(state.validationErrors.containsKey("location"))
        verifyNoInteractions(farmRepository)
    }

    @Test
    fun `registerFarm with invalid phone number shows validation error`() = runTest {
        // Arrange
        viewModel.updateFarmerName("John Doe")
        viewModel.updateFarmerId("12345678")
        viewModel.updatePhoneNumber("123") // Too short

        // Act
        viewModel.registerFarm()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertTrue(state.validationErrors.containsKey("phoneNumber"))
        assertEquals("Invalid phone number format", state.validationErrors["phoneNumber"])
    }

    @Test
    fun `registerFarm failure shows error message`() = runTest {
        // Arrange
        val mockLocation = LocationResult(
            location = GeoPoint(-1.2921, 36.8219),
            accuracy = 8f,
            timestamp = System.currentTimeMillis()
        )

        whenever(farmRepository.registerFarm(any()))
            .thenReturn(Result.failure(Exception("Network error")))

        viewModel.updateFarmerName("John Doe")
        viewModel.updateFarmerId("12345678")
        viewModel.updatePhoneNumber("+254712345678")
        
        whenever(locationManager.isLocationEnabled()).thenReturn(true)
        whenever(locationManager.getCurrentLocation()).thenReturn(Result.success(mockLocation))
        whenever(locationManager.getAccuracyStatus(8f)).thenReturn(LocationAccuracyStatus.Ideal)
        viewModel.captureLocation()
        advanceUntilIdle()

        // Act
        viewModel.registerFarm()
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertFalse(state.registrationSuccess)
        assertFalse(state.isRegistering)
        assertTrue(state.error?.contains("Network error") == true)
    }
}
