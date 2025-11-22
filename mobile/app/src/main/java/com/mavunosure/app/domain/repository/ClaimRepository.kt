package com.mavunosure.app.domain.repository

import com.mavunosure.app.domain.model.ClaimPacket
import com.mavunosure.app.domain.model.ClaimStatus
import kotlinx.coroutines.flow.Flow

/**
 * Repository for managing claims list and syncing with backend
 */
interface ClaimRepository {
    
    /**
     * Observes all claims from local database, sorted by created_at descending
     */
    fun observeAllClaims(): Flow<List<ClaimPacket>>
    
    /**
     * Gets all claims from local database, sorted by created_at descending
     */
    suspend fun getAllClaims(): List<ClaimPacket>
    
    /**
     * Gets claims filtered by status, sorted by created_at descending
     */
    suspend fun getClaimsByStatus(status: ClaimStatus): List<ClaimPacket>
    
    /**
     * Gets a specific claim by ID
     */
    suspend fun getClaimById(claimId: String): ClaimPacket?
    
    /**
     * Syncs claims from backend API when online
     * Updates local database with latest claim statuses
     */
    suspend fun syncClaimsFromBackend(): Result<Unit>
    
    /**
     * Refreshes a specific claim from backend
     */
    suspend fun refreshClaim(claimId: String): Result<ClaimPacket>
}
