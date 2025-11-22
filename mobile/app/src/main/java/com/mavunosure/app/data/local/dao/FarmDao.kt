package com.mavunosure.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.mavunosure.app.data.local.entity.FarmEntity

@Dao
interface FarmDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFarm(farm: FarmEntity)

    @Query("SELECT * FROM farms WHERE id = :farmId")
    suspend fun getFarmById(farmId: String): FarmEntity?

    @Query("SELECT * FROM farms WHERE farmerId = :farmerId")
    suspend fun getFarmsByFarmerId(farmerId: String): List<FarmEntity>

    @Query("SELECT * FROM farms")
    suspend fun getAllFarms(): List<FarmEntity>
}
