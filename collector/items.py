# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Book(scrapy.Item):
    title = scrapy.Field()
    genre = scrapy.Field()
    rating = scrapy.Field()
    rating_count = scrapy.Field()
    review_count = scrapy.Field()
    content = scrapy.Field()