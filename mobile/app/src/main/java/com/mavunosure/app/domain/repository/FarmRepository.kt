package com.mavunosure.app.domain.repository

import com.mavunosure.app.domain.model.Farm

interface FarmRepository {
    suspend fun registerFarm(farm: Farm): Result<Farm>
    suspend fun getFarmById(id: String): Result<Farm>
    suspend fun searchFarmsByFarmerId(farmerId: String): Result<List<Farm>>
}
