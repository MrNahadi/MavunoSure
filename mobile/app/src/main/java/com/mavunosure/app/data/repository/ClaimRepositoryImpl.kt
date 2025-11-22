package com.mavunosure.app.data.repository

import android.content.Context
import com.mavunosure.app.data.local.dao.ClaimDao
import com.mavunosure.app.data.local.entity.ClaimEntity
import com.mavunosure.app.data.local.entity.toDomain
import com.mavunosure.app.data.remote.ClaimApi
import com.mavunosure.app.data.remote.dto.ClaimDetailResponse
import com.mavunosure.app.domain.model.*
import com.mavunosure.app.domain.repository.AuthRepository
import com.mavunosure.app.domain.repository.ClaimRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.Instant
import javax.inject.Inject

class ClaimRepositoryImpl @Inject constructor(
    private val claimDao: ClaimDao,
    private val claimApi: ClaimApi,
    private val authRepository: AuthRepository,
    private val context: Context
) : ClaimRepository {
    
    override fun observeAllClaims(): Flow<List<ClaimPacket>> {
        return claimDao.getAllClaimsFlow().map { entities ->
            entities.map { it.toDomain() }
                .sortedByDescending { it.timestamp }
        }
    }
    
    override suspend fun getAllClaims(): List<ClaimPacket> {
        return claimDao.getAllClaimsFlow()
            .map { entities ->
                entities.map { it.toDomain() }
                    .sortedByDescending { it.timestamp }
            }
            .let { flow ->
                // Get first emission
                var result: List<ClaimPacket> = emptyList()
                flow.collect { result = it }
                result
            }
    }
    
    override suspend fun getClaimsByStatus(status: ClaimStatus): List<ClaimPacket> {
        return claimDao.getClaimsByStatus(listOf(status.name))
            .map { it.toDomain() }
            .sortedByDescending { it.timestamp }
    }
    
    override suspend fun getClaimById(claimId: String): ClaimPacket? {
        return claimDao.getClaimById(claimId)?.toDomain()
    }
    
    override suspend fun syncClaimsFromBackend(): Result<Unit> {
        return try {
            // Get current agent ID from auth
            val agentId = getCurrentAgentId()
            
            // Fetch claims from backend
            val response = claimApi.getClaims(agentId = agentId)
            
            if (response.isSuccessful && response.body() != null) {
                val claimSummaries = response.body()!!.claims
                
                // For each claim, fetch full details and update local database
                claimSummaries.forEach { summary ->
                    try {
                        val detailResponse = claimApi.getClaimById(summary.id)
                        if (detailResponse.isSuccessful && detailResponse.body() != null) {
                            val claimDetail = detailResponse.body()!!
                            updateLocalClaimFromBackend(claimDetail)
                        }
                    } catch (e: Exception) {
                        // Continue with other claims if one fails
                    }
                }
                
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to fetch claims: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun refreshClaim(claimId: String): Result<ClaimPacket> {
        return try {
            val response = claimApi.getClaimById(claimId)
            
            if (response.isSuccessful && response.body() != null) {
                val claimDetail = response.body()!!
                val updatedClaim = updateLocalClaimFromBackend(claimDetail)
                Result.success(updatedClaim)
            } else {
                Result.failure(Exception("Failed to fetch claim: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    private suspend fun updateLocalClaimFromBackend(claimDetail: ClaimDetailResponse): ClaimPacket {
        // Get existing claim from local database
        val existingClaim = claimDao.getClaimById(claimDetail.id)
        
        // Parse claim status from backend
        val claimStatus = try {
            ClaimStatus.valueOf(claimDetail.status.uppercase())
        } catch (e: Exception) {
            ClaimStatus.PENDING
        }
        
        // Parse crop condition
        val cropCondition = try {
            CropCondition.valueOf(claimDetail.mlClass.uppercase())
        } catch (e: Exception) {
            CropCondition.OTHER
        }
        
        // Parse top three classes
        val topThreeClasses = claimDetail.topThreeClasses.map { classDto ->
            val condition = try {
                CropCondition.valueOf(classDto.className.uppercase())
            } catch (e: Exception) {
                CropCondition.OTHER
            }
            condition to classDto.confidence
        }
        
        // Create updated entity
        val updatedEntity = if (existingClaim != null) {
            // Update existing claim with backend data
            existingClaim.copy(
                claimStatus = claimStatus.name,
                syncStatus = SyncStatus.SYNCED.name
            )
        } else {
            // Create new entity from backend data
            ClaimEntity(
                claimId = claimDetail.id,
                agentId = claimDetail.agentId,
                farmId = claimDetail.farmId,
                farmGpsLatitude = claimDetail.farmGpsLat,
                farmGpsLongitude = claimDetail.farmGpsLng,
                timestamp = parseTimestamp(claimDetail.createdAt),
                mlClass = cropCondition.name,
                mlConfidence = claimDetail.mlConfidence,
                topThreeClassesJson = serializeTopThreeClasses(topThreeClasses),
                deviceTilt = claimDetail.deviceTilt,
                deviceAzimuth = claimDetail.deviceAzimuth,
                captureGpsLatitude = claimDetail.captureGpsLat,
                captureGpsLongitude = claimDetail.captureGpsLng,
                imageUri = claimDetail.imageUrl,
                syncStatus = SyncStatus.SYNCED.name,
                claimStatus = claimStatus.name
            )
        }
        
        // Save to database
        claimDao.insertClaim(updatedEntity)
        
        return updatedEntity.toDomain()
    }
    
    private fun getCurrentAgentId(): String {
        // Get agent ID from auth repository or shared preferences
        // For now, return a placeholder - this should be implemented based on auth flow
        return "current_agent_id"
    }
    
    private fun parseTimestamp(timestamp: String): Long {
        return try {
            Instant.parse(timestamp).toEpochMilli()
        } catch (e: Exception) {
            System.currentTimeMillis()
        }
    }
    
    private fun serializeTopThreeClasses(classes: List<Pair<CropCondition, Float>>): String {
        val gson = com.google.gson.Gson()
        val list = classes.map { 
            mapOf("condition" to it.first.name, "confidence" to it.second)
        }
        return gson.toJson(list)
    }
}
