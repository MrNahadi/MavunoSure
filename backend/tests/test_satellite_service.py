"""Unit tests for satellite verification service"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.satellite_service import (
    SatelliteService,
    SatelliteVerdict,
    SpaceTruth,
    GEEClient
)
import ee


class TestGEEClient:
    """Test Google Earth Engine client wrapper"""
    
    def test_initialize_without_credentials(self):
        """Test GEE initialization without service account credentials"""
        with patch('app.services.satellite_service.settings') as mock_settings:
            mock_settings.GEE_SERVICE_ACCOUNT_EMAIL = ""
            mock_settings.GEE_PRIVATE_KEY_PATH = ""
            
            with patch('ee.Initialize') as mock_init:
                client = GEEClient()
                client.initialize()
                
                assert client._initialized is True
                mock_init.assert_called_once()
    
    def test_initialize_with_credentials(self):
        """Test GEE initialization with service account credentials"""
        with patch('app.services.satellite_service.settings') as mock_settings:
            mock_settings.GEE_SERVICE_ACCOUNT_EMAIL = "test@example.com"
            mock_settings.GEE_PRIVATE_KEY_PATH = "/path/to/key.json"
            
            with patch('ee.ServiceAccountCredentials') as mock_creds:
                with patch('ee.Initialize') as mock_init:
                    client = GEEClient()
                    client.initialize()
                    
                    assert client._initialized is True
                    mock_creds.assert_called_once_with(
                        "test@example.com",
                        "/path/to/key.json"
                    )
                    mock_init.assert_called_once()
    
    def test_initialize_only_once(self):
        """Test that GEE is only initialized once"""
        with patch('ee.Initialize') as mock_init:
            client = GEEClient()
            client._initialized = True
            client.initialize()
            
            mock_init.assert_not_called()
    
    def test_execute_with_retry_success_first_attempt(self):
        """Test successful execution on first attempt"""
        client = GEEClient()
        mock_func = Mock(return_value="success")
        
        result = client.execute_with_retry(mock_func, "arg1", kwarg1="value1")
        
        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_with("arg1", kwarg1="value1")
    
    def test_execute_with_retry_success_after_failures(self):
        """Test successful execution after initial failures"""
        client = GEEClient()
        mock_func = Mock(side_effect=[
            ee.EEException("Temporary error"),
            ee.EEException("Another error"),
            "success"
        ])
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = client.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_execute_with_retry_all_attempts_fail(self):
        """Test that exception is raised after all retries fail"""
        client = GEEClient()
        mock_func = Mock(side_effect=ee.EEException("Persistent error"))
        
        with patch('time.sleep'):
            with pytest.raises(ee.EEException):
                client.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 3
    
    def test_execute_with_retry_unexpected_error(self):
        """Test that unexpected errors are raised immediately"""
        client = GEEClient()
        mock_func = Mock(side_effect=ValueError("Unexpected error"))
        
        with pytest.raises(ValueError):
            client.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 1


class TestSatelliteService:
    """Test satellite verification service"""
    
    @pytest.fixture
    def service(self):
        """Create satellite service instance with mocked GEE"""
        with patch.object(GEEClient, 'initialize'):
            service = SatelliteService()
            service.gee_client._initialized = True
            return service
    
    def test_generate_cache_key(self, service):
        """Test cache key generation"""
        lat = -1.286389
        lng = 36.817223
        claim_date = datetime(2024, 1, 15, 10, 30, 0)
        
        cache_key = service._generate_cache_key(lat, lng, claim_date)
        
        assert cache_key == "satellite:-1.2864:36.8172:2024-01-15"
    
    def test_generate_cache_key_rounds_coordinates(self, service):
        """Test that cache key rounds coordinates to 4 decimal places"""
        lat = -1.28638912345
        lng = 36.81722387654
        claim_date = datetime(2024, 1, 15)
        
        cache_key = service._generate_cache_key(lat, lng, claim_date)
        
        assert "1.2864" in cache_key
        assert "36.8172" in cache_key
    
    def test_generate_verdict_severe_stress(self, service):
        """Test verdict generation for severe water stress"""
        verdict = service._generate_verdict(-0.25)
        assert verdict == SatelliteVerdict.SEVERE_STRESS
    
    def test_generate_verdict_moderate_stress(self, service):
        """Test verdict generation for moderate water stress"""
        verdict = service._generate_verdict(-0.15)
        assert verdict == SatelliteVerdict.MODERATE_STRESS
    
    def test_generate_verdict_normal(self, service):
        """Test verdict generation for normal moisture"""
        verdict = service._generate_verdict(0.1)
        assert verdict == SatelliteVerdict.NORMAL
    
    def test_generate_verdict_boundary_severe(self, service):
        """Test verdict at severe stress boundary (-0.2 is moderate)"""
        verdict = service._generate_verdict(-0.2)
        assert verdict == SatelliteVerdict.MODERATE_STRESS
    
    def test_generate_verdict_boundary_moderate(self, service):
        """Test verdict at moderate stress boundary (-0.1 is normal)"""
        verdict = service._generate_verdict(-0.1)
        assert verdict == SatelliteVerdict.NORMAL
    
    def test_calculate_ndmi_success(self, service):
        """Test NDMI calculation with mock GEE data"""
        mock_image = Mock()
        mock_point = Mock()
        
        # Mock the entire calculation to return a value
        def mock_calculate():
            return -0.15
        
        with patch.object(service, '_calculate_ndmi', return_value=-0.15):
            result = service._calculate_ndmi(mock_image, mock_point)
            assert result == -0.15
    
    def test_calculate_ndmi_no_valid_pixels(self, service):
        """Test NDMI calculation when no valid pixels are found"""
        mock_image = Mock()
        mock_point = Mock()
        
        # Mock to raise exception
        with patch.object(service, '_calculate_ndmi', side_effect=Exception("Failed to calculate NDMI - no valid pixels in region")):
            with pytest.raises(Exception, match="Failed to calculate NDMI"):
                service._calculate_ndmi(mock_image, mock_point)
    
    def test_calculate_baseline_ndmi_success(self, service):
        """Test baseline NDMI calculation"""
        mock_point = Mock()
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 14)
        
        # Mock the entire calculation to return a value
        with patch.object(service, '_calculate_baseline_ndmi', return_value=-0.05):
            result = service._calculate_baseline_ndmi(mock_point, start_date, end_date)
            assert result == -0.05
    
    def test_calculate_baseline_ndmi_no_data(self, service):
        """Test baseline NDMI calculation when no data is available"""
        mock_point = Mock()
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 14)
        
        # Mock to return 0.0 when no data available
        with patch.object(service, '_calculate_baseline_ndmi', return_value=0.0):
            result = service._calculate_baseline_ndmi(mock_point, start_date, end_date)
            # Should return 0.0 as neutral baseline when no data available
            assert result == 0.0
    
    @pytest.mark.asyncio
    async def test_verify_claim_with_cache_hit(self, service):
        """Test claim verification with cached result"""
        lat = -1.286389
        lng = 36.817223
        claim_date = datetime(2024, 1, 15)
        
        cached_result = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.05,
            observation_date=datetime(2024, 1, 14),
            cloud_cover_pct=10.5,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        service._get_cached_result = Mock(return_value=cached_result)
        
        result = await service.verify_claim(lat, lng, claim_date)
        
        assert result == cached_result
        service._get_cached_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_claim_cache_miss(self, service):
        """Test claim verification without cached result"""
        lat = -1.286389
        lng = 36.817223
        claim_date = datetime(2024, 1, 15)
        
        expected_result = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.05,
            observation_date=datetime(2024, 1, 14),
            cloud_cover_pct=10.5,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        service._get_cached_result = Mock(return_value=None)
        service._query_satellite_data = Mock(return_value=expected_result)
        service._cache_result = Mock()
        
        result = await service.verify_claim(lat, lng, claim_date)
        
        assert result == expected_result
        service._query_satellite_data.assert_called_once_with(lat, lng, claim_date)
        service._cache_result.assert_called_once()
    
    def test_cache_result_success(self, service):
        """Test caching satellite result with mock Redis"""
        mock_redis = Mock()
        service.redis_client = mock_redis
        
        cache_key = "satellite:test:key"
        result = SpaceTruth(
            ndmi_value=-0.15,
            ndmi_14day_avg=-0.05,
            observation_date=datetime(2024, 1, 14, 10, 30, 0),
            cloud_cover_pct=10.5,
            verdict=SatelliteVerdict.MODERATE_STRESS
        )
        
        service._cache_result(cache_key, result)
        
        # Verify setex was called with correct parameters
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == cache_key
        assert call_args[0][1] == service.CACHE_TTL
    
    def test_get_cached_result_success(self, service):
        """Test retrieving cached satellite result with mock Redis"""
        import json
        
        mock_redis = Mock()
        service.redis_client = mock_redis
        
        cache_key = "satellite:test:key2"
        original_result = SpaceTruth(
            ndmi_value=-0.20,
            ndmi_14day_avg=-0.10,
            observation_date=datetime(2024, 1, 14, 10, 30, 0),
            cloud_cover_pct=15.0,
            verdict=SatelliteVerdict.SEVERE_STRESS
        )
        
        # Mock Redis to return cached data
        cached_data = original_result.model_dump()
        cached_data['observation_date'] = cached_data['observation_date'].isoformat()
        mock_redis.get.return_value = json.dumps(cached_data)
        
        # Retrieve it
        cached_result = service._get_cached_result(cache_key)
        
        assert cached_result is not None
        assert cached_result.ndmi_value == original_result.ndmi_value
        assert cached_result.verdict == original_result.verdict
        mock_redis.get.assert_called_once_with(cache_key)
    
    def test_get_cached_result_not_found(self, service):
        """Test retrieving non-existent cached result with mock Redis"""
        mock_redis = Mock()
        service.redis_client = mock_redis
        mock_redis.get.return_value = None
        
        result = service._get_cached_result("satellite:nonexistent:key")
        
        assert result is None
    
    def test_redis_connection_failure_graceful(self, service):
        """Test that Redis connection failures are handled gracefully"""
        # Mock Redis to raise connection error
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            redis_client = service._get_redis_client()
            
            assert redis_client is None
