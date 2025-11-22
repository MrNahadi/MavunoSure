package com.mavunosure.app.domain.repository

import com.mavunosure.app.domain.model.ClaimPacket
import kotlinx.coroutines.flow.Flow

interface OfflineQueueRepository {
    
    /**
     * Enqueues a claim for offline storage with encryption
     */
    suspend fun enqueueClaim(claim: ClaimPacket): Result<Unit>
    
    /**
     * Gets all pending claims that need to be synced
     */
    suspend fun getPendingClaims(): List<ClaimPacket>
    
    /**
     * Syncs a specific claim to the backend
     */
    suspend fun syncClaim(claimId: String): Result<Unit>
    
    /**
     * Marks a claim as successfully synced
     */
    suspend fun markSynced(claimId: String): Result<Unit>
    
    /**
     * Observes all claims
     */
    fun observeAllClaims(): Flow<List<ClaimPacket>>
}
