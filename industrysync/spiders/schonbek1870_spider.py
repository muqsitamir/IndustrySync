from scrapy import FormRequest, Request
from scrapy.spiders import CrawlSpider


class Schonbek1870Spider(CrawlSpider):
    name = 'schonbek1870_crawl'
    allowed_domains = ['ws.schonbek.com']
    start_urls = ['https://ws.schonbek.com/ws/ext/login.html']
    inventory_url = 'https://ws.schonbek.com/ws/ext/z_repavailfixinventory.html'
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def start_requests(self):
        payload = {
            'Name': 'jkrupp',
            'password': '@Chloe071135@',
            'Submit': 'login',
            'action': 'login'
        }
        return [FormRequest(url=self.start_urls[0], formdata=payload, callback=self.parse_start_url)]

    def parse_start_url(self, response, **kwargs):
        body = 'electrics=100&electrics=110&electrics=120-240&electrics=12V&electrics=220&electrics=24V' \
               '&electrics=CANDLE&electrics=LOW%2BVOLT&electrics=NONE&action=submit'
        return FormRequest(url=self.inventory_url, method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'},
                           body=body, callback=self.parse_items)

    def parse_items(self, response):
        keys = response.css('thead th::text').extract()
        for row_s in response.css('.tableTbody tr'):
            values = row_s.css('img::attr(src),td::text').extract()
            product = {k: v for k, v in zip(keys, values)}
            product['Image'] = response.urljoin(product['Image'])
            yield product


class Schonbek1870CustomerSpider(Schonbek1870Spider):
    name = 'schonbek1870_customer_crawl'
    customers = ['18123100', 'BY171623']
    customer_url = 'https://ws.schonbek.com/ws/ext/z_custmaster.html?customer={}&company=SWM'

    def parse_start_url(self, response, **kwargs):
        for customer in self.customers:
            yield Request(url=self.customer_url.format(customer), callback=self.parse_items)

    def parse_items(self, response):
        item = {
            'customer-name': response.css('.subheader1 ::text').get(),
            'excel-price-list': response.urljoin(response.css('a:contains("Excel Price List") ::attr(href)').get()),
            'excel-product-information': response.urljoin(response.css('a:contains("Excel Product Information") ::attr(href)').get()),
        }
        return item
