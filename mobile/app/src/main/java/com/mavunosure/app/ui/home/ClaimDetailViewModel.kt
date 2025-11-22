package com.mavunosure.app.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mavunosure.app.domain.model.ClaimPacket
import com.mavunosure.app.domain.repository.OfflineQueueRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ClaimDetailViewModel @Inject constructor(
    private val offlineQueueRepository: OfflineQueueRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<ClaimDetailUiState>(ClaimDetailUiState.Loading)
    val uiState: StateFlow<ClaimDetailUiState> = _uiState.asStateFlow()
    
    fun loadClaim(claimId: String) {
        viewModelScope.launch {
            _uiState.value = ClaimDetailUiState.Loading
            try {
                offlineQueueRepository.observeAllClaims()
                    .collect { claims ->
                        val claim = claims.find { it.claimId == claimId }
                        _uiState.value = if (claim != null) {
                            ClaimDetailUiState.Success(claim)
                        } else {
                            ClaimDetailUiState.Error("Claim not found")
                        }
                    }
            } catch (e: Exception) {
                _uiState.value = ClaimDetailUiState.Error(e.message ?: "Unknown error")
            }
        }
    }
}

sealed class ClaimDetailUiState {
    object Loading : ClaimDetailUiState()
    data class Success(val claim: ClaimPacket) : ClaimDetailUiState()
    data class Error(val message: String) : ClaimDetailUiState()
}
