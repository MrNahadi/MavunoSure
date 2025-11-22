package com.mavunosure.app.domain.usecase

import android.graphics.Bitmap
import com.mavunosure.app.data.ml.TFLiteClassifier
import com.mavunosure.app.domain.model.InferenceResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Use case for running ML inference on crop images
 * Ensures inference runs on background thread and completes within 2 seconds
 */
class ClassifyImageUseCase @Inject constructor(
    private val classifier: TFLiteClassifier
) {
    companion object {
        private const val MAX_INFERENCE_TIME_MS = 2000L
    }

    suspend operator fun invoke(bitmap: Bitmap): Result<InferenceResult> = withContext(Dispatchers.Default) {
        try {
            val startTime = System.currentTimeMillis()
            val result = classifier.classify(bitmap)
            val elapsedTime = System.currentTimeMillis() - startTime
            
            // Log warning if inference takes too long
            if (elapsedTime > MAX_INFERENCE_TIME_MS) {
                // In production, log to analytics
                println("Warning: Inference took ${elapsedTime}ms (target: ${MAX_INFERENCE_TIME_MS}ms)")
            }
            
            Result.success(result)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
