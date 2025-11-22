package com.mavunosure.app.data.repository

import android.content.Context
import com.mavunosure.app.data.local.EncryptionManager
import com.mavunosure.app.data.local.ImageCompressor
import com.mavunosure.app.data.local.dao.ClaimDao
import com.mavunosure.app.data.local.entity.ClaimEntity
import com.mavunosure.app.data.remote.ClaimApi
import com.mavunosure.app.domain.model.*
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.junit.MockitoJUnitRunner
import org.mockito.kotlin.any
import org.mockito.kotlin.whenever
import java.time.Instant

@RunWith(MockitoJUnitRunner::class)
class OfflineQueueRepositoryTest {
    
    @Mock
    private lateinit var claimDao: ClaimDao
    
    @Mock
    private lateinit var claimApi: ClaimApi
    
    @Mock
    private lateinit var encryptionManager: EncryptionManager
    
    @Mock
    private lateinit var imageCompressor: ImageCompressor
    
    @Mock
    private lateinit var context: Context
    
    private lateinit var repository: OfflineQueueRepositoryImpl
    
    @Before
    fun setup() {
        repository = OfflineQueueRepositoryImpl(
            claimDao,
            claimApi,
            encryptionManager,
            imageCompressor,
            context
        )
    }
    
    @Test
    fun `getPendingClaims returns list of pending claims`() = runTest {
        // Given
        val pendingClaims = listOf(
            createMockClaimEntity("claim1", SyncStatus.PENDING),
            createMockClaimEntity("claim2", SyncStatus.FAILED)
        )
        whenever(claimDao.getPendingClaims()).thenReturn(pendingClaims)
        
        // When
        val result = repository.getPendingClaims()
        
        // Then
        assertEquals(2, result.size)
        assertEquals("claim1", result[0].claimId)
        assertEquals("claim2", result[1].claimId)
    }
    
    @Test
    fun `markSynced updates claim status to SYNCED`() = runTest {
        // Given
        val claimId = "claim1"
        val claimEntity = createMockClaimEntity(claimId, SyncStatus.SYNCING)
        whenever(claimDao.getClaimById(claimId)).thenReturn(claimEntity)
        
        // When
        val result = repository.markSynced(claimId)
        
        // Then
        assertTrue(result.isSuccess)
        verify(claimDao).updateSyncStatus(claimId, SyncStatus.SYNCED.name)
    }
    
    private fun createMockClaimEntity(claimId: String, status: SyncStatus): ClaimEntity {
        return ClaimEntity(
            claimId = claimId,
            agentId = "agent1",
            farmId = "farm1",
            farmGpsLatitude = -1.0,
            farmGpsLongitude = 36.0,
            timestamp = Instant.now().toEpochMilli(),
            mlClass = CropCondition.DROUGHT.name,
            mlConfidence = 0.9f,
            topThreeClassesJson = "[]",
            deviceTilt = 60f,
            deviceAzimuth = 180f,
            captureGpsLatitude = -1.0,
            captureGpsLongitude = 36.0,
            imageUri = "/path/to/image.jpg",
            syncStatus = status.name
        )
    }
}
