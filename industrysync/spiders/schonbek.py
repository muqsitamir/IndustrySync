from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class SchonbekSpider(CrawlSpider):
    name = 'schonbek'
    allowed_domains = ['schonbek.com']
    start_urls = ['https://www.schonbek.com/']
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }
    rules = (
        Rule(LinkExtractor(restrict_css='a.product'), callback='parse_item'),
    )

    def parse_start_url(self, response, **kwargs):
        for category in response.css('ul.main-menu__inner-list[data-menu~=menu-908] li:nth-child(n+2) a::attr(href)').getall():
            yield Request(category+"?&product_list_limit=all")

    def parse_item(self, response):
        product = {
            'title': response.css('.product-name span::text').get().replace('\t', '').replace('\n', '').replace('\r', ''),
            'core-sku': response.css('.product-name h2::text').get(),
            'specsheet': response.css('.download-specs::attr(href)').get(),
        }
        yield product
