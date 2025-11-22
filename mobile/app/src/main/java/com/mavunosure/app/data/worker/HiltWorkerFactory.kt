package com.mavunosure.app.data.worker

import android.content.Context
import androidx.work.Configuration
import androidx.work.WorkManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object WorkManagerModule {
    
    @Provides
    @Singleton
    fun provideClaimSyncScheduler(
        @ApplicationContext context: Context
    ): ClaimSyncScheduler {
        return ClaimSyncScheduler(context)
    }
}
