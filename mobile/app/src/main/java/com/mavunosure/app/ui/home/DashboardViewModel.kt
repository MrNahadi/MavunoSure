package com.mavunosure.app.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mavunosure.app.domain.model.ClaimPacket
import com.mavunosure.app.domain.model.ClaimStatus
import com.mavunosure.app.domain.repository.ClaimRepository
import com.mavunosure.app.domain.repository.OfflineQueueRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val claimRepository: ClaimRepository,
    private val offlineQueueRepository: OfflineQueueRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<DashboardUiState>(DashboardUiState.Loading)
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()
    
    private val _selectedFilter = MutableStateFlow<StatusFilter>(StatusFilter.ALL)
    val selectedFilter: StateFlow<StatusFilter> = _selectedFilter.asStateFlow()
    
    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()
    
    init {
        loadClaims()
    }
    
    fun loadClaims() {
        viewModelScope.launch {
            claimRepository.observeAllClaims()
                .combine(selectedFilter) { claims, filter ->
                    filterClaims(claims, filter)
                }
                .catch { e ->
                    _uiState.value = DashboardUiState.Error(e.message ?: "Unknown error")
                    _isRefreshing.value = false
                }
                .collect { filteredClaims ->
                    _uiState.value = if (filteredClaims.isEmpty()) {
                        DashboardUiState.Empty
                    } else {
                        DashboardUiState.Success(filteredClaims)
                    }
                    _isRefreshing.value = false
                }
        }
    }
    
    fun setFilter(filter: StatusFilter) {
        _selectedFilter.value = filter
    }
    
    fun refreshClaims() {
        viewModelScope.launch {
            _isRefreshing.value = true
            try {
                // Sync claims from backend to get latest statuses
                claimRepository.syncClaimsFromBackend()
                
                // Also sync pending claims that haven't been uploaded yet
                val pendingClaims = offlineQueueRepository.getPendingClaims()
                pendingClaims.forEach { claim ->
                    offlineQueueRepository.syncClaim(claim.claimId)
                }
            } catch (e: Exception) {
                // Sync errors are handled in the repository
            } finally {
                _isRefreshing.value = false
            }
        }
    }
    
    private fun filterClaims(claims: List<ClaimPacket>, filter: StatusFilter): List<ClaimPacket> {
        return when (filter) {
            StatusFilter.ALL -> claims
            StatusFilter.PENDING -> claims.filter { 
                it.claimStatus == ClaimStatus.PENDING || 
                it.claimStatus == ClaimStatus.FLAGGED_FOR_REVIEW 
            }
            StatusFilter.APPROVED -> claims.filter { 
                it.claimStatus == ClaimStatus.AUTO_APPROVED 
            }
            StatusFilter.REJECTED -> claims.filter { 
                it.claimStatus == ClaimStatus.REJECTED 
            }
            StatusFilter.PAID -> claims.filter { 
                it.claimStatus == ClaimStatus.PAID 
            }
        }.sortedByDescending { it.timestamp }
    }
}

sealed class DashboardUiState {
    object Loading : DashboardUiState()
    object Empty : DashboardUiState()
    data class Success(val claims: List<ClaimPacket>) : DashboardUiState()
    data class Error(val message: String) : DashboardUiState()
}

enum class StatusFilter {
    ALL, PENDING, APPROVED, REJECTED, PAID
}
