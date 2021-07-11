import itertools
import json
from urllib.parse import parse_qs
import urllib.parse as urlparse
from scrapy import Request, Selector
from scrapy.http import XmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, XMLFeedSpider
from w3lib.url import add_or_replace_parameters, url_query_parameter


class Mixin:
    provider = 'robern'
    allowed_domains = ['robern.com']
    start_urls = ['https://robern.com/']
    product_url = 'https://robern.com/umbraco/Api/ProductApi/GetProductInfo'
    headers = {
        'Accept': 'application/json; charset=utf-8'
    }


class RobernParseSpider(Mixin, XMLFeedSpider, CrawlSpider):
    name = Mixin.provider + '_parse'
    namespaces = [('xmlns', 'http://schemas.datacontract.org/2004/07/Robern.ViewModels.Api.Product')]

    def parse(self, response, **kwargs):
        raw_product = json.loads(response.css('[data-product-model]::attr(data-product-model)').get())
        item = {
            'images': ';'.join(set(response.css('[data-big2x]::attr(data-big2x)').getall())),
            'accessories-and-kits': ';'.join(self.parse_accessories(response, raw_product)),
            'technical-documents-installation-instructions': ';'.join(response.css('[data-filter-value="(Show Installation Instructions)|^$"] ::attr(href)').getall()),
            'technical-documents-specifications': ';'.join(response.css('[data-filter-value="(Show Specifications)|^$"] ::attr(href)').getall()),
            'technical-documents-cad-files': ';'.join(response.css('[data-filter-value="(Show CAD Files)|^$"] ::attr(href)').getall()),
            'next_requests': self.sku_requests(response)
        }

        return self.item_or_next_requests(item)

    def parse_skus(self, response):
        item = response.meta['item']

        item['size'] = url_query_parameter(response.url, 'SIZE')
        item['upgrade-options'] = url_query_parameter(response.url, 'ELECTRIC_PACKAGE')
        item['decorative-options'] = url_query_parameter(response.url, 'COLOR_FINISH_NAME')
        item['decorative-options-image'] = response.meta.get('decorative-image', '')

        for k, v in parse_qs(urlparse.urlparse(response.url).query).items():
            if k not in ['Style', 'DefaultSku', 'SIZE', 'ELECTRIC_PACKAGE', 'COLOR_FINISH_NAME']:
                item[k.lower().replace('_', '-')] = url_query_parameter(response.url, k)

        if isinstance(response, XmlResponse):
            self.parse_xml_sku(response, item)
        else:
            self.parse_json_sku(response, item)

        return item

    def parse_xml_sku(self, response, item):
        selector = Selector(response, type='xml')
        self._register_namespaces(selector)

        item['model-number'] = selector.xpath('xmlns:Sku/text()').get()
        item['list-price'] = int(selector.xpath('xmlns:PriceNumeric/text()').get())
        item['installation-guide'] = selector.xpath('xmlns:InstallationDocumentation//text()').get() or ''
        item['spec-sheet'] = selector.xpath('xmlns:SpecsDocumentation//text()').get() or ''

    def parse_json_sku(self, response, item):
        raw_sku = json.loads(response.body)

        item['model-number'] = raw_sku['Sku']
        item['list-price'] = int(raw_sku['PriceNumeric'])
        item['installation-guide'] = (raw_sku['InstallationDocumentation'] or [''])[0]
        item['spec-sheet'] = (raw_sku['SpecsDocumentation'] or [''])[0]

    def sku_requests(self, response):
        sku_requests = []
        combinations = {}

        sizes = response.css('#SIZE ::attr(value)').getall()
        if sizes:
            combinations['SIZE'] = sizes

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
                'decorative-image': ';'.join(image_element.split(',')) if image_element else ''
            }
            url = add_or_replace_parameters(self.product_url, payload)
            sku_requests.append(Request(url, self.parse_skus, headers=self.headers, meta=meta))

        if sku_requests:
            return sku_requests

        meta = {
            'combo': {
                'SIZE': response.css('li:contains("Size:") ::text').getall()[-1].strip(),
                'COLOR_FINISH_NAME':  response.css('[itemprop="additionalProperty"]::text').get()
            },
        }
        url = add_or_replace_parameters(self.product_url, payload)
        return [Request(url, self.parse_skus, headers=self.headers, meta=meta)]

    def item_or_next_requests(self, item):
        requests = item.pop('next_requests')

        if not requests:
            return item

        for request in requests:
            request.meta['item'] = item.copy()

        return requests

    def parse_accessories(self, response, raw_product):
        return [response.urljoin(accessory['Url']) for accessory in raw_product['Accessories']]


class RobernCrawlSpider(Mixin, CrawlSpider):
    name = Mixin.provider + '_crawl'
    parse_spider = RobernParseSpider()
    listing_css = ['.primaryNav-link:contains("Products ") + .primaryNav-submenu .feature']
    product_css = ['.feature-ft']

    custom_settings = {
        'CRAWLERA_ENABLED': True,
        'CRAWLERA_USER': '217db34c0e52472e9bb3fb50cefe3a84',
        'CRAWLERA_APIKEY': '217db34c0e52472e9bb3fb50cefe3a84'
    }

    rules = (
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css=product_css), callback='parse_item'),
    )

    def parse_item(self, response, **kwargs):
        return self.parse_spider.parse(response)
