import itertools
import json

from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from w3lib.url import add_or_replace_parameters


class Mixin:
    provider = 'robern'
    allowed_domains = ['robern.com']
    start_urls = ['https://robern.com/']
    product_url = 'https://robern.com/umbraco/Api/ProductApi/GetProductInfo'
    headers = {
        'Accept': 'application/json'
    }


class RobernParseSpider(Mixin, CrawlSpider):
    name = Mixin.provider + '_parse'

    def parse(self, response, **kwargs):

        item = {
            'images': ';'.join(set(response.css('[data-big2x]::attr(data-big2x)').getall())),
            'accessories-and-kits': '',
            'technical-documents-installation-instructions': ';'.join(response.css('[data-filter-value="(Show Installation Instructions)|^$"] ::attr(href)').getall()),
            'technical-documents-specifications': ';'.join(response.css('[data-filter-value="(Show Specifications)|^$"] ::attr(href)').getall()),
            'technical-documents-cad-files': ';'.join(response.css('[data-filter-value="(Show CAD Files)|^$"] ::attr(href)').getall()),
            'next_requests': self.sku_requests(response)
        }
        return self.item_or_next_requests(item)

    def parse_skus(self, response):
        raw_sku = json.loads(response.body)
        item = response.meta['item']

        item['model-number'] = raw_sku['Sku']
        item['list-price'] = int(raw_sku['PriceNumeric'])
        item['size'] = response.meta['combo']['SIZE']
        item['upgrade-options'] = response.meta['combo'].get("ELECTRIC_PACKAGE", '')
        item['decorative-options'] = response.meta['combo'].get("COLOR_FINISH_NAME", '')
        item['decorative-options-image'] = response.meta['decorative-image']
        item['installation-guide'] = raw_sku['InstallationDocumentation'][0] if raw_sku['InstallationDocumentation'] else ''
        item['spec-sheet'] = raw_sku['SpecsDocumentation'][0] if raw_sku['SpecsDocumentation'] else ''

        return item

    def sku_requests(self, response):
        sku_requests = []
        combinations = {
            'SIZE': response.css('#SIZE ::attr(value)').getall(),
        }

        for panel in set(response.css('.collapsible-panel input::attr(name)').getall()):
            combinations[panel] = response.css(f'[name={panel}] ::attr(value)').getall()

        parameters = combinations.keys()
        payload = {
            'Style': response.css(f'[name="Style"] ::attr(value)').get(),
            'DefaultSku': response.css(f'[name="DefaultSku"] ::attr(value)').get(),
        }

        for sku in itertools.product(*combinations.values()):
            for item in sku:
                for param in parameters:
                    if item in combinations[param]:
                        payload[param] = item

            image_css = f'[name="COLOR_FINISH_NAME"][value="{payload.get("COLOR_FINISH_NAME")}"] + span img::attr(srcset)'
            image_element = response.css(image_css).get()
            meta = {
                'combo': payload.copy(),
                'decorative-image': ';'.join(image_element.split(',')) if image_element else ''
            }
            url = add_or_replace_parameters(self.product_url, payload)
            sku_requests.append(Request(url, self.parse_skus, headers=self.headers, meta=meta))

        return sku_requests

    def item_or_next_requests(self, item):
        requests = item.pop('next_requests')

        if not requests:
            return item

        for request in requests:
            request.meta['item'] = item.copy()

        return requests


class RobernCrawlSpider(Mixin, CrawlSpider):
    name = Mixin.provider + '_crawl'
    parse_spider = RobernParseSpider()
    listing_css = ['.primaryNav-link:contains("Products ") + .primaryNav-submenu .feature']
    product_css = ['.feature-ft']

    rules = (
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css=product_css), callback='parse_item'),
    )

    def parse_item(self, response, **kwargs):
        return self.parse_spider.parse(response)
