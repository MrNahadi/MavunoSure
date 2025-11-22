package com.mavunosure.app.ui.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import com.mavunosure.app.domain.model.ClaimStatus
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ClaimDetailScreen(
    claimId: String,
    viewModel: ClaimDetailViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(claimId) {
        viewModel.loadClaim(claimId)
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Claim Details") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { paddingValues ->
        when (uiState) {
            is ClaimDetailUiState.Loading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            is ClaimDetailUiState.Success -> {
                val claim = (uiState as ClaimDetailUiState.Success).claim
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Status Card
                    StatusCard(status = claim.claimStatus)
                    
                    // Claim Info Card
                    ClaimInfoCard(
                        claimId = claim.claimId,
                        timestamp = claim.timestamp.atZone(java.time.ZoneId.systemDefault())
                            .format(DateTimeFormatter.ofPattern("MMM dd, yyyy HH:mm"))
                    )
                    
                    // Image Card
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp)
                        ) {
                            Text(
                                text = "Claim Photo",
                                style = MaterialTheme.typography.titleMedium
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            AsyncImage(
                                model = claim.imageUri,
                                contentDescription = "Claim photo",
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(300.dp),
                                contentScale = ContentScale.Crop
                            )
                        }
                    }
                    
                    // Ground Truth Card
                    GroundTruthCard(
                        mlClass = claim.groundTruth.mlClass.name.replace("_", " "),
                        confidence = claim.groundTruth.mlConfidence,
                        topClasses = claim.groundTruth.topThreeClasses
                    )
                    
                    // Location Card
                    LocationCard(
                        farmGps = claim.farmGps,
                        captureGps = claim.groundTruth.captureGps,
                        deviceTilt = claim.groundTruth.deviceTilt,
                        deviceAzimuth = claim.groundTruth.deviceAzimuth
                    )
                }
            }
            is ClaimDetailUiState.Error -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(32.dp)
                    ) {
                        Text(
                            text = "Error loading claim",
                            style = MaterialTheme.typography.headlineSmall
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = (uiState as ClaimDetailUiState.Error).message,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { viewModel.loadClaim(claimId) }) {
                            Text("Retry")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusCard(status: ClaimStatus) {
    val (color, label) = when (status) {
        ClaimStatus.PENDING -> Color(0xFFFFA726) to "Pending Verification"
        ClaimStatus.FLAGGED_FOR_REVIEW -> Color(0xFFFFA726) to "Flagged for Review"
        ClaimStatus.AUTO_APPROVED -> Color(0xFF66BB6A) to "Approved"
        ClaimStatus.PAID -> Color(0xFF66BB6A) to "Paid"
        ClaimStatus.REJECTED -> Color(0xFFEF5350) to "Rejected"
    }
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(12.dp)
                    .padding(end = 8.dp)
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    shape = MaterialTheme.shapes.small,
                    color = color
                ) {}
            }
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.titleLarge,
                color = color
            )
        }
    }
}

@Composable
private fun ClaimInfoCard(claimId: String, timestamp: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Claim Information",
                style = MaterialTheme.typography.titleMedium
            )
            Divider()
            InfoRow(label = "Claim ID", value = claimId.take(16))
            InfoRow(label = "Submitted", value = timestamp)
        }
    }
}

@Composable
private fun GroundTruthCard(
    mlClass: String,
    confidence: Float,
    topClasses: List<Pair<String, Float>>
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Ground Truth Assessment",
                style = MaterialTheme.typography.titleMedium
            )
            Divider()
            InfoRow(label = "Classification", value = mlClass)
            InfoRow(label = "Confidence", value = "${(confidence * 100).toInt()}%")
            
            if (topClasses.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Top Predictions",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                topClasses.forEachIndexed { index, (className, conf) ->
                    InfoRow(
                        label = "${index + 1}. ${className.replace("_", " ")}",
                        value = "${(conf * 100).toInt()}%"
                    )
                }
            }
        }
    }
}

@Composable
private fun LocationCard(
    farmGps: com.mavunosure.app.domain.model.GeoPoint,
    captureGps: com.mavunosure.app.domain.model.GeoPoint,
    deviceTilt: Float,
    deviceAzimuth: Float
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Location & Metadata",
                style = MaterialTheme.typography.titleMedium
            )
            Divider()
            InfoRow(
                label = "Farm GPS",
                value = "${String.format("%.6f", farmGps.latitude)}, ${String.format("%.6f", farmGps.longitude)}"
            )
            InfoRow(
                label = "Capture GPS",
                value = "${String.format("%.6f", captureGps.latitude)}, ${String.format("%.6f", captureGps.longitude)}"
            )
            InfoRow(label = "Device Tilt", value = "${String.format("%.1f", deviceTilt)}°")
            InfoRow(label = "Device Azimuth", value = "${String.format("%.1f", deviceAzimuth)}°")
        }
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium
        )
    }
}