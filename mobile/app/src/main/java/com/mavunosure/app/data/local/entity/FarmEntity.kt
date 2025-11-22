package com.mavunosure.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.mavunosure.app.domain.model.CropType
import com.mavunosure.app.domain.model.Farm
import com.mavunosure.app.domain.model.GeoPoint
import java.time.Instant

@Entity(tableName = "farms")
data class FarmEntity(
    @PrimaryKey
    val id: String,
    val farmerName: String,
    val farmerId: String,
    val phoneNumber: String,
    val cropType: String,
    val latitude: Double,
    val longitude: Double,
    val gpsAccuracy: Float,
    val registeredAt: Long,
    val registeredBy: String?
)

fun FarmEntity.toDomain(): Farm {
    return Farm(
        id = id,
        farmerName = farmerName,
        farmerId = farmerId,
        phoneNumber = phoneNumber,
        cropType = CropType.valueOf(cropType),
        gpsCoordinates = GeoPoint(latitude, longitude),
        gpsAccuracy = gpsAccuracy,
        registeredAt = Instant.ofEpochMilli(registeredAt),
        registeredBy = registeredBy
    )
}

fun Farm.toEntity(): FarmEntity {
    return FarmEntity(
        id = id,
        farmerName = farmerName,
        farmerId = farmerId,
        phoneNumber = phoneNumber,
        cropType = cropType.name,
        latitude = gpsCoordinates.latitude,
        longitude = gpsCoordinates.longitude,
        gpsAccuracy = gpsAccuracy,
        registeredAt = registeredAt.toEpochMilli(),
        registeredBy = registeredBy
    )
}
