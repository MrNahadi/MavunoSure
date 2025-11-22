package com.mavunosure.app.data.repository

import android.content.Context
import android.util.Base64
import com.mavunosure.app.data.local.EncryptionManager
import com.mavunosure.app.data.local.ImageCompressor
import com.mavunosure.app.data.local.dao.ClaimDao
import com.mavunosure.app.data.local.entity.toDomain
import com.mavunosure.app.data.local.entity.toEntity
import com.mavunosure.app.data.remote.ClaimApi
import com.mavunosure.app.data.remote.dto.*
import com.mavunosure.app.domain.model.ClaimPacket
import com.mavunosure.app.domain.model.SyncStatus
import com.mavunosure.app.domain.repository.OfflineQueueRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.io.File
import javax.inject.Inject

class OfflineQueueRepositoryImpl @Inject constructor(
    private val claimDao: ClaimDao,
    private val claimApi: ClaimApi,
    private val encryptionManager: EncryptionManager,
    private val imageCompressor: ImageCompressor,
    private val context: Context
) : OfflineQueueRepository {
    
    private val secureImagesDir: File by lazy {
        File(context.filesDir, "secure_images").apply {
            if (!exists()) mkdirs()
        }
    }
    
    private val compressedImagesDir: File by lazy {
        File(context.cacheDir, "compressed_images").apply {
            if (!exists()) mkdirs()
        }
    }
    
    override suspend fun enqueueClaim(claim: ClaimPacket): Result<Unit> {
        return try {
            // Compress the image
            val originalFile = File(claim.imageUri)
            val compressedFile = File(compressedImagesDir, "${claim.claimId}_compressed.jpg")
            imageCompressor.compressImage(originalFile, compressedFile)
            
            // Encrypt the compressed image
            val encryptedFile = File(secureImagesDir, "${claim.claimId}_encrypted.dat")
            encryptionManager.encryptFile(compressedFile, encryptedFile)
            
            // Update claim with encrypted image path
            val updatedClaim = claim.copy(
                imageUri = encryptedFile.absolutePath,
                syncStatus = SyncStatus.PENDING
            )
            
            // Save to database
            claimDao.insertClaim(updatedClaim.toEntity())
            
            // Clean up temporary compressed file
            compressedFile.delete()
            
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun getPendingClaims(): List<ClaimPacket> {
        return claimDao.getPendingClaims().map { it.toDomain() }
    }
    
    override suspend fun syncClaim(claimId: String): Result<Unit> {
        return try {
            // Update status to syncing
            claimDao.updateSyncStatus(claimId, SyncStatus.SYNCING.name)
            
            // Get the claim
            val claimEntity = claimDao.getClaimById(claimId)
                ?: return Result.failure(Exception("Claim not found"))
            
            val claim = claimEntity.toDomain()
            
            // Decrypt the image
            val encryptedFile = File(claim.imageUri)
            val decryptedFile = File(compressedImagesDir, "${claim.claimId}_decrypted.jpg")
            encryptionManager.decryptFile(encryptedFile, decryptedFile)
            
            // Read and encode image to Base64
            val imageBytes = decryptedFile.readBytes()
            val imageBase64 = Base64.encodeToString(imageBytes, Base64.NO_WRAP)
            
            // Prepare API request
            val request = ClaimCreateRequest(
                agentId = claim.agentId,
                farmId = claim.farmId,
                farmGps = GpsDto(
                    latitude = claim.farmGps.latitude,
                    longitude = claim.farmGps.longitude
                ),
                timestampCreated = claim.timestamp.toString(),
                groundTruth = GroundTruthDto(
                    mlClass = claim.groundTruth.mlClass.name.lowercase(),
                    mlConfidence = claim.groundTruth.mlConfidence,
                    topThreeClasses = claim.groundTruth.topThreeClasses.map {
                        ClassificationDto(
                            className = it.first.name.lowercase(),
                            confidence = it.second
                        )
                    },
                    deviceTilt = claim.groundTruth.deviceTilt,
                    deviceAzimuth = claim.groundTruth.deviceAzimuth,
                    captureGps = GpsDto(
                        latitude = claim.groundTruth.captureGps.latitude,
                        longitude = claim.groundTruth.captureGps.longitude
                    )
                ),
                imageData = imageBase64
            )
            
            // Make API call
            val response = claimApi.createClaim(request)
            
            // Clean up decrypted file
            decryptedFile.delete()
            
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                // Update status to failed
                claimDao.updateSyncStatus(claimId, SyncStatus.FAILED.name)
                Result.failure(Exception("API error: ${response.code()}"))
            }
        } catch (e: Exception) {
            // Update status to failed
            claimDao.updateSyncStatus(claimId, SyncStatus.FAILED.name)
            Result.failure(e)
        }
    }
    
    override suspend fun markSynced(claimId: String): Result<Unit> {
        return try {
            // Update status
            claimDao.updateSyncStatus(claimId, SyncStatus.SYNCED.name)
            
            // Delete encrypted image file
            val claimEntity = claimDao.getClaimById(claimId)
            if (claimEntity != null) {
                val encryptedFile = File(claimEntity.imageUri)
                if (encryptedFile.exists()) {
                    encryptedFile.delete()
                }
            }
            
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override fun observeAllClaims(): Flow<List<ClaimPacket>> {
        return claimDao.getAllClaimsFlow().map { entities ->
            entities.map { it.toDomain() }
        }
    }
}
