import scrapy
from scrapy_selenium import SeleniumRequest
import time

class TestSpider(scrapy.Spider):
  name='TestSpider'
  def start_requests(self):
    self.logger.info('\t\t\t\t\t->Yielding the request now')
    yield SeleniumRequest(url='https://python.org')
    yield SeleniumRequest(url='https://google.com')
    yield SeleniumRequest(url='https://bing.com')
    yield SeleniumRequest(url='https://imdb.com')
    yield SeleniumRequest(url='https://amazon.com')
    yield SeleniumRequest(url='https://cnn.com')
    
  
  def parse(self,response):
    self.logger.info('\t\t\t\t\t->Processing the response now')
    time.sleep(10)
    driver = response.request.meta['driver']
    self.logger.info(f'\t\t\t\t\t->TEST SCRAPER SUCCESSFUL: {driver.title}')
    response.release_driver()
