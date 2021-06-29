# Better Scrapy Selenium Middleware

## Why Fork Scrapy Selenium
Scrapy is a great scraping tool. But in most of the modern scraping tasks I've faced, I find that I need a tool that can
render javascript with dynamic loading and even **interact dynamically with a page**.
Selenium is great for this, so surely someone has made a selenium-scrapy sandwich, right?  The [official Scrapy documentation recommends scrapy_selenium library](https://docs.scrapy.org/en/latest/topics/dynamic-content.html#using-a-headless-browser). 
This sounds like a match made in heaven. So why not just use selenium-scrapy and call it a day?

The architectural idea behind scrapy is that the two tasks are not interdependent:
1) getting a page
2) parsing the information you want to scrape from a page

Given the async nature of scrapy, (1) and (2) are separate and can happen concurrently (`CONCURRENT_REQUESTS`) for different pages you scrape.
Selenium-scrapy is a scrapy downloader middleware that invokes **a single selenium webdriver** to get and render pages,
and then return the rendered response. But what about cases when tasks (1) and (2) aren't so separable? What if your parse function
needs to use the selenium webdriver to interact with the page? Scrapy-selenium permits this by saving the selenium webdriver in the meta
dictionary of request (`response.request.meta['driver']`). 

What this means, is that the state of the selenium webdriver can be affected by other requests while your parse function is running.
This can lead to all sorts of problems and [this issue has been acknowledged by the dev](https://github.com/clemfromspace/scrapy-selenium/issues/22).

## Better How?

What's better about this middleware?  Three things:

1) It initializes a queue of Selenium webdrivers. SeleniumRequests pull a selenium driver from this queue. When you are done in your scrapy parse function,
you just have to release the driver associated with that response/request, and it will be returned to the queue.
   
2) SeleniumRequests now take the user-agent from scrapy. So if you are using middlewares such as [scrapy-fake-useragent](https://github.com/alecxe/scrapy-fake-useragent), requests
will use the user-agent, provided you place the user-agent middleware at a higher priority than the selenium middleware.

3) Added `wait_sleep` as an unconditional delay after a selenium webdriver gets a page but before it returns the page source.
   I've found this to be more convenient than waits conditional on specific elements on the page (e.g., implicit waits, which are also available) 
   


## Installation
```
$ pip install git+https://github.com/dylanwalker/better-scrapy-selenium.git
```
You should use **python>=3.6**. 
You will also need one of the Selenium [compatible browsers](http://www.seleniumhq.org/about/platforms.jsp).

## Configuration
1. Add the browser to use, the path to the driver executable, and the arguments to pass to the executable to the scrapy settings:
    ```python
    SELENIUM_DRIVER_NAME = 'chrome'
    SELENIUM_DRIVER_EXECUTABLE_PATH = 'path/to/chromedriver.exe'
    SELENIUM_DRIVER_ARGUMENTS=['--window-size=1920,1080','--headless']  
    SELENIUM_MAX_INSTANCES = 16 # if not set, will default to match CONCURRENT_REQUESTS 
    ```

In order to use a remote Selenium driver, specify `SELENIUM_COMMAND_EXECUTOR` instead of `SELENIUM_DRIVER_EXECUTABLE_PATH`:
    ```python
    SELENIUM_COMMAND_EXECUTOR = 'http://localhost:4444/wd/hub'
    ```

2. Add the `SeleniumMiddleware` to the downloader middlewares:
   
    ```python
        DOWNLOADER_MIDDLEWARES = {
            'scrapy_selenium.SeleniumMiddleware': 800
        }
    ```

## Usage
Use the `scrapy_selenium.SeleniumRequest` instead of the scrapy built-in `Request` like below:
```python
from scrapy_selenium import SeleniumRequest

yield SeleniumRequest(url=url, callback=self.parse_result)
```
The request will be handled by selenium, and the request will have an additional `meta` key, named `driver` containing the selenium driver with the request processed.
```python
def parse_result(self, response):
    driver = response.request.meta['driver']
    # Do some dynamic stuff here with the driver. 
    #  e.g.,
    driver.find_element_by_xpath('//some/xpath').click()
    driver.execute_script('some script here')
    # and when you are done, you want to "refresh" the response
    response = response.refresh()
    # Do some stuff with the response data
    #  e.g.,
    print(response.request.meta['driver'].title)
    # Finish by releasing the webdriver, so it can go back into the queue and be used by other requests
    response.release_driver()
```
For more information about the available driver methods and attributes, refer to the [selenium python documentation](http://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.remote.webdriver)

The `selector` response attribute work as usual (but contains the html processed by the selenium driver).
```python
def parse_result(self, response):
    print(response.selector.xpath('//title/@text'))
```

### Additional arguments
The `scrapy_selenium.SeleniumRequest` accept 5 additional arguments:

#### `wait_time` / `wait_until` / `wait_sleep`

When used, selenium will perform an [Explicit wait](http://selenium-python.readthedocs.io/waits.html#explicit-waits) before returning the response to the spider.
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

yield SeleniumRequest(
    url=url,
    callback=self.parse_result,
    wait_time=10,
    wait_sleep=2,
    wait_until=EC.element_to_be_clickable((By.ID, 'someid'))
)
```

where `wait_sleep` will literally call a `time.sleep(wait_sleep)` before forming the response from selenium.


#### `screenshot`
When used, selenium will take a screenshot of the page and the binary data of the .png captured will be added to the response `meta`:
```python
yield SeleniumRequest(
    url=url,
    callback=self.parse_result,
    screenshot=True
)
#... other stuff
def parse_result(self, response):
    with open('image.png', 'wb') as image_file:
        image_file.write(response.meta['screenshot'])
```

The screenshot stored in `meta` is taken after the first time selenium renders the page. However, if you would like to 
grab a screenshot at any time aftewards (e.g., during parse) when handling a response, you can also call `response.get_screenshot()`:
```python
def parse_result(self,response):
    ...
    with open('image.png','wb') as image_file:
        image_file.write(response.get_screenshot())

```

#### `script`
When used, selenium will execute custom JavaScript code.
```python
yield SeleniumRequest(
    url=url,
    callback=self.parse_result,
    script='window.scrollTo(0, document.body.scrollHeight);',
)
```
