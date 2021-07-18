import json
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CasablancaCrawlSpider(CrawlSpider):
    name = 'casablanca_crawl'
    allowed_domains = ['hunterfan.com', 's7d5.scene7.com']
    start_urls = ['https://www.hunterfan.com/collections/ceiling-fans']
    imageset_url_t = 'https://s7d5.scene7.com/is/image/{}?req=set,json,UTF-8'
    image_url_t = 'https://s7d5.scene7.com/is/image/{}?fit=constrain,1&wid={}&hei={}&fmt=jpg'

    rules = (
        Rule(LinkExtractor(restrict_css='div.infinitpagin a')),
        Rule(LinkExtractor(restrict_css='a.grid-view-item__title'), callback='parse_item'),
    )

    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse_item(self, response):
        item = {
            'title': response.css('h1.product-single__title.desktop_only::text').get(),
            'price': response.css('#ProductPrice-product-template ::text').get(),
            'finish': '',
            'sku': '',
            'images': '',
            'url': response.url,
            'overview': '\n'.join([s for s in response.css('.product-description .overview ::text').getall() if s != '\n']),
            'specsheet-image': response.css('.specs-diagram img::attr(data-src)').get(),
            'specsheet-description': '\n'.join(response.css('#shopify-product-specs li::text').getall()),
            'owners-manual': response.css('div.manual a:contains("Manual")::attr(href)').get(),
            'energy-guide': response.css('div.manual a:contains("Energy")::attr(href)').get(),
            'parts-guide': response.css('div.manual a:contains("Parts")::attr(href)').get(),
        }
        for sku_s in response.css('div[data-varsku]'):
            sku = item.copy()
            sku['sku'] = sku_s.css('::attr(data-varsku)').get()
            sku['finish'] = sku_s.css('::attr(data-value)').get()

            yield Request(self.imageset_url_t.format(sku_s.css('::attr(data-medialink)').get()),
                          callback=self.parse_images, meta={'item': sku})

    def parse_images(self, response):
        item = response.meta['item']
        raw_images = response.text.replace('/*jsonp*/s7jsonResponse(', '').replace(',"");', '')

        item['images'] = ';'.join([self.image_url_t.format(raw_img['i']['n'], raw_img['dx'], raw_img['dy'])
                                   for raw_img in json.loads(raw_images)['set']['item'] if 'type' not in raw_img])

        yield item
