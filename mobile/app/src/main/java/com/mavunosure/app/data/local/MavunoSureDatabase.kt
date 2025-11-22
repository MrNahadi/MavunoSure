package com.mavunosure.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.mavunosure.app.data.local.dao.ClaimDao
import com.mavunosure.app.data.local.dao.FarmDao
import com.mavunosure.app.data.local.entity.ClaimEntity
import com.mavunosure.app.data.local.entity.FarmEntity

@Database(
    entities = [FarmEntity::class, ClaimEntity::class],
    version = 3,
    exportSchema = false
)
abstract class MavunoSureDatabase : RoomDatabase() {
    abstract fun farmDao(): FarmDao
    abstract fun claimDao(): ClaimDao
}
