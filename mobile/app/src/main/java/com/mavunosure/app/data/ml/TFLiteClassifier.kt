package com.mavunosure.app.data.ml

import android.content.Context
import android.graphics.Bitmap
import com.mavunosure.app.domain.model.CropCondition
import com.mavunosure.app.domain.model.InferenceResult
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.gpu.CompatibilityList
import org.tensorflow.lite.gpu.GpuDelegate
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.system.measureTimeMillis

@Singleton
class TFLiteClassifier @Inject constructor(
    private val context: Context
) {
    private var interpreter: Interpreter? = null
    private var gpuDelegate: GpuDelegate? = null
    
    companion object {
        private const val MODEL_PATH = "maize_disease_v1.tflite"
        private const val INPUT_SIZE = 224
        private const val PIXEL_SIZE = 3
        private const val IMAGE_MEAN = 127.5f
        private const val IMAGE_STD = 127.5f
        private const val NUM_CLASSES = 6
    }

    /**
     * Initialize the TFLite interpreter with GPU delegate if available
     */
    fun initialize() {
        if (interpreter != null) return
        
        val options = Interpreter.Options()
        
        // Try to use GPU delegate if available
        val compatibilityList = CompatibilityList()
        if (compatibilityList.isDelegateSupportedOnThisDevice) {
            gpuDelegate = GpuDelegate(compatibilityList.bestOptionsForThisDevice)
            options.addDelegate(gpuDelegate)
        } else {
            // Use 4 threads for CPU inference
            options.setNumThreads(4)
        }
        
        val model = loadModelFile()
        interpreter = Interpreter(model, options)
    }

    /**
     * Load the TFLite model from assets
     */
    private fun loadModelFile(): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd(MODEL_PATH)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        val startOffset = fileDescriptor.startOffset
        val declaredLength = fileDescriptor.declaredLength
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
    }

    /**
     * Preprocess the image: resize to 224x224 and normalize
     */
    fun preprocessImage(bitmap: Bitmap): ByteBuffer {
        val resizedBitmap = Bitmap.createScaledBitmap(bitmap, INPUT_SIZE, INPUT_SIZE, true)
        
        val byteBuffer = ByteBuffer.allocateDirect(4 * INPUT_SIZE * INPUT_SIZE * PIXEL_SIZE)
        byteBuffer.order(ByteOrder.nativeOrder())
        
        val intValues = IntArray(INPUT_SIZE * INPUT_SIZE)
        resizedBitmap.getPixels(intValues, 0, INPUT_SIZE, 0, 0, INPUT_SIZE, INPUT_SIZE)
        
        var pixel = 0
        for (i in 0 until INPUT_SIZE) {
            for (j in 0 until INPUT_SIZE) {
                val value = intValues[pixel++]
                
                // Normalize RGB values to [-1, 1]
                byteBuffer.putFloat(((value shr 16 and 0xFF) - IMAGE_MEAN) / IMAGE_STD)
                byteBuffer.putFloat(((value shr 8 and 0xFF) - IMAGE_MEAN) / IMAGE_STD)
                byteBuffer.putFloat(((value and 0xFF) - IMAGE_MEAN) / IMAGE_STD)
            }
        }
        
        return byteBuffer
    }

    /**
     * Run inference on the preprocessed image
     */
    fun classify(bitmap: Bitmap): InferenceResult {
        if (interpreter == null) {
            initialize()
        }
        
        val inputBuffer = preprocessImage(bitmap)
        val outputArray = Array(1) { FloatArray(NUM_CLASSES) }
        
        val inferenceTime = measureTimeMillis {
            interpreter?.run(inputBuffer, outputArray)
        }
        
        val probabilities = outputArray[0]
        
        // Get top 3 classes
        val classesWithProbs = probabilities.mapIndexed { index, prob ->
            CropCondition.fromIndex(index) to prob
        }.sortedByDescending { it.second }.take(3)
        
        val primaryClass = classesWithProbs[0].first
        val confidence = classesWithProbs[0].second
        
        return InferenceResult(
            primaryClass = primaryClass,
            confidence = confidence,
            topThreeClasses = classesWithProbs,
            inferenceTimeMs = inferenceTime
        )
    }

    /**
     * Release resources
     */
    fun close() {
        interpreter?.close()
        interpreter = null
        gpuDelegate?.close()
        gpuDelegate = null
    }
}
