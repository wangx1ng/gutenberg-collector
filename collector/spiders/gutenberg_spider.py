import scrapy
from collector.items import Book


class BookSpider(scrapy.Spider):
    name = 'gutenberg'
    allowed_domains = ['www.gutenberg.org', 'www.goodreads.org']

    start_url = 'http://www.gutenberg.org/wiki/Category:Fiction_Bookshelf'
    gutenberg_base = 'http://www.gutenberg.org'
    scheme_http = 'http://'

    # Log strings
    BOOK_CRAWLING = "Crawling book from url: "
    RATING_CRAWLING = "Crawling rating from url: "

    def start_requests(self):
        yield scrapy.Request(self.start_url, self.handle_page)

    def handle_page(self, response):
        categories = response.xpath('//div[@class="mw-category-group"]/ul/li/a')
        for cate in categories:
            genre = cate.xpath('.//@title').extract_first()
            if genre.endswith(' (Bookshelf)'):
                genre = genre[:-12]
            suffix = cate.xpath('.//@href').extract_first()
            d = {'genre': genre}
            yield scrapy.Request(self.gutenberg_base + suffix, self.handle_items, meta=d)

    def handle_items(self, response):
        books = response.xpath('//a[@class="extiw"]')
        for book in books:
            url = book.xpath('.//@href').extract_first()
            title = book.xpath('.//text()').extract_first()
            d = {'genre': response.meta.get('genre'), 'title': title}
            yield scrapy.Request(self.scheme_http + url, self.parse_book, meta=d)

    def parse_book(self, response):
        self.logger.info(self.BOOK_CRAWLING + response.url + "...")
        url = response.xpath('//a[@type="text/plain"]/@href').extract_first()
        yield scrapy.Request(self.gutenberg_base + url, self.save_book, meta=response.meta)

    def save_book(self, response):
        content = response.xpath('//text()').extract_first()
        title = response.meta.get('title')
        genre = response.meta.get('genre')

        book = Book()
        book['title'] = title
        book['genre'] = genre
        book['content'] = content
        yield book
