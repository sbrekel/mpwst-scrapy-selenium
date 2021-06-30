"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""

from importlib import import_module
from queue import Queue
import time

from scrapy import signals
from scrapy.exceptions import NotConfigured
from selenium.webdriver.support.ui import WebDriverWait

from .http import SeleniumRequest, SeleniumHtmlResponse


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path,
                 browser_executable_path, command_executor, driver_arguments, max_driver_instances):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        command_executor: str
            Selenium remote server endpoint
        """

        webdriver_base_path = f'selenium.webdriver.{driver_name}'

        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()

        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        driver_kwargs = {
            'executable_path': driver_executable_path,
            f'{driver_name}_options': driver_options
        }

        self.driver_queue = Queue(maxsize=max_driver_instances)

        # locally installed driver
        if driver_executable_path is not None:
            driver_kwargs = {
                'executable_path': driver_executable_path,
                f'{driver_name}_options': driver_options
            }
            for i in range(0, max_driver_instances):
                self.driver_queue.put(driver_klass(**driver_kwargs))        # remote driver
        elif command_executor is not None:
            from selenium import webdriver
            capabilities = driver_options.to_capabilities()
            for i in range(0, max_driver_instances):
                self.driver_queue.put(webdriver.Remote(command_executor=command_executor,
                                                       desired_capabilities=capabilities))

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        command_executor = crawler.settings.get('SELENIUM_COMMAND_EXECUTOR')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')
        concurrent_requests = crawler.settings.get('CONCURRENT_REQUESTS')
        max_driver_instances = crawler.settings.get('SELENIUM_MAX_INSTANCES')

        if max_driver_instances is None:
            max_driver_instances = concurrent_requests  # if not specified, num browsers = num concurrent requests

        if driver_name is None:
            raise NotConfigured('SELENIUM_DRIVER_NAME must be set')

        if driver_executable_path is None and command_executor is None:
            raise NotConfigured('Either SELENIUM_DRIVER_EXECUTABLE_PATH '
                                'or SELENIUM_COMMAND_EXECUTOR must be set')

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            browser_executable_path=browser_executable_path,
            command_executor=command_executor,
            driver_arguments=driver_arguments,
            max_driver_instances=max_driver_instances
        )

        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if not isinstance(request, SeleniumRequest):
            return None
        driver = self.driver_queue.get()

        try:
            user_agent = request.headers['User-Agent'].decode('utf-8')  # take user-agent from scrapy
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
        except AttributeError:
            spider.logger.info('Cannot set selenium user agent. Currently, this is only implemented for chromedriver. Are you using Chrome?')

        driver.get(request.url)

        for cookie_name, cookie_value in request.cookies.items():
            driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': cookie_value
                }
            )

        if request.wait_until:
            WebDriverWait(driver, request.wait_time).until(
                request.wait_until
            )

        if request.wait_sleep:
            time.sleep(request.wait_sleep)

        if request.screenshot:
            request.meta['screenshot'] = driver.get_screenshot_as_png()

        if request.script:
            driver.execute_script(request.script)

        body = str.encode(driver.page_source)

        # Expose the driver and middleware via the "meta" attribute
        #  the latter to allow sipder parse() to release the driver
        #  and return it to the driver_queue
        request.meta.update({'driver': driver})
        request.meta.update({'middleware': self})

        return SeleniumHtmlResponse(
            url=driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""
        while not(self.driver_queue.empty()):
            self.driver_queue.get().quit()
