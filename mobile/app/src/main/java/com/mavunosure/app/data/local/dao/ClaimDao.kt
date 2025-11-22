package com.mavunosure.app.data.local.dao

import androidx.room.*
import com.mavunosure.app.data.local.entity.ClaimEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ClaimDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertClaim(claim: ClaimEntity)
    
    @Query("SELECT * FROM claims WHERE claimId = :claimId")
    suspend fun getClaimById(claimId: String): ClaimEntity?
    
    @Query("SELECT * FROM claims WHERE syncStatus IN (:statuses)")
    suspend fun getClaimsByStatus(statuses: List<String>): List<ClaimEntity>
    
    @Query("SELECT * FROM claims WHERE syncStatus = 'PENDING' OR syncStatus = 'FAILED'")
    suspend fun getPendingClaims(): List<ClaimEntity>
    
    @Query("SELECT * FROM claims ORDER BY timestamp DESC")
    fun getAllClaimsFlow(): Flow<List<ClaimEntity>>
    
    @Query("UPDATE claims SET syncStatus = :status WHERE claimId = :claimId")
    suspend fun updateSyncStatus(claimId: String, status: String)
    
    @Delete
    suspend fun deleteClaim(claim: ClaimEntity)
    
    @Query("DELETE FROM claims WHERE claimId = :claimId")
    suspend fun deleteClaimById(claimId: String)
}
