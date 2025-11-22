package com.mavunosure.app.di

import android.content.Context
import androidx.room.Room
import com.mavunosure.app.data.local.MavunoSureDatabase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): MavunoSureDatabase {
        return Room.databaseBuilder(
            context,
            MavunoSureDatabase::class.java,
            "mavunosure_db"
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    @Singleton
    fun provideFarmDao(database: MavunoSureDatabase): com.mavunosure.app.data.local.dao.FarmDao {
        return database.farmDao()
    }

    @Provides
    @Singleton
    fun provideClaimDao(database: MavunoSureDatabase): com.mavunosure.app.data.local.dao.ClaimDao {
        return database.claimDao()
    }

    @Provides
    @Singleton
    fun provideEncryptionManager(@ApplicationContext context: Context): com.mavunosure.app.data.local.EncryptionManager {
        return com.mavunosure.app.data.local.EncryptionManager(context)
    }

    @Provides
    @Singleton
    fun provideImageCompressor(@ApplicationContext context: Context): com.mavunosure.app.data.local.ImageCompressor {
        return com.mavunosure.app.data.local.ImageCompressor(context)
    }

    @Provides
    @Singleton
    fun provideSecureImageStorage(@ApplicationContext context: Context): com.mavunosure.app.data.local.SecureImageStorage {
        return com.mavunosure.app.data.local.SecureImageStorage(context)
    }
}
