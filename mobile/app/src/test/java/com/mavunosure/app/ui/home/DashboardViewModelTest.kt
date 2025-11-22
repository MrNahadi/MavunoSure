package com.mavunosure.app.ui.home

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.mavunosure.app.domain.model.*
import com.mavunosure.app.domain.repository.ClaimRepository
import com.mavunosure.app.domain.repository.OfflineQueueRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.*
import java.time.Instant

@OptIn(ExperimentalCoroutinesApi::class)
class DashboardViewModelTest {

    @get:Rule
    val instantTaskExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = StandardTestDispatcher()

    private lateinit var claimRepository: ClaimRepository
    private lateinit var offlineQueueRepository: OfflineQueueRepository
    private lateinit var viewModel: DashboardViewModel

    private val testClaims = listOf(
        createTestClaim("claim1", ClaimStatus.PENDING, Instant.now().minusSeconds(100)),
        createTestClaim("claim2", ClaimStatus.AUTO_APPROVED, Instant.now().minusSeconds(200)),
        createTestClaim("claim3", ClaimStatus.REJECTED, Instant.now().minusSeconds(300)),
        createTestClaim("claim4", ClaimStatus.PAID, Instant.now().minusSeconds(400)),
        createTestClaim("claim5", ClaimStatus.FLAGGED_FOR_REVIEW, Instant.now().minusSeconds(500))
    )

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        claimRepository = mock()
        offlineQueueRepository = mock()
        
        // Default mock behavior
        whenever(claimRepository.observeAllClaims()).thenReturn(flowOf(testClaims))
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `initial state is Loading`() {
        // Act
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)

