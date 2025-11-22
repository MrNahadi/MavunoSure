package com.mavunosure.app.data.repository

import com.mavunosure.app.data.local.dao.FarmDao
import com.mavunosure.app.data.local.entity.toDomain
import com.mavunosure.app.data.local.entity.toEntity
import com.mavunosure.app.data.remote.FarmApi
import com.mavunosure.app.data.remote.dto.toDomain
import com.mavunosure.app.data.remote.dto.toRegistrationRequest
import com.mavunosure.app.domain.model.Farm
import com.mavunosure.app.domain.repository.FarmRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject

class FarmRepositoryImpl @Inject constructor(
    private val farmApi: FarmApi,
    private val farmDao: FarmDao
) : FarmRepository {

    override suspend fun registerFarm(farm: Farm): Result<Farm> = withContext(Dispatchers.IO) {
        try {
            // Attempt to register farm with backend API
            val request = farm.toRegistrationRequest()
            val response = farmApi.registerFarm(request)
            val registeredFarm = response.toDomain()
            
            // Store in local database
            farmDao.insertFarm(registeredFarm.toEntity())
            
            Result.success(registeredFarm)
        } catch (e: Exception) {
            // If API call fails, store locally for later sync
            farmDao.insertFarm(farm.toEntity())
            Result.failure(e)
        }
    }

    override suspend fun getFarmById(id: String): Result<Farm> = withContext(Dispatchers.IO) {
        try {
            // Try to fetch from API first
            val response = farmApi.getFarmById(id)
            val farm = response.toDomain()
            
            // Update local cache
            farmDao.insertFarm(farm.toEntity())
            
            Result.success(farm)
        } catch (e: Exception) {
            // Fallback to local database
            val localFarm = farmDao.getFarmById(id)
            if (localFarm != null) {
                Result.success(localFarm.toDomain())
            } else {
                Result.failure(e)
            }
        }
    }

    override suspend fun searchFarmsByFarmerId(farmerId: String): Result<List<Farm>> = 
        withContext(Dispatchers.IO) {
            try {
                // Try to fetch from API first
                val response = farmApi.searchFarmsByFarmerId(farmerId)
                val farms = response.map { it.toDomain() }
                
                // Update local cache
                farms.forEach { farm ->
                    farmDao.insertFarm(farm.toEntity())
                }
                
                Result.success(farms)
            } catch (e: Exception) {
                // Fallback to local database
                val localFarms = farmDao.getFarmsByFarmerId(farmerId)
                if (localFarms.isNotEmpty()) {
                    Result.success(localFarms.map { it.toDomain() })
                } else {
                    Result.failure(e)
                }
            }
        }
}
