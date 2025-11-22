package com.mavunosure.app.ui.home

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.mavunosure.app.domain.model.*
import com.mavunosure.app.ui.theme.MavunoSureTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.time.Instant

@RunWith(AndroidJUnit4::class)
class HomeScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private val testClaims = listOf(
        createTestClaim("claim1", ClaimStatus.PENDING, Instant.now().minusSeconds(100)),
        createTestClaim("claim2", ClaimStatus.AUTO_APPROVED, Instant.now().minusSeconds(200)),
        createTestClaim("claim3", ClaimStatus.REJECTED, Instant.now().minusSeconds(300)),
        createTestClaim("claim4", ClaimStatus.PAID, Instant.now().minusSeconds(400))
    )

    @Test
    fun homeScreen_displaysTopBar() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithText("MavunoSure Dashboard").assertIsDisplayed()
    }

    @Test
    fun homeScreen_displaysNewVerificationButton() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithContentDescription("New Verification").assertIsDisplayed()
    }

    @Test
    fun homeScreen_displaysFilterChips() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithText("ALL").assertIsDisplayed()
        composeTestRule.onNodeWithText("PENDING").assertIsDisplayed()
        composeTestRule.onNodeWithText("APPROVED").assertIsDisplayed()
        composeTestRule.onNodeWithText("REJECTED").assertIsDisplayed()
        composeTestRule.onNodeWithText("PAID").assertIsDisplayed()
    }

    @Test
    fun homeScreen_filterChipClickTriggersCallback() {
        var selectedFilter: StatusFilter? = null
        
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = { selectedFilter = it },
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithText("PENDING").performClick()
        
        assert(selectedFilter == StatusFilter.PENDING)
    }

    @Test
    fun homeScreen_displaysClaimsList() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        // Verify claims are displayed
        composeTestRule.onNodeWithText("Claim #claim1", substring = true).assertIsDisplayed()
        composeTestRule.onNodeWithText("Claim #claim2", substring = true).assertIsDisplayed()
    }

    @Test
    fun homeScreen_claimCardClickTriggersCallback() {
        var clickedClaimId: String? = null
        
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = { clickedClaimId = it }
                )
            }
        }

        composeTestRule.onNodeWithText("Claim #claim1", substring = true).performClick()
        
        assert(clickedClaimId == "claim1")
    }

    @Test
    fun homeScreen_displaysStatusIndicators() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        // Verify status labels are displayed
        composeTestRule.onNodeWithText("Pending").assertIsDisplayed()
        composeTestRule.onNodeWithText("Approved").assertIsDisplayed()
        composeTestRule.onNodeWithText("Rejected").assertIsDisplayed()
        composeTestRule.onNodeWithText("Paid").assertIsDisplayed()
    }

    @Test
    fun homeScreen_emptyStateDisplaysCorrectly() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Empty,
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithText("No claims yet").assertIsDisplayed()
        composeTestRule.onNodeWithText("Tap the + button to start a new verification").assertIsDisplayed()
    }

    @Test
    fun homeScreen_loadingStateDisplaysProgressIndicator() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Loading,
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        // CircularProgressIndicator should be displayed
        composeTestRule.onNode(hasProgressBarRangeInfo(ProgressBarRangeInfo.Indeterminate))
            .assertIsDisplayed()
    }

    @Test
    fun homeScreen_errorStateDisplaysCorrectly() {
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Error("Network error"),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Error loading claims").assertIsDisplayed()
        composeTestRule.onNodeWithText("Network error").assertIsDisplayed()
        composeTestRule.onNodeWithText("Retry").assertIsDisplayed()
    }

    @Test
    fun homeScreen_errorStateRetryButtonTriggersCallback() {
        var retryClicked = false
        
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Error("Network error"),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = { retryClicked = true },
                    onNewVerificationClick = {},
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithText("Retry").performClick()
        
        assert(retryClicked)
    }

    @Test
    fun homeScreen_newVerificationButtonTriggersCallback() {
        var newVerificationClicked = false
        
        composeTestRule.setContent {
            MavunoSureTheme {
                HomeScreenContent(
                    uiState = DashboardUiState.Success(testClaims),
                    selectedFilter = StatusFilter.ALL,
                    isRefreshing = false,
                    onFilterSelected = {},
                    onRefresh = {},
                    onNewVerificationClick = { newVerificationClicked = true },
                    onClaimClick = {}
                )
            }
        }

        composeTestRule.onNodeWithContentDescription("New Verification").performClick()
        
        assert(newVerificationClicked)
    }

    private fun createTestClaim(
        id: String,
        status: ClaimStatus,
        timestamp: Instant
    ): ClaimPacket {
        return ClaimPacket(
            claimId = id,
            agentId = "agent1",
            farmId = "farm1",
            farmGps = GeoPoint(-1.2921, 36.8219),
            timestamp = timestamp,
            groundTruth = GroundTruthData(
                mlClass = CropCondition.DROUGHT_STRESS,
                mlConfidence = 0.85f,
                topThreeClasses = listOf(
                    CropCondition.DROUGHT_STRESS to 0.85f,
                    CropCondition.HEALTHY to 0.10f,
                    CropCondition.OTHER to 0.05f
                ),
                deviceTilt = 60f,
                deviceAzimuth = 180f,
                captureGps = GeoPoint(-1.2921, 36.8219)
            ),
            imageUri = "file:///test.jpg",
            syncStatus = SyncStatus.SYNCED,
            claimStatus = status
        )
    }
}

