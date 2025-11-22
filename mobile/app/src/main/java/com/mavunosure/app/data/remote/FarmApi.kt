package com.mavunosure.app.data.remote

import com.mavunosure.app.data.remote.dto.FarmDto
import com.mavunosure.app.data.remote.dto.FarmRegistrationRequest
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface FarmApi {
    @POST("farms")
    suspend fun registerFarm(@Body request: FarmRegistrationRequest): FarmDto

    @GET("farms/{id}")
    suspend fun getFarmById(@Path("id") farmId: String): FarmDto

    @GET("farms/search")
    suspend fun searchFarmsByFarmerId(@Query("farmerId") farmerId: String): List<FarmDto>
}
