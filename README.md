# Gutenberg Collector

This project is used to crawl free Gutenberg fiction books and their corresponding ratings from Goodreads as well. It is based on `Scrapy` framework and `Selenium`, data scraped is stored in `MongoDB`.

## Usage
Download code and install dependencies:
 
 `Scrapy`, `Selenium`, `pymongo`

Setup MongoDB environment and download and place `chromedriver` (workable with your Chrome version) to the right place.

Then, run:

`scrapy crawl gutenberg`

It will scrape the `title`, `genre` and `content` of books. After it's done, run:

`python3 rating_collector.py`

It will crawl the `rating` and `rating_count` from Goodreads website. (You need to put a text file containing your Goodreads credential to be read by the script)