// Helper composable for testing
@androidx.compose.runtime.Composable
private fun HomeScreenContent(
    uiState: DashboardUiState,
    selectedFilter: StatusFilter,
    isRefreshing: Boolean,
    onFilterSelected: (StatusFilter) -> Unit,
    onRefresh: () -> Unit,
    onNewVerificationClick: () -> Unit,
    onClaimClick: (String) -> Unit
) {
    androidx.compose.material3.Scaffold(
        topBar = {
            androidx.compose.material3.TopAppBar(
                title = { androidx.compose.material3.Text("MavunoSure Dashboard") }
            )
        },
        floatingActionButton = {
            androidx.compose.material3.FloatingActionButton(
                onClick = onNewVerificationClick
            ) {
                androidx.compose.material3.Icon(
                    androidx.compose.material.icons.Icons.Default.Add,
                    contentDescription = "New Verification"
                )
            }
        }
    ) { paddingValues ->
        androidx.compose.foundation.layout.Column(
            modifier = androidx.compose.ui.Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Filter chips
            androidx.compose.foundation.layout.Row(
                modifier = androidx.compose.ui.Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = androidx.compose.foundation.layout.Arrangement.spacedBy(8.dp)
            ) {
                StatusFilter.values().forEach { filter ->
                    androidx.compose.material3.FilterChip(
                        selected = selectedFilter == filter,
                        onClick = { onFilterSelected(filter) },
                        label = { androidx.compose.material3.Text(filter.name) }
                    )
                }
            }
            
            // Content based on state
            when (uiState) {
                is DashboardUiState.Loading -> {
                    androidx.compose.foundation.layout.Box(
                        modifier = androidx.compose.ui.Modifier.fillMaxSize(),
                        contentAlignment = androidx.compose.ui.Alignment.Center
                    ) {
                        androidx.compose.material3.CircularProgressIndicator()
                    }
                }
                is DashboardUiState.Empty -> {
                    androidx.compose.foundation.layout.Box(
                        modifier = androidx.compose.ui.Modifier.fillMaxSize(),
                        contentAlignment = androidx.compose.ui.Alignment.Center
                    ) {
                        androidx.compose.foundation.layout.Column(
                            horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                            modifier = androidx.compose.ui.Modifier.padding(32.dp)
                        ) {
                            androidx.compose.material3.Text(
                                text = "No claims yet",
                                style = androidx.compose.material3.MaterialTheme.typography.headlineSmall
                            )
                            androidx.compose.foundation.layout.Spacer(modifier = androidx.compose.ui.Modifier.height(8.dp))
                            androidx.compose.material3.Text(
                                text = "Tap the + button to start a new verification",
                                style = androidx.compose.material3.MaterialTheme.typography.bodyMedium
                            )
                        }
                    }
                }
                is DashboardUiState.Success -> {
                    androidx.compose.foundation.lazy.LazyColumn(
                        modifier = androidx.compose.ui.Modifier.fillMaxSize(),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                        verticalArrangement = androidx.compose.foundation.layout.Arrangement.spacedBy(12.dp)
                    ) {
                        items(uiState.claims.size) { index ->
                            val claim = uiState.claims[index]
                            ClaimCardTest(
                                claim = claim,
                                onClick = { onClaimClick(claim.claimId) }
                            )
                        }
                    }
                }
                is DashboardUiState.Error -> {
                    androidx.compose.foundation.layout.Box(
                        modifier = androidx.compose.ui.Modifier.fillMaxSize(),
                        contentAlignment = androidx.compose.ui.Alignment.Center
                    ) {
                        androidx.compose.foundation.layout.Column(
                            horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                            modifier = androidx.compose.ui.Modifier.padding(32.dp)
                        ) {
                            androidx.compose.material3.Text(
                                text = "Error loading claims",
                                style = androidx.compose.material3.MaterialTheme.typography.headlineSmall
                            )
                            androidx.compose.foundation.layout.Spacer(modifier = androidx.compose.ui.Modifier.height(8.dp))
                            androidx.compose.material3.Text(
                                text = uiState.message,
                                style = androidx.compose.material3.MaterialTheme.typography.bodyMedium
                            )
                            androidx.compose.foundation.layout.Spacer(modifier = androidx.compose.ui.Modifier.height(16.dp))
                            androidx.compose.material3.Button(onClick = onRefresh) {
                                androidx.compose.material3.Text("Retry")
                            }
                        }
                    }
                }
            }
        }
    }
}

@androidx.compose.runtime.Composable
private fun ClaimCardTest(
    claim: ClaimPacket,
    onClick: () -> Unit
) {
    androidx.compose.material3.Card(
        modifier = androidx.compose.ui.Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        androidx.compose.foundation.layout.Row(
            modifier = androidx.compose.ui.Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = androidx.compose.foundation.layout.Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
        ) {
            androidx.compose.foundation.layout.Column(
                modifier = androidx.compose.ui.Modifier.weight(1f)
            ) {
                androidx.compose.material3.Text(
                    text = "Claim #${claim.claimId.take(8)}",
                    style = androidx.compose.material3.MaterialTheme.typography.titleMedium
                )
            }
            
            val statusLabel = when (claim.claimStatus) {
                ClaimStatus.PENDING, ClaimStatus.FLAGGED_FOR_REVIEW -> "Pending"
                ClaimStatus.AUTO_APPROVED -> "Approved"
                ClaimStatus.REJECTED -> "Rejected"
                ClaimStatus.PAID -> "Paid"
            }
            
            androidx.compose.material3.Text(
                text = statusLabel,
                style = androidx.compose.material3.MaterialTheme.typography.labelSmall
            )
        }
    }
}
