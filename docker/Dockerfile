FROM selenium/standalone-chrome

USER root
RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y git
RUN apt-get install -y vim
RUN apt-get install -y nano
RUN python3 -m pip install selenium
RUN python3 -m pip install scrapy
RUN python3 -m pip install git+https://github.com/dylanwalker/better-scrapy-selenium.git
RUN scrapy startproject test_spider
COPY settings.py /test_spider/test_spider/settings.py
COPY TestSpider.py /test_spider/test_spider/spiders/TestSpider.py