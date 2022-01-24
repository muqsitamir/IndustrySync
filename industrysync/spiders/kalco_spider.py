import scrapy
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class KalcoSpider(CrawlSpider):
    name = 'kalco_crawl'
    allowed_domains = ['kalco.com']
    start_urls = ['https://portal.kalco.com/kal/e/1/login']
    custom_settings = {
        'COOKIES_ENABLED': True,
        'CRAWLERA_ENABLED': False
    }
    username = 'industrysync'
    password = 'weSync2020!'

    listing_css = ['.datatable tbody [data-label="ID"]', '.pagination']

    rules = (
         Rule(LinkExtractor(restrict_css=listing_css)),
         Rule(LinkExtractor(restrict_css='.export-products-purchased', attrs=("data-url",))),
    )

    def start_requests(self):
        return [Request(url=self.start_urls[0], callback=self.parse_login_page)]

    def parse_login_page(self, response):
        payload = {
            'authenticity_token': response.css('[name="csrf-token"]::attr(content)').get(),
            'return_url': '/kal/e/1/customers',
            'username': self.username,
            'password': self.password,
            'utf8': '✓',
        }
        return scrapy.FormRequest(url=response.url, formdata=payload, dont_filter=True)
