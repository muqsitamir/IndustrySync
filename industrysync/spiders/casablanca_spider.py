import json
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CasablancaCrawlSpider(CrawlSpider):
    name = 'casablanca_crawl'
    allowed_domains = ['hunterfan.com', 's7d5.scene7.com']
    start_urls = [
        'https://www.hunterfan.com/',
        'https://www.hunterfan.com/pages/casablanca'
    ]

    imageset_url_t = 'https://s7d5.scene7.com/is/image/{}?req=set,json,UTF-8'
    image_url_t = 'https://s7d5.scene7.com/is/image/{}?fit=constrain,1&wid={}&hei={}&fmt=jpg'
    video_url_t = 'https://s7d5.scene7.com/is/content/{}'

    listing_css = ['.site-nav.lvl-2:contains(" All")', '.site-nav.lvl-1:contains(" all")', '.Grid', '.infinitpagin']
    rules = (
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css='.grid-view-item__title'), callback='parse_item'),
    )

    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse_item(self, response):
        item = {
            'title': response.css('h1.product-single__title.desktop_only::text').get(),
            'price': response.css('#ProductPrice-product-template ::text').get(),
            'finish': '',
            'images': '',
            'sku': '',
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
        content = []
        raw_images = json.loads(raw_images)['set']['item']

        if isinstance(raw_images, dict):
            item['images'] = self.image_url_t.format(raw_images['i']['n'], raw_images['dx'], raw_images['dy'])
            return item

        for raw_content in raw_images:
            if 'type' not in raw_content:
                content.append(self.image_url_t.format(raw_content['i']['n'], raw_content['dx'], raw_content['dy']))
            elif raw_content['type'] == 'video':
                content.append(self.video_url_t.format(raw_content['v']['path']))
            elif raw_content['type'] == 'video_set':
                res = [int(v['v']['dx'])*int(v['v']['dy']) for v in raw_content['set']['item']]
                max_res_index = res.index(max(res))
                content.append(self.video_url_t.format(raw_content['set']['item'][max_res_index]['v']['path']))

        item['images'] = ';'.join(content)
        return item
