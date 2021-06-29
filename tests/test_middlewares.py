"""This module contains the test cases for the middlewares of the ``scrapy_selenium`` package"""

from unittest.mock import patch
from contextlib import ExitStack

from scrapy import Request
from scrapy.crawler import Crawler

from scrapy_selenium.http import SeleniumRequest
from scrapy_selenium.middlewares import SeleniumMiddleware

from .test_cases import BaseScrapySeleniumTestCase


class SeleniumMiddlewareTestCase(BaseScrapySeleniumTestCase):
    """Test case for the ``SeleniumMiddleware`` middleware"""

    @classmethod
    def setUpClass(cls):
        """Initialize the middleware"""

        super().setUpClass()

        crawler = Crawler(
            spidercls=cls.spider_klass,
            settings=cls.settings
        )

        cls.selenium_middleware = SeleniumMiddleware.from_crawler(crawler)

    @classmethod
    def tearDownClass(cls):
        """Close the selenium webdriver"""

        super().tearDownClass()

        while not(cls.selenium_middleware.driver_queue.empty()):
            cls.selenium_middleware.driver_queue.get().quit()

    def test_from_crawler_method_should_initialize_the_driver(self):
        """Test that the ``from_crawler`` method should initialize the selenium driver"""

        crawler = Crawler(
            spidercls=self.spider_klass,
            settings=self.settings
        )

        selenium_middleware = SeleniumMiddleware.from_crawler(crawler)

        # The driver_queue must be initialized
        self.assertIsNotNone(selenium_middleware.driver_queue)
        # Each driver in the queue must be initialized:
        for i in range(0,selenium_middleware.driver_queue.qsize()):
            # queue is FIFO, so this should test all of them.
            driver = selenium_middleware.driver_queue.get()
            self.assertIsNotNone(driver)
            selenium_middleware.driver_queue.put(driver)

        # Test all of the drivers in the queue
        for i in range(0, selenium_middleware.driver_queue.qsize()):
            driver = selenium_middleware.driver_queue.get()
            driver.get('http://www.python.org')
            self.assertIsNotNone(driver)
            self.assertIn('Python', driver.title)
            selenium_middleware.driver_queue.put(driver)

        for i in range(0, selenium_middleware.driver_queue.qsize()):
            driver = selenium_middleware.driver_queue.get()
            driver.close()

    def test_spider_closed_should_close_the_driver(self):
        """Test that the ``spider_closed`` method should close the driver"""

        crawler = Crawler(
            spidercls=self.spider_klass,
            settings=self.settings
        )

        selenium_middleware = SeleniumMiddleware.from_crawler(crawler)

        with ExitStack() as stack:
            mocked_quits = []
            for i in range(0, selenium_middleware.driver_queue.qsize()):
                mocked_quits.append(stack.enter_context(patch.object(selenium_middleware.driver_queue.get(), 'quit')))
            selenium_middleware.spider_closed()

        for mocked_quit in mocked_quits:
            mocked_quit.assert_called_once()

    def test_process_request_should_return_none_if_not_selenium_request(self):
        """Test that the ``process_request`` should return none if not selenium request"""

        scrapy_request = Request(url='http://not-an-url')

        self.assertIsNone(
            self.selenium_middleware.process_request(
                request=scrapy_request,
                spider=None
            )
        )

    def test_process_request_should_return_a_response_if_selenium_request(self):
        """Test that the ``process_request`` should return a response if selenium request"""

        selenium_request = SeleniumRequest(url='http://www.python.org')

        html_response = self.selenium_middleware.process_request(
            request=selenium_request,
            spider=None
        )

        # The driver assigned to this request is no longer in the driver queue
        self.assertNotIn(
            html_response.meta['driver'],
            self.selenium_middleware.driver_queue
        )

        # We also have access to the "selector" attribute on the response
        self.assertEqual(
            html_response.selector.xpath('//title/text()').extract_first(),
            'Welcome to Python.org'
        )

    def test_process_request_should_return_a_screenshot_if_screenshot_option(self):
        """Test that the ``process_request`` should return a response with a screenshot"""

        selenium_request = SeleniumRequest(
            url='http://www.python.org',
            screenshot=True
        )

        html_response = self.selenium_middleware.process_request(
            request=selenium_request,
            spider=None
        )

        self.assertIsNotNone(html_response.meta['screenshot'])

    def test_process_request_should_execute_script_if_script_option(self):
        """Test that the ``process_request`` should execute the script and return a response"""

        selenium_request = SeleniumRequest(
            url='http://www.python.org',
            script='document.title = "scrapy_selenium";'
        )

        html_response = self.selenium_middleware.process_request(
            request=selenium_request,
            spider=None
        )

        self.assertEqual(
            html_response.selector.xpath('//title/text()').extract_first(),
            'scrapy_selenium'
        )
