package com.mavunosure.app.ui.farm

import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.mavunosure.app.domain.location.LocationAccuracyStatus
import com.mavunosure.app.domain.location.LocationPermissionHandler
import com.mavunosure.app.domain.model.CropType

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FarmRegistrationScreen(
    onNavigateBack: () -> Unit,
    onRegistrationSuccess: () -> Unit,
    viewModel: FarmRegistrationViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current

    var showPermissionRationale by remember { mutableStateOf(false) }

    val locationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            viewModel.captureLocation()
        } else {
            showPermissionRationale = true
        }
    }

    LaunchedEffect(uiState.registrationSuccess) {
        if (uiState.registrationSuccess) {
            onRegistrationSuccess()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Register Farm") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Farmer Information Section
            Text(
                text = "Farmer Information",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary
            )

            OutlinedTextField(
                value = uiState.farmerName,
                onValueChange = viewModel::updateFarmerName,
                label = { Text("Farmer Name") },
                modifier = Modifier.fillMaxWidth(),
                isError = uiState.validationErrors.containsKey("farmerName"),
                supportingText = {
                    uiState.validationErrors["farmerName"]?.let {
                        Text(it, color = MaterialTheme.colorScheme.error)
                    }
                }
            )

            OutlinedTextField(
                value = uiState.farmerId,
                onValueChange = viewModel::updateFarmerId,
                label = { Text("Farmer ID Number") },
                modifier = Modifier.fillMaxWidth(),
                isError = uiState.validationErrors.containsKey("farmerId"),
                supportingText = {
                    uiState.validationErrors["farmerId"]?.let {
                        Text(it, color = MaterialTheme.colorScheme.error)
                    }
                }
            )

            OutlinedTextField(
                value = uiState.phoneNumber,
                onValueChange = viewModel::updatePhoneNumber,
                label = { Text("Phone Number") },
                modifier = Modifier.fillMaxWidth(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                isError = uiState.validationErrors.containsKey("phoneNumber"),
                supportingText = {
                    uiState.validationErrors["phoneNumber"]?.let {
                        Text(it, color = MaterialTheme.colorScheme.error)
                    }
                }
            )

            // Crop Type Selection
            var expanded by remember { mutableStateOf(false) }
            ExposedDropdownMenuBox(
                expanded = expanded,
                onExpandedChange = { expanded = it }
            ) {
                OutlinedTextField(
                    value = uiState.cropType.name,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Crop Type") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .menuAnchor()
                )
                ExposedDropdownMenu(
                    expanded = expanded,
                    onDismissRequest = { expanded = false }
                ) {
                    CropType.values().forEach { cropType ->
                        DropdownMenuItem(
                            text = { Text(cropType.name) },
                            onClick = {
                                viewModel.updateCropType(cropType)
                                expanded = false
                            }
                        )
                    }
                }
            }

            Divider()

            // GPS Location Section
            Text(
                text = "Farm Location",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary
            )

            Button(
                onClick = {
                    locationPermissionLauncher.launch(LocationPermissionHandler.REQUIRED_PERMISSIONS)
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isCapturingLocation
            ) {
                if (uiState.isCapturingLocation) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Capturing Location...")
                } else {
                    Icon(Icons.Default.LocationOn, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Capture GPS Location")
                }
            }

            // Location Display
            uiState.location?.let { location ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = when (uiState.accuracyStatus) {
                            is LocationAccuracyStatus.Ideal -> MaterialTheme.colorScheme.primaryContainer
                            is LocationAccuracyStatus.Acceptable -> MaterialTheme.colorScheme.secondaryContainer
                            is LocationAccuracyStatus.Warning -> MaterialTheme.colorScheme.errorContainer
                            else -> MaterialTheme.colorScheme.surfaceVariant
                        }
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "GPS Coordinates",
                            style = MaterialTheme.typography.titleSmall
                        )
                        Text(
                            text = "Lat: ${String.format("%.6f", location.location.latitude)}",
                            style = MaterialTheme.typography.bodyMedium
                        )
                        Text(
                            text = "Lng: ${String.format("%.6f", location.location.longitude)}",
                            style = MaterialTheme.typography.bodyMedium
                        )
                        Text(
                            text = "Accuracy: ${String.format("%.1f", location.accuracy)}m",
                            style = MaterialTheme.typography.bodyMedium
                        )

                        // Accuracy Warning
                        when (val status = uiState.accuracyStatus) {
                            is LocationAccuracyStatus.Warning -> {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Icon(
                                        Icons.Default.Warning,
                                        contentDescription = null,
                                        tint = MaterialTheme.colorScheme.error
                                    )
                                    Text(
                                        text = "GPS accuracy is poor (>${String.format("%.0f", status.accuracy)}m). " +
                                                "Please move to open ground for better signal.",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.error
                                    )
                                }
                            }
                            is LocationAccuracyStatus.Ideal -> {
                                Text(
                                    text = "✓ Excellent GPS accuracy",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                            is LocationAccuracyStatus.Acceptable -> {
                                Text(
                                    text = "✓ Good GPS accuracy",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.secondary
                                )
                            }
                            else -> {}
                        }
                    }
                }
            }

            if (uiState.validationErrors.containsKey("location")) {
                Text(
                    text = uiState.validationErrors["location"] ?: "",
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }

            // Error Display
            uiState.error?.let { error ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer
                    )
                ) {
                    Text(
                        text = error,
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer
                    )
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Register Button
            Button(
                onClick = viewModel::registerFarm,
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isRegistering
            ) {
                if (uiState.isRegistering) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Registering...")
                } else {
                    Text("Register Farm")
                }
            }
        }
    }

    // Permission Rationale Dialog
    if (showPermissionRationale) {
        AlertDialog(
            onDismissRequest = { showPermissionRationale = false },
            title = { Text("Location Permission Required") },
            text = { Text(LocationPermissionHandler.PERMISSION_RATIONALE) },
            confirmButton = {
                TextButton(
                    onClick = {
                        showPermissionRationale = false
                        locationPermissionLauncher.launch(LocationPermissionHandler.REQUIRED_PERMISSIONS)
                    }
                ) {
                    Text("Grant Permission")
                }
            },
            dismissButton = {
                TextButton(onClick = { showPermissionRationale = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}
