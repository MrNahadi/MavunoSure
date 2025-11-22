package com.mavunosure.app.data.local

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Manages AES-256 encryption using Android Keystore
 */
class EncryptionManager(private val context: Context) {
    
    private val keyStore: KeyStore = KeyStore.getInstance(KEYSTORE_PROVIDER).apply {
        load(null)
    }
    
    init {
        if (!keyStore.containsAlias(KEY_ALIAS)) {
            generateKey()
        }
    }
    
    private fun generateKey() {
        val keyGenerator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            KEYSTORE_PROVIDER
        )
        
        val keyGenParameterSpec = KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .build()
        
        keyGenerator.init(keyGenParameterSpec)
        keyGenerator.generateKey()
    }
    
    private fun getSecretKey(): SecretKey {
        return keyStore.getKey(KEY_ALIAS, null) as SecretKey
    }
    
    /**
     * Encrypts data and returns encrypted bytes with IV prepended
     */
    fun encrypt(data: ByteArray): ByteArray {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getSecretKey())
        
        val iv = cipher.iv
        val encryptedData = cipher.doFinal(data)
        
        // Prepend IV to encrypted data
        return iv + encryptedData
    }
    
    /**
     * Decrypts data where IV is prepended to the encrypted bytes
     */
    fun decrypt(encryptedDataWithIv: ByteArray): ByteArray {
        val iv = encryptedDataWithIv.copyOfRange(0, IV_SIZE)
        val encryptedData = encryptedDataWithIv.copyOfRange(IV_SIZE, encryptedDataWithIv.size)
        
        val cipher = Cipher.getInstance(TRANSFORMATION)
        val spec = GCMParameterSpec(GCM_TAG_LENGTH, iv)
        cipher.init(Cipher.DECRYPT_MODE, getSecretKey(), spec)
        
        return cipher.doFinal(encryptedData)
    }
    
    /**
     * Encrypts a file and saves it to the destination
     */
    fun encryptFile(sourceFile: File, destFile: File) {
        val data = sourceFile.readBytes()
        val encryptedData = encrypt(data)
        destFile.writeBytes(encryptedData)
    }
    
    /**
     * Decrypts a file and saves it to the destination
     */
    fun decryptFile(encryptedFile: File, destFile: File) {
        val encryptedData = encryptedFile.readBytes()
        val decryptedData = decrypt(encryptedData)
        destFile.writeBytes(decryptedData)
    }
    
    companion object {
        private const val KEYSTORE_PROVIDER = "AndroidKeyStore"
        private const val KEY_ALIAS = "mavunosure_encryption_key"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val IV_SIZE = 12 // GCM standard IV size
        private const val GCM_TAG_LENGTH = 128
    }
}
