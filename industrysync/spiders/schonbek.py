from scrapy import Request
from scrapy.spiders import CrawlSpider


class SchonbekSpider(CrawlSpider):
    name = 'schonbek'
    allowed_domains = ['schonbek.com']
    start_urls = ['https://www.schonbek.com/']
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse_start_url(self, response, **kwargs):
        for category in response.css('ul.main-menu__inner-list[data-menu~=menu-908] li:nth-child(n+2) a::attr(href)').getall():
            yield Request(category+"?&product_list_limit=all", callback=self.parse_category)

    def parse_category(self, response):
        for link in response.css('a.product::attr(href)').getall():
            yield Request(link, callback=self.parse_item)

    def parse_item(self, response):
        product = {
            'title': response.css('.product-name span::text').get().replace('\t', '').replace('\n', '').replace('\r', ''),
            'core-sku': response.css('.product-name h2::text').get(),
            'specsheet': response.css('.download-specs::attr(href)').get(),
        }
        yield product
