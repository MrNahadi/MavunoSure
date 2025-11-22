package com.mavunosure.app.data.remote.dto

import com.google.gson.annotations.SerializedName
import com.mavunosure.app.domain.model.CropType
import com.mavunosure.app.domain.model.Farm
import com.mavunosure.app.domain.model.GeoPoint
import java.time.Instant

data class FarmDto(
    @SerializedName("id")
    val id: String,
    @SerializedName("farmer_name")
    val farmerName: String,
    @SerializedName("farmer_id")
    val farmerId: String,
    @SerializedName("phone_number")
    val phoneNumber: String,
    @SerializedName("crop_type")
    val cropType: String,
    @SerializedName("gps_lat")
    val gpsLat: Double,
    @SerializedName("gps_lng")
    val gpsLng: Double,
    @SerializedName("gps_accuracy")
    val gpsAccuracy: Float,
    @SerializedName("registered_at")
    val registeredAt: String,
    @SerializedName("registered_by")
    val registeredBy: String?
)

data class FarmRegistrationRequest(
    @SerializedName("farmer_name")
    val farmerName: String,
    @SerializedName("farmer_id")
    val farmerId: String,
    @SerializedName("phone_number")
    val phoneNumber: String,
    @SerializedName("crop_type")
    val cropType: String,
    @SerializedName("gps_lat")
    val gpsLat: Double,
    @SerializedName("gps_lng")
    val gpsLng: Double,
    @SerializedName("gps_accuracy")
    val gpsAccuracy: Float
)

fun FarmDto.toDomain(): Farm {
    return Farm(
        id = id,
        farmerName = farmerName,
        farmerId = farmerId,
        phoneNumber = phoneNumber,
        cropType = CropType.valueOf(cropType.uppercase()),
        gpsCoordinates = GeoPoint(gpsLat, gpsLng),
        gpsAccuracy = gpsAccuracy,
        registeredAt = Instant.parse(registeredAt),
        registeredBy = registeredBy
    )
}

fun Farm.toRegistrationRequest(): FarmRegistrationRequest {
    return FarmRegistrationRequest(
        farmerName = farmerName,
        farmerId = farmerId,
        phoneNumber = phoneNumber,
        cropType = cropType.name.lowercase(),
        gpsLat = gpsCoordinates.latitude,
        gpsLng = gpsCoordinates.longitude,
        gpsAccuracy = gpsAccuracy
    )
}
