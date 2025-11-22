package com.mavunosure.app.domain.model

import java.time.Instant

data class ClaimPacket(
    val claimId: String,
    val agentId: String,
    val farmId: String,
    val farmGps: GeoPoint,
    val timestamp: Instant,
    val groundTruth: GroundTruthData,
    val imageUri: String,
    val syncStatus: SyncStatus,
    val claimStatus: ClaimStatus = ClaimStatus.PENDING
)
