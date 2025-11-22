package com.mavunosure.app.data.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.mavunosure.app.domain.repository.OfflineQueueRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.delay

/**
 * WorkManager worker that syncs pending claims to the backend
 */
@HiltWorker
class ClaimSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val offlineQueueRepository: OfflineQueueRepository
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        return try {
            // Get all pending claims
            val pendingClaims = offlineQueueRepository.getPendingClaims()
            
            if (pendingClaims.isEmpty()) {
                return Result.success()
            }
            
            var successCount = 0
            var failureCount = 0
            
            // Sync each claim
            for (claim in pendingClaims) {
                val result = offlineQueueRepository.syncClaim(claim.claimId)
                
                if (result.isSuccess) {
                    // Mark as synced
                    offlineQueueRepository.markSynced(claim.claimId)
                    successCount++
                } else {
                    failureCount++
                }
                
                // Small delay between requests to avoid overwhelming the server
                delay(500)
            }
            
            // If all failed, retry
            if (failureCount > 0 && successCount == 0) {
                Result.retry()
            } else {
                Result.success()
            }
        } catch (e: Exception) {
            // Retry on exception
            if (runAttemptCount < MAX_RETRY_ATTEMPTS) {
                Result.retry()
            } else {
                Result.failure()
            }
        }
    }
    
    companion object {
        const val WORK_NAME = "claim_sync_work"
        private const val MAX_RETRY_ATTEMPTS = 3
    }
}
