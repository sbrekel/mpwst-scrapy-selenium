"""This module contains the ``SeleniumRequest`` class"""

from scrapy import Request
from scrapy.http import HtmlResponse
import logging

logger = logging.getLogger(__name__)

class SeleniumRequest(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    def __init__(self, wait_time=None, wait_until=None, wait_sleep=None, screenshot=False,
                 script=None, *args, **kwargs):
        """Initialize a new selenium request

        Parameters
        ----------
        wait_time: int
            The number of seconds to wait.
        wait_until: method
            One of the "selenium.webdriver.support.expected_conditions". The response
            will be returned until the given condition is fulfilled.
        screenshot: bool
            If True, a screenshot of the page will be taken and the data of the screenshot
            will be returned in the response "meta" attribute.
        script: str
            JavaScript code to execute.

        """

        self.wait_time = wait_time
        self.wait_until = wait_until
        self.wait_sleep = wait_sleep
        self.screenshot = screenshot
        self.script = script

        super().__init__(*args, **kwargs)

    def release_driver(self):
        middleware = self.meta['middleware']
        driver = self.meta['driver']
        if driver:
            driver.get('about:blank')  # get a blank tab -- ensures next request using driver won't have "stale" content
            middleware.driver_queue.put(driver)
            logger.debug(f'Returned driver to the queue ({middleware.driver_queue.qsize()} drivers available)')
            del self.meta['driver']


class SeleniumHtmlResponse(HtmlResponse):

    def refresh(self):
        driver = self.request.meta['driver']
        response = self.replace(
            url=driver.current_url,
            body=str.encode(driver.page_source),
            encoding='utf-8',
            request=self.request
        )
        return response

    def get_screenshot(self):
        driver = self.request.meta['driver']
        return driver.get_screenshot_as_png()

    def release_driver(self):
        self.request.release_driver()
