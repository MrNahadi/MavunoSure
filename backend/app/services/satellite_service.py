"""Satellite verification service using Google Earth Engine"""

import ee
import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from app.config import settings
import logging
import time

logger = logging.getLogger(__name__)


class SatelliteVerdict(str, Enum):
    """Satellite-based crop stress verdict"""
    SEVERE_STRESS = "severe_stress"
    MODERATE_STRESS = "moderate_stress"
    NORMAL = "normal"


class SpaceTruth(BaseModel):
    """Space Truth data from satellite imagery"""
    ndmi_value: float
    ndmi_14day_avg: float
    observation_date: datetime
    cloud_cover_pct: float
    verdict: SatelliteVerdict


class GEEClient:
    """Google Earth Engine client wrapper with connection pooling and error handling"""
    
    def __init__(self):
        self._initialized = False
        self._max_retries = 3
        self._retry_delay = 2  # seconds
    
    def initialize(self) -> None:
        """
        Initialize Google Earth Engine with service account authentication
        
        Raises:
            Exception: If GEE initialization fails
        """
        if self._initialized:
            return
        
        try:
            # Check if credentials are configured
            if not settings.GEE_SERVICE_ACCOUNT_EMAIL or not settings.GEE_PRIVATE_KEY_PATH:
                logger.warning("GEE credentials not configured, using default authentication")
                ee.Initialize()
            else:
                # Use service account authentication
                credentials = ee.ServiceAccountCredentials(
                    settings.GEE_SERVICE_ACCOUNT_EMAIL,
                    settings.GEE_PRIVATE_KEY_PATH
                )
                ee.Initialize(credentials)
            
            self._initialized = True
            logger.info("Google Earth Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Earth Engine: {str(e)}")
            raise
    
    def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Execute a GEE function with retry logic
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function execution
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self._max_retries):
            try:
                return func(*args, **kwargs)
            except ee.EEException as e:
                last_exception = e
                logger.warning(
                    f"GEE API call failed (attempt {attempt + 1}/{self._max_retries}): {str(e)}"
                )
                
                if attempt < self._max_retries - 1:
                    # Exponential backoff
                    delay = self._retry_delay * (2 ** attempt)
                    time.sleep(delay)
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in GEE API call: {str(e)}")
                raise
        
        # All retries failed
        logger.error(f"All {self._max_retries} retry attempts failed")
        raise last_exception


