#!/bin/bash
docker cp settings.py bss:/test_spider/test_spider/settings.py
docker cp TestSpider.py bss:/test_spider/test_spider/spiders/TestSpider.py