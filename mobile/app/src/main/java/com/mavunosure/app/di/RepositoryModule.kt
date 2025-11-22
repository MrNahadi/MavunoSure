package com.mavunosure.app.di

import com.mavunosure.app.data.repository.AuthRepositoryImpl
import com.mavunosure.app.data.repository.ClaimRepositoryImpl
import com.mavunosure.app.data.repository.FarmRepositoryImpl
import com.mavunosure.app.domain.repository.AuthRepository
import com.mavunosure.app.domain.repository.ClaimRepository
import com.mavunosure.app.domain.repository.FarmRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        authRepositoryImpl: AuthRepositoryImpl
    ): AuthRepository

    @Binds
    @Singleton
    abstract fun bindFarmRepository(
        farmRepositoryImpl: FarmRepositoryImpl
    ): FarmRepository

    @Binds
    @Singleton
    abstract fun bindOfflineQueueRepository(
        offlineQueueRepositoryImpl: com.mavunosure.app.data.repository.OfflineQueueRepositoryImpl
    ): com.mavunosure.app.domain.repository.OfflineQueueRepository

    @Binds
    @Singleton
    abstract fun bindClaimRepository(
        claimRepositoryImpl: ClaimRepositoryImpl
    ): ClaimRepository
}
