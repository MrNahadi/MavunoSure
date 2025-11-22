package com.mavunosure.app.data.ml

import android.content.Context
import android.graphics.Bitmap
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mock
import org.mockito.junit.MockitoJUnitRunner
import java.nio.ByteBuffer

@RunWith(MockitoJUnitRunner::class)
class TFLiteClassifierTest {

    @Mock
    private lateinit var context: Context

    private lateinit var classifier: TFLiteClassifier

    @Before
    fun setup() {
        classifier = TFLiteClassifier(context)
    }

    @Test
    fun `preprocessImage resizes bitmap to 224x224`() {
        val inputBitmap = Bitmap.createBitmap(512, 512, Bitmap.Config.ARGB_8888)
        
        val buffer = classifier.preprocessImage(inputBitmap)
        
        // Buffer size should be 224 * 224 * 3 channels * 4 bytes per float
        val expectedSize = 224 * 224 * 3 * 4
        assertEquals(expectedSize, buffer.capacity())
    }

    @Test
    fun `preprocessImage normalizes pixel values`() {
        // Create a white bitmap (RGB 255, 255, 255)
        val inputBitmap = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
        inputBitmap.eraseColor(android.graphics.Color.WHITE)
        
        val buffer = classifier.preprocessImage(inputBitmap)
        
        // Read first pixel values
        buffer.rewind()
        val r = buffer.float
        val g = buffer.float
        val b = buffer.float
        
        // White (255) should normalize to approximately 1.0
        // (255 - 127.5) / 127.5 = 1.0
        assertEquals(1.0f, r, 0.01f)
        assertEquals(1.0f, g, 0.01f)
        assertEquals(1.0f, b, 0.01f)
    }

    @Test
    fun `preprocessImage normalizes black pixels correctly`() {
        // Create a black bitmap (RGB 0, 0, 0)
        val inputBitmap = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
        inputBitmap.eraseColor(android.graphics.Color.BLACK)
        
        val buffer = classifier.preprocessImage(inputBitmap)
        
        // Read first pixel values
        buffer.rewind()
        val r = buffer.float
        val g = buffer.float
        val b = buffer.float
        
        // Black (0) should normalize to approximately -1.0
        // (0 - 127.5) / 127.5 = -1.0
        assertEquals(-1.0f, r, 0.01f)
        assertEquals(-1.0f, g, 0.01f)
        assertEquals(-1.0f, b, 0.01f)
    }

    @Test
    fun `preprocessImage handles different input sizes`() {
        val sizes = listOf(100, 224, 512, 1024)
        
        sizes.forEach { size ->
            val inputBitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
            val buffer = classifier.preprocessImage(inputBitmap)
            
            // All should result in same buffer size (224x224x3x4)
            val expectedSize = 224 * 224 * 3 * 4
            assertEquals("Failed for input size $size", expectedSize, buffer.capacity())
        }
    }

    @Test
    fun `preprocessImage handles rectangular images`() {
        val inputBitmap = Bitmap.createBitmap(400, 300, Bitmap.Config.ARGB_8888)
        
        val buffer = classifier.preprocessImage(inputBitmap)
        
        // Should still produce 224x224 output
        val expectedSize = 224 * 224 * 3 * 4
        assertEquals(expectedSize, buffer.capacity())
    }
}
