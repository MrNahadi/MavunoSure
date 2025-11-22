package com.mavunosure.app.ui.camera

import android.Manifest
import android.graphics.Bitmap
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Camera
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.hilt.navigation.compose.hiltViewModel
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.rememberMultiplePermissionsState

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun SmartCameraScreen(
    farmLatitude: Double,
    farmLongitude: Double,
    onCaptureComplete: (Bitmap, com.mavunosure.app.domain.model.CaptureMetadata) -> Unit,
    onCancel: () -> Unit,
    viewModel: SmartCameraViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    
    val permissionsState = rememberMultiplePermissionsState(
        permissions = listOf(
            Manifest.permission.CAMERA,
            Manifest.permission.ACCESS_FINE_LOCATION
        )
    )

    val uiState by viewModel.uiState.collectAsState()
    val validationState by viewModel.validationState.collectAsState()

    LaunchedEffect(farmLatitude, farmLongitude) {
        viewModel.setFarmLocation(farmLatitude, farmLongitude)
    }

    LaunchedEffect(permissionsState.allPermissionsGranted) {
        if (!permissionsState.allPermissionsGranted) {
            permissionsState.launchMultiplePermissionRequest()
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        when {
            !permissionsState.allPermissionsGranted -> {
                PermissionRequiredScreen(
                    onRequestPermissions = { permissionsState.launchMultiplePermissionRequest() }
                )
            }
            uiState is CameraUiState.CaptureSuccess -> {
                val successState = uiState as CameraUiState.CaptureSuccess
                CaptureResultScreen(
                    bitmap = successState.bitmap,
                    inferenceResult = successState.inferenceResult,
                    onProceed = {
                        onCaptureComplete(successState.bitmap, successState.metadata)
                    },
                    onRetake = {
                        viewModel.resetState()
                    }
                )
            }
            else -> {
                CameraPreviewScreen(
                    validationState = validationState,
                    isCapturing = uiState is CameraUiState.Capturing,
                    onCapture = { bitmap ->
                        viewModel.captureAndClassify(bitmap)
                    },
                    onCancel = onCancel,
                    onValidationUpdate = { lat, lng ->
                        viewModel.updateValidation(lat, lng)
                    }
                )
            }
        }
    }
}

@Composable
fun CameraPreviewScreen(
    validationState: com.mavunosure.app.domain.model.CameraValidation,
    isCapturing: Boolean,
    onCapture: (Bitmap) -> Unit,
    onCancel: () -> Unit,
    onValidationUpdate: (Double, Double) -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var previewView: PreviewView? by remember { mutableStateOf(null) }

    Box(modifier = Modifier.fillMaxSize()) {
        // Camera Preview
        AndroidView(
            factory = { ctx ->
                PreviewView(ctx).also {
                    previewView = it
                }
            },
            modifier = Modifier.fillMaxSize()
        )

        // Guidance overlay
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.TopCenter)
                .background(Color.Black.copy(alpha = 0.6f))
                .padding(16.dp)
        ) {
            Text(
                text = "Point at the most affected leaf. Hold steady.",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Validation indicator
            ValidationIndicator(validationState)
        }

        // Close button
        IconButton(
            onClick = onCancel,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(16.dp)
        ) {
            Icon(
                imageVector = Icons.Default.Close,
                contentDescription = "Close",
                tint = Color.White
            )
        }

        // Capture button
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            if (!validationState.isValid) {
                Text(
                    text = validationState.message,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .background(
                            Color.Red.copy(alpha = 0.8f),
                            RoundedCornerShape(8.dp)
                        )
                        .padding(12.dp)
                )
                Spacer(modifier = Modifier.height(16.dp))
            }
            
            Button(
                onClick = {
                    // In real implementation, capture from CameraX
                    // For now, this is a placeholder
                },
                enabled = validationState.isValid && !isCapturing,
                modifier = Modifier.size(72.dp),
                shape = CircleShape,
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (validationState.isValid) Color.Green else Color.Gray
                )
            ) {
                if (isCapturing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(32.dp),
                        color = Color.White
                    )
                } else {
                    Icon(
                        imageVector = Icons.Default.Camera,
                        contentDescription = "Capture",
                        modifier = Modifier.size(32.dp),
                        tint = Color.White
                    )
                }
            }
        }
    }
}

@Composable
fun ValidationIndicator(validation: com.mavunosure.app.domain.model.CameraValidation) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceEvenly
    ) {
        ValidationItem(
            label = "Tilt",
            isValid = validation.isTiltValid,
            value = "${validation.tiltAngle.toInt()}°"
        )
        ValidationItem(
            label = "Distance",
            isValid = validation.isGpsValid,
            value = "${validation.distanceFromFarm.toInt()}m"
        )
    }
}

@Composable
fun ValidationItem(label: String, isValid: Boolean, value: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Canvas(modifier = Modifier.size(12.dp)) {
            drawCircle(color = if (isValid) Color.Green else Color.Red)
        }
        Column {
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = Color.White
            )
            Text(
                text = value,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
fun CaptureResultScreen(
    bitmap: Bitmap,
    inferenceResult: com.mavunosure.app.domain.model.InferenceResult,
    onProceed: () -> Unit,
    onRetake: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Classification Result",
            style = MaterialTheme.typography.headlineSmall,
            color = Color.White
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Show captured image
        Image(
            bitmap = bitmap.asImageBitmap(),
            contentDescription = "Captured image",
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Show classification result
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface
            )
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = inferenceResult.primaryClass.displayName,
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Confidence: ${(inferenceResult.confidence * 100).toInt()}%",
                    style = MaterialTheme.typography.bodyLarge
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = "Top 3 Predictions:",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold
                )
                inferenceResult.topThreeClasses.forEach { (condition, confidence) ->
                    Text(
                        text = "${condition.displayName}: ${(confidence * 100).toInt()}%",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                
                Text(
                    text = "Inference time: ${inferenceResult.inferenceTimeMs}ms",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Action buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            OutlinedButton(
                onClick = onRetake,
                modifier = Modifier.weight(1f)
            ) {
                Text("Retake")
            }
            Button(
                onClick = onProceed,
                modifier = Modifier.weight(1f)
            ) {
                Text("Proceed")
            }
        }
    }
}

@Composable
fun PermissionRequiredScreen(onRequestPermissions: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Camera and Location permissions are required",
            style = MaterialTheme.typography.titleMedium,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = onRequestPermissions) {
            Text("Grant Permissions")
        }
    }
}
