import unittest
import time
from unittest.mock import MagicMock, patch

from crawv.middleware.adaptive_concurrency import AdaptiveConcurrencyMiddleware


class TestAdaptiveConcurrencyMiddleware(unittest.TestCase):
    """Test the AdaptiveConcurrencyMiddleware."""

    def setUp(self):
        # Create mocks
        self.crawler = MagicMock()
        self.crawler.settings = {
            'ADAPTIVE_CONCURRENCY_ENABLED': True,
            'ADAPTIVE_CONCURRENCY_TARGET_RESPONSE_TIME': 0.5,
            'ADAPTIVE_CONCURRENCY_MIN_REQUESTS': 5,
            'ADAPTIVE_CONCURRENCY_MAX_REQUESTS': 20,
            'ADAPTIVE_CONCURRENCY_WINDOW_SIZE': 10,
            'ADAPTIVE_CONCURRENCY_ADJUSTMENT_INTERVAL': 1,
            'CONCURRENT_REQUESTS': 10,
        }
        self.crawler.settings.getbool = lambda key, default: self.crawler.settings.get(key, default)
        self.crawler.settings.getfloat = lambda key, default: self.crawler.settings.get(key, default)
        self.crawler.settings.getint = lambda key, default: self.crawler.settings.get(key, default)
        
        self.spider = MagicMock()
        self.spider.name = 'test_spider'
        
        # Create middleware
        self.middleware = AdaptiveConcurrencyMiddleware(self.crawler)
        self.middleware.logger = MagicMock()
        
        # Create request and response mocks
        self.request = MagicMock()
        self.request.meta = {}
        self.response = MagicMock()

    async def test_process_request_adds_start_time(self):
        """Test that process_request adds a start time to the request meta."""
        result = await self.middleware.process_request(self.request, self.spider)
        
        # Verify that the result is None (middleware continues)
        self.assertIsNone(result)
        
        # Verify that a start time was added to the request meta
        self.assertIn('request_start_time', self.request.meta)
        self.assertIsInstance(self.request.meta['request_start_time'], float)

    async def test_process_response_calculates_time(self):
        """Test that process_response calculates the response time."""
        # Set up a request with a start time
        start_time = time.time() - 0.3  # 300ms ago
        self.request.meta['request_start_time'] = start_time
        
        result = await self.middleware.process_response(self.request, self.response, self.spider)
        
        # Verify that the result is the response
        self.assertEqual(result, self.response)
        
        # Verify that a response time was added to the deque
        self.assertEqual(len(self.middleware.response_times), 1)
        self.assertGreaterEqual(self.middleware.response_times[0], 0.3)

    async def test_adjust_concurrency_faster_responses(self):
        """Test that concurrency is increased when responses are faster than target."""
        # Fill the response times deque with fast responses (0.2s)
        self.middleware.response_times.extend([0.2] * self.middleware.window_size)
        self.middleware.current_concurrency = 10
        
        # Adjust concurrency
        self.middleware._adjust_concurrency()
        
        # Verify that concurrency was increased
        self.assertGreater(self.middleware.current_concurrency, 10)
        
