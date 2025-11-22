package com.mavunosure.app.di

import android.content.Context
import android.hardware.SensorManager
import com.google.android.gms.location.FusedLocationProviderClient
import com.mavunosure.app.data.camera.MetadataCollector
import com.mavunosure.app.data.ml.TFLiteClassifier
import com.mavunosure.app.domain.camera.AntiFraudValidator
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object CameraModule {

    @Provides
    @Singleton
    fun provideSensorManager(
        @ApplicationContext context: Context
    ): SensorManager {
        return context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    }

    @Provides
    @Singleton
    fun provideMetadataCollector(
        sensorManager: SensorManager,
        locationClient: FusedLocationProviderClient
    ): MetadataCollector {
        return MetadataCollector(sensorManager, locationClient)
    }

    @Provides
    @Singleton
    fun provideAntiFraudValidator(): AntiFraudValidator {
        return AntiFraudValidator()
    }
}