        // Assert
        assertTrue(viewModel.uiState.value is DashboardUiState.Loading)
    }

    @Test
    fun `loadClaims with data shows Success state`() = runTest {
        // Act
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertTrue(state is DashboardUiState.Success)
        assertEquals(5, (state as DashboardUiState.Success).claims.size)
    }

    @Test
    fun `loadClaims with empty data shows Empty state`() = runTest {
        // Arrange
        whenever(claimRepository.observeAllClaims()).thenReturn(flowOf(emptyList()))

        // Act
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Assert
        assertTrue(viewModel.uiState.value is DashboardUiState.Empty)
    }

    @Test
    fun `loadClaims with error shows Error state`() = runTest {
        // Arrange
        whenever(claimRepository.observeAllClaims()).thenThrow(RuntimeException("Database error"))

        // Act
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertTrue(state is DashboardUiState.Error)
        assertEquals("Database error", (state as DashboardUiState.Error).message)
    }

    @Test
    fun `filter ALL shows all claims sorted by timestamp descending`() = runTest {
        // Arrange
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.setFilter(StatusFilter.ALL)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value as DashboardUiState.Success
        assertEquals(5, state.claims.size)
        // Verify sorted by timestamp descending (most recent first)
        assertEquals("claim1", state.claims[0].claimId)
        assertEquals("claim5", state.claims[4].claimId)
    }

    @Test
    fun `filter PENDING shows only pending and flagged claims`() = runTest {
        // Arrange
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.setFilter(StatusFilter.PENDING)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value as DashboardUiState.Success
        assertEquals(2, state.claims.size)
        assertTrue(state.claims.all { 
            it.claimStatus == ClaimStatus.PENDING || 
            it.claimStatus == ClaimStatus.FLAGGED_FOR_REVIEW 
        })
    }

    @Test
    fun `filter APPROVED shows only approved claims`() = runTest {
        // Arrange
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.setFilter(StatusFilter.APPROVED)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value as DashboardUiState.Success
        assertEquals(1, state.claims.size)
        assertEquals(ClaimStatus.AUTO_APPROVED, state.claims[0].claimStatus)
    }

    @Test
    fun `filter REJECTED shows only rejected claims`() = runTest {
        // Arrange
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.setFilter(StatusFilter.REJECTED)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value as DashboardUiState.Success
        assertEquals(1, state.claims.size)
        assertEquals(ClaimStatus.REJECTED, state.claims[0].claimStatus)
    }

    @Test
    fun `filter PAID shows only paid claims`() = runTest {
        // Arrange
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.setFilter(StatusFilter.PAID)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value as DashboardUiState.Success
        assertEquals(1, state.claims.size)
        assertEquals(ClaimStatus.PAID, state.claims[0].claimStatus)
    }

    @Test
    fun `filter with no matching claims shows Empty state`() = runTest {
        // Arrange
        val claimsWithoutPaid = testClaims.filter { it.claimStatus != ClaimStatus.PAID }
        whenever(claimRepository.observeAllClaims()).thenReturn(flowOf(claimsWithoutPaid))
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.setFilter(StatusFilter.PAID)
        advanceUntilIdle()

        // Assert
        assertTrue(viewModel.uiState.value is DashboardUiState.Empty)
    }

    @Test
    fun `refreshClaims syncs from backend and offline queue`() = runTest {
        // Arrange
        val pendingClaims = listOf(
            createTestClaim("pending1", ClaimStatus.PENDING, Instant.now())
        )
        whenever(offlineQueueRepository.getPendingClaims()).thenReturn(pendingClaims)
        whenever(claimRepository.syncClaimsFromBackend()).thenReturn(Result.success(Unit))
        whenever(offlineQueueRepository.syncClaim(any())).thenReturn(Result.success(Unit))
        
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.refreshClaims()
        advanceUntilIdle()

        // Assert
        verify(claimRepository).syncClaimsFromBackend()
        verify(offlineQueueRepository).getPendingClaims()
        verify(offlineQueueRepository).syncClaim("pending1")
        assertFalse(viewModel.isRefreshing.value)
    }

    @Test
    fun `refreshClaims sets isRefreshing to true during sync`() = runTest {
        // Arrange
        whenever(offlineQueueRepository.getPendingClaims()).thenReturn(emptyList())
        whenever(claimRepository.syncClaimsFromBackend()).thenReturn(Result.success(Unit))
        
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.refreshClaims()

        // Assert - check before advanceUntilIdle
        assertTrue(viewModel.isRefreshing.value)
        
        advanceUntilIdle()
        assertFalse(viewModel.isRefreshing.value)
    }

    @Test
    fun `refreshClaims handles sync errors gracefully`() = runTest {
        // Arrange
        whenever(offlineQueueRepository.getPendingClaims()).thenReturn(emptyList())
        whenever(claimRepository.syncClaimsFromBackend())
            .thenReturn(Result.failure(Exception("Network error")))
        
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.refreshClaims()
        advanceUntilIdle()

        // Assert - should not crash and should reset refreshing state
        assertFalse(viewModel.isRefreshing.value)
    }

    @Test
    fun `selectedFilter initial value is ALL`() {
        // Act
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)

        // Assert
        assertEquals(StatusFilter.ALL, viewModel.selectedFilter.value)
    }

    @Test
    fun `setFilter updates selectedFilter state`() = runTest {
        // Arrange
        viewModel = DashboardViewModel(claimRepository, offlineQueueRepository)
        advanceUntilIdle()

        // Act
        viewModel.setFilter(StatusFilter.APPROVED)

        // Assert
        assertEquals(StatusFilter.APPROVED, viewModel.selectedFilter.value)
    }

    private fun createTestClaim(
        id: String,
        status: ClaimStatus,
        timestamp: Instant
    ): ClaimPacket {
        return ClaimPacket(
            claimId = id,
            agentId = "agent1",
            farmId = "farm1",
            farmGps = GeoPoint(-1.2921, 36.8219),
            timestamp = timestamp,
            groundTruth = GroundTruthData(
                mlClass = CropCondition.DROUGHT_STRESS,
                mlConfidence = 0.85f,
                topThreeClasses = listOf(
                    CropCondition.DROUGHT_STRESS to 0.85f,
                    CropCondition.HEALTHY to 0.10f,
                    CropCondition.OTHER to 0.05f
                ),
                deviceTilt = 60f,
                deviceAzimuth = 180f,
                captureGps = GeoPoint(-1.2921, 36.8219)
            ),
            imageUri = "file:///test.jpg",
            syncStatus = SyncStatus.SYNCED,
            claimStatus = status
        )
    }
}
