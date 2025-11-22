package com.mavunosure.app.data.local

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import androidx.exifinterface.media.ExifInterface
import java.io.File
import java.io.FileOutputStream

/**
 * Handles image compression for offline storage
 */
class ImageCompressor(private val context: Context) {
    
    /**
     * Compresses an image to JPEG with 80% quality and max dimension of 1024px
     * Returns the compressed file
     */
    fun compressImage(sourceFile: File, destFile: File): File {
        // Load the bitmap
        val options = BitmapFactory.Options().apply {
            inJustDecodeBounds = true
        }
        BitmapFactory.decodeFile(sourceFile.absolutePath, options)
        
        // Calculate sample size
        val sampleSize = calculateSampleSize(options.outWidth, options.outHeight, MAX_DIMENSION)
        
        // Load the actual bitmap with sampling
        options.inJustDecodeBounds = false
        options.inSampleSize = sampleSize
        var bitmap = BitmapFactory.decodeFile(sourceFile.absolutePath, options)
        
        // Handle EXIF orientation
        bitmap = rotateImageIfRequired(bitmap, sourceFile)
        
        // Scale down if still too large
        if (bitmap.width > MAX_DIMENSION || bitmap.height > MAX_DIMENSION) {
            bitmap = scaleBitmap(bitmap, MAX_DIMENSION)
        }
        
        // Compress to JPEG
        FileOutputStream(destFile).use { out ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, out)
        }
        
        bitmap.recycle()
        
        return destFile
    }
    
    private fun calculateSampleSize(width: Int, height: Int, maxDimension: Int): Int {
        var sampleSize = 1
        val maxCurrentDimension = maxOf(width, height)
        
        while (maxCurrentDimension / sampleSize > maxDimension) {
            sampleSize *= 2
        }
        
        return sampleSize
    }
    
    private fun scaleBitmap(bitmap: Bitmap, maxDimension: Int): Bitmap {
        val width = bitmap.width
        val height = bitmap.height
        
        val scale = if (width > height) {
            maxDimension.toFloat() / width
        } else {
            maxDimension.toFloat() / height
        }
        
        val newWidth = (width * scale).toInt()
        val newHeight = (height * scale).toInt()
        
        return Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
    }
    
    private fun rotateImageIfRequired(bitmap: Bitmap, imageFile: File): Bitmap {
        val exif = ExifInterface(imageFile.absolutePath)
        val orientation = exif.getAttributeInt(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_NORMAL
        )
        
        return when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> rotateBitmap(bitmap, 90f)
            ExifInterface.ORIENTATION_ROTATE_180 -> rotateBitmap(bitmap, 180f)
            ExifInterface.ORIENTATION_ROTATE_270 -> rotateBitmap(bitmap, 270f)
            else -> bitmap
        }
    }
    
    private fun rotateBitmap(bitmap: Bitmap, degrees: Float): Bitmap {
        val matrix = Matrix().apply {
            postRotate(degrees)
        }
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }
    
    companion object {
        private const val MAX_DIMENSION = 1024
        private const val JPEG_QUALITY = 80
    }
}
