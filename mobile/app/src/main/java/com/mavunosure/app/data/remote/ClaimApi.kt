package com.mavunosure.app.data.remote

import com.mavunosure.app.data.remote.dto.ClaimCreateRequest
import com.mavunosure.app.data.remote.dto.ClaimCreateResponse
import com.mavunosure.app.data.remote.dto.ClaimDetailResponse
import com.mavunosure.app.data.remote.dto.ClaimListResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ClaimApi {
    
    @POST("api/v1/claims")
    suspend fun createClaim(
        @Body request: ClaimCreateRequest
    ): Response<ClaimCreateResponse>
    
    @GET("api/v1/claims")
    suspend fun getClaims(
        @Query("agentId") agentId: String? = null,
        @Query("status") status: String? = null
    ): Response<ClaimListResponse>
    
    @GET("api/v1/claims/{id}")
    suspend fun getClaimById(
        @Path("id") claimId: String
    ): Response<ClaimDetailResponse>
}
