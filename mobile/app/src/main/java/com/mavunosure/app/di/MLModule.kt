package com.mavunosure.app.di

import android.content.Context
import com.mavunosure.app.data.ml.TFLiteClassifier
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object MLModule {

    @Provides
    @Singleton
    fun provideTFLiteClassifier(
        @ApplicationContext context: Context
    ): TFLiteClassifier {
        return TFLiteClassifier(context).apply {
            initialize()
        }
    }
}