class SatelliteService:
    """Service for satellite-based crop verification"""
    
    # Sentinel-2 collection ID
    SENTINEL2_COLLECTION = 'COPERNICUS/S2_SR_HARMONIZED'
    
    # Cloud cover threshold
    MAX_CLOUD_COVER = 20.0
    
    # Date range for recent imagery (days)
    RECENT_IMAGE_DAYS = 3
    
    # Date range for baseline (days)
    BASELINE_START_DAYS = 17
    BASELINE_END_DAYS = 3
    
    # Buffer radius for sampling (meters)
    SAMPLE_BUFFER = 50
    
    # Sentinel-2 spatial resolution (meters)
    SPATIAL_SCALE = 20
    
    # Cache TTL (seconds) - 24 hours
    CACHE_TTL = 86400
    
    def __init__(self):
        self.gee_client = GEEClient()
        self.redis_client = None
        
        # Initialize GEE
        try:
            self.gee_client.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize GEE client: {str(e)}")
    
    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client for caching"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {str(e)}")
                return None
        
        return self.redis_client
    
    def _generate_cache_key(self, lat: float, lng: float, claim_date: datetime) -> str:
        """
        Generate cache key based on GPS coordinates and date
        
        Args:
            lat: Latitude
            lng: Longitude
            claim_date: Claim date
            
        Returns:
            Cache key string
        """
        # Round coordinates to 4 decimal places (~11m precision)
        lat_rounded = round(lat, 4)
        lng_rounded = round(lng, 4)
        date_str = claim_date.strftime('%Y-%m-%d')
        
        key_string = f"satellite:{lat_rounded}:{lng_rounded}:{date_str}"
        return key_string
    
    def _get_cached_result(self, cache_key: str) -> Optional[SpaceTruth]:
        """
        Get cached satellite result
        
        Args:
            cache_key: Cache key
            
        Returns:
            SpaceTruth if cached, None otherwise
        """
        redis_client = self._get_redis_client()
        if redis_client is None:
            return None
        
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Convert observation_date string back to datetime
                data['observation_date'] = datetime.fromisoformat(data['observation_date'])
                return SpaceTruth(**data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached result: {str(e)}")
        
        return None
    
    def _cache_result(self, cache_key: str, result: SpaceTruth) -> None:
        """
        Cache satellite result
        
        Args:
            cache_key: Cache key
            result: SpaceTruth to cache
        """
        redis_client = self._get_redis_client()
        if redis_client is None:
            return
        
        try:
            # Convert to dict and handle datetime serialization
            data = result.model_dump()
            data['observation_date'] = data['observation_date'].isoformat()
            
            redis_client.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to cache result: {str(e)}")
    
    async def verify_claim(
        self,
        lat: float,
        lng: float,
        claim_date: datetime
    ) -> SpaceTruth:
        """
        Verify claim using satellite data
        
        Args:
            lat: Farm latitude
            lng: Farm longitude
            claim_date: Date of claim submission
            
        Returns:
            SpaceTruth with satellite verification data
            
        Raises:
            Exception: If satellite verification fails
        """
        # Check cache first
        cache_key = self._generate_cache_key(lat, lng, claim_date)
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result:
            logger.info(f"Using cached satellite data for {cache_key}")
            return cached_result
        
        # Query satellite data
        logger.info(f"Querying satellite data for lat={lat}, lng={lng}, date={claim_date}")
        
        try:
            result = self._query_satellite_data(lat, lng, claim_date)
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Satellite verification failed: {str(e)}")
            raise
    
    def _query_satellite_data(
        self,
        lat: float,
        lng: float,
        claim_date: datetime
    ) -> SpaceTruth:
        """
        Query Google Earth Engine for satellite data and calculate NDMI
        
        Args:
            lat: Farm latitude
            lng: Farm longitude
            claim_date: Date of claim submission
            
        Returns:
            SpaceTruth with NDMI values and verdict
            
        Raises:
            Exception: If no suitable imagery is found or calculation fails
        """
        # Create point geometry
        point = ee.Geometry.Point([lng, lat])
        
        # Define date ranges
        recent_start = claim_date - timedelta(days=self.RECENT_IMAGE_DAYS)
        recent_end = claim_date + timedelta(days=self.RECENT_IMAGE_DAYS)
        baseline_start = claim_date - timedelta(days=self.BASELINE_START_DAYS)
        baseline_end = claim_date - timedelta(days=self.BASELINE_END_DAYS)
        
        # Query recent image with retry logic
        def get_recent_image():
            collection = ee.ImageCollection(self.SENTINEL2_COLLECTION) \
                .filterBounds(point) \
                .filterDate(recent_start.isoformat(), recent_end.isoformat()) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.MAX_CLOUD_COVER)) \
                .sort('CLOUDY_PIXEL_PERCENTAGE')
            
            # Get the first (least cloudy) image
            image = collection.first()
            
            # Check if image exists
            image_info = image.getInfo()
            if image_info is None:
                raise Exception(
                    f"No suitable Sentinel-2 imagery found for location ({lat}, {lng}) "
                    f"between {recent_start.date()} and {recent_end.date()} "
                    f"with cloud cover < {self.MAX_CLOUD_COVER}%"
                )
            
            return image
        
        recent_image = self.gee_client.execute_with_retry(get_recent_image)
        
        # Calculate NDMI for recent image
        ndmi_value = self._calculate_ndmi(recent_image, point)
        
        # Get image metadata
        def get_image_metadata():
            return recent_image.getInfo()
        
        image_metadata = self.gee_client.execute_with_retry(get_image_metadata)
        
        observation_date = datetime.fromtimestamp(
            image_metadata['properties']['system:time_start'] / 1000
        )
        cloud_cover_pct = image_metadata['properties']['CLOUDY_PIXEL_PERCENTAGE']
        
        # Calculate 14-day baseline NDMI
        ndmi_14day_avg = self._calculate_baseline_ndmi(point, baseline_start, baseline_end)
        
        # Generate verdict
        verdict = self._generate_verdict(ndmi_value)
        
        return SpaceTruth(
            ndmi_value=ndmi_value,
            ndmi_14day_avg=ndmi_14day_avg,
            observation_date=observation_date,
            cloud_cover_pct=cloud_cover_pct,
            verdict=verdict
        )
    
    def _calculate_ndmi(self, image: ee.Image, point: ee.Geometry.Point) -> float:
        """
        Calculate NDMI (Normalized Difference Moisture Index) for an image
        
        NDMI = (B8A - B11) / (B8A + B11)
        where B8A is NIR narrow band and B11 is SWIR band
        
        Args:
            image: Sentinel-2 image
            point: Point geometry for sampling
            
        Returns:
            NDMI value (typically ranges from -1 to 1)
        """
        def calculate():
            # Calculate NDMI using normalized difference
            ndmi = image.normalizedDifference(['B8A', 'B11'])
            
            # Sample NDMI value at the point with buffer
            ndmi_value = ndmi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(self.SAMPLE_BUFFER),
                scale=self.SPATIAL_SCALE,
                maxPixels=1e9
            ).get('nd')
            
            # Get the value
            result = ndmi_value.getInfo()
            
            if result is None:
                raise Exception("Failed to calculate NDMI - no valid pixels in region")
            
            return float(result)
        
        return self.gee_client.execute_with_retry(calculate)
    
    def _calculate_baseline_ndmi(
        self,
        point: ee.Geometry.Point,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calculate 14-day moving average NDMI for baseline comparison
        
        Args:
            point: Point geometry for sampling
            start_date: Start date for baseline period
            end_date: End date for baseline period
            
        Returns:
            Average NDMI value over the baseline period
        """
        def calculate():
            # Get collection for baseline period
            collection = ee.ImageCollection(self.SENTINEL2_COLLECTION) \
                .filterBounds(point) \
                .filterDate(start_date.isoformat(), end_date.isoformat()) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.MAX_CLOUD_COVER))
            
            # Calculate NDMI for each image
            def calc_ndmi(image):
                return image.normalizedDifference(['B8A', 'B11'])
            
            ndmi_collection = collection.map(calc_ndmi)
            
            # Calculate mean NDMI across all images
            mean_ndmi = ndmi_collection.mean()
            
            # Sample at the point
            ndmi_value = mean_ndmi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(self.SAMPLE_BUFFER),
                scale=self.SPATIAL_SCALE,
                maxPixels=1e9
            ).get('nd')
            
            result = ndmi_value.getInfo()
            
            if result is None:
                # If no baseline data available, return 0 as neutral baseline
                logger.warning(
                    f"No baseline imagery found for period {start_date.date()} to {end_date.date()}"
                )
                return 0.0
            
            return float(result)
        
        return self.gee_client.execute_with_retry(calculate)
    
    def _generate_verdict(self, ndmi_value: float) -> SatelliteVerdict:
        """
        Generate satellite verdict based on NDMI value
        
        NDMI interpretation:
        - < -0.2: Severe water stress
        - -0.2 to < -0.1: Moderate water stress
        - >= -0.1: Normal moisture levels
        
        Args:
            ndmi_value: NDMI value
            
        Returns:
            SatelliteVerdict
        """
        if ndmi_value < -0.2:
            return SatelliteVerdict.SEVERE_STRESS
        elif ndmi_value < -0.1:
            return SatelliteVerdict.MODERATE_STRESS
        else:
            return SatelliteVerdict.NORMAL


# Singleton instance
satellite_service = SatelliteService()
