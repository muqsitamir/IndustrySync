import json

from scrapy import FormRequest, Request
from scrapy.spiders import CrawlSpider


class Mixin:
    provider = 'casablancafanco'
    allowed_domains = ['casablancafanco.com']
    start_urls = ['https://fanconnect.casablancafanco.com/']
    product_url_t = 'https://fanconnect.casablancafanco.com/catalogs/product.aspx?type=p&p={}'
    listing_url = 'https://fanconnect.casablancafanco.com/service/sales/browser/browse.json'
    username = 'sales@ktrlighting.com'
    password = '054'


class CasablancaFancoParseSpider(Mixin, CrawlSpider):
    name = Mixin.provider + '_parse'

    def parse(self, response):
        return {
            'model': response.css('#strProductID span::text').get(),
            'item': response.css('#strUPCCode span::text').get(),
        }


class CasablancaFancoCrawlSpider(Mixin, CrawlSpider):
    name = Mixin.provider + '_crawl'
    parse_spider = CasablancaFancoParseSpider()
    custom_settings = {
        'COOKIES_ENABLED': True
    }

    def parse_start_url(self, response, **kwargs):
        payload = {
            '__VIEWSTATE': response.css('#__VIEWSTATE::attr(value)').get(),
            '__EVENTVALIDATION': response.css('#__EVENTVALIDATION::attr(value)').get(),
            'ctl00$containerContent$txtUsername': self.username,
            'ctl00$containerContent$txtPassword': self.password,
            'ctl00$containerContent$btnLogin': 'Login'
        }
        return FormRequest(self.start_urls[0], callback=self.parse_catalog, formdata=payload, dont_filter=True)

    def parse_catalog(self, response):
        payload = {
            "Catalogs": [
                "c91af5e7-2639-4cc9-85b3-469572246cc7",
                "296cc9ab-7049-4549-a7e2-c54b0084d09d"
            ]
        }
        headers = {
            'Content-Type': 'application/json; charset=UTF-8'
        }
        return FormRequest(self.listing_url, callback=self.parse_listing, headers=headers, body=json.dumps(payload))

    def parse_listing(self, response):
        return [Request(self.product_url_t.format(product_id), callback=self.parse_item)
                for product_id in json.loads(response.text)['productIds']]

    def parse_item(self, response):
        return self.parse_spider.parse(response)
