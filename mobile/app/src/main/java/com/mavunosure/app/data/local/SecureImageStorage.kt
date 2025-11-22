package com.mavunosure.app.data.local

import android.content.Context
import android.graphics.Bitmap
import java.io.File
import java.io.FileOutputStream
import java.util.UUID
import javax.inject.Inject

/**
 * Manages secure storage of images in app-private directory
 */
class SecureImageStorage @Inject constructor(
    private val context: Context
) {
    
    private val secureImagesDir: File by lazy {
        File(context.filesDir, "secure_images").apply {
            if (!exists()) {
                mkdirs()
                // Create .nomedia file to prevent gallery scanning
                File(this, ".nomedia").createNewFile()
            }
        }
    }
    
    /**
     * Saves a bitmap to secure storage and returns the file path
     * Images are stored in app-private directory and won't appear in gallery
     */
    fun saveBitmap(bitmap: Bitmap, claimId: String = UUID.randomUUID().toString()): File {
        val file = File(secureImagesDir, "${claimId}_original.jpg")
        
        FileOutputStream(file).use { out ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, 100, out)
        }
        
        return file
    }
    
    /**
     * Gets a file from secure storage
     */
    fun getFile(claimId: String): File {
        return File(secureImagesDir, "${claimId}_original.jpg")
    }
    
    /**
     * Deletes an image from secure storage
     */
    fun deleteImage(claimId: String): Boolean {
        val file = getFile(claimId)
        return if (file.exists()) {
            file.delete()
        } else {
            false
        }
    }
    
    /**
     * Checks if an image exists in secure storage
     */
    fun imageExists(claimId: String): Boolean {
        return getFile(claimId).exists()
    }
    
    /**
     * Gets the secure images directory
     */
    fun getSecureDirectory(): File = secureImagesDir
}
