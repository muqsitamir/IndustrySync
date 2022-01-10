import json
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CasablancaCrawlSpider(CrawlSpider):
    name = 'casablanca_crawl'
    allowed_domains = ['hunterfan.com', 's7d5.scene7.com', 'edge.curalate.com', 'res.cloudinary.com']
    start_urls = [
        'https://www.hunterfan.com/',
        'https://www.hunterfan.com/pages/casablanca'
    ]
    handle_httpstatus_list = [404]
    imageset_url_t = 'https://res.cloudinary.com/casablancahunter/image/list/{}.json'
    videoset_url_t = 'https://res.cloudinary.com/casablancahunter/video/list/{}.json'
    image_url_t = 'https://res.cloudinary.com/casablancahunter/image/upload/b_rgb:FFFFFF/{}'
    video_url_t = 'https://res.cloudinary.com/casablancahunter/video/upload/b_rgb:FFFFFF/{}'
    large_img_url = 'https://edge.curalate.com/v1/media/RBAUVdgCASbpxxGt?filter=((productId%3A%27{}%27))'

    listing_css = ['.site-nav.lvl-2:contains(" All")', '.site-nav.lvl-1:contains(" all")', '.Grid', '.infinitpagin']
    rules = (
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css='.grid-view-item__title'), callback='parse_item'),
    )

    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse_item(self, response):
        main_video = response.css('script:contains("myGallery")::text').re_first('publicId:\s"(.*?)"')
        item = {
            'title': response.css('h1.product-single__title.desktop_only::text').get(),
            'price': response.css('#ProductPrice-product-template ::text').get(),
            'finish': '',
            'sku': '',
            'aux-image': '',
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
            sku['images'] = [self.video_url_t.format(main_video)] if main_video else []

            yield Request(self.imageset_url_t.format(sku['sku']), callback=self.parse_images, meta={'item': sku})

    def parse_images(self, response):
        item = response.meta['item']
        item['images'] += [self.image_url_t.format(img["public_id"])
                           for img in json.loads(response.text)['resources']]
        yield Request(self.videoset_url_t.format(item['sku']), callback=self.parse_videos, meta={'item': item})

    def parse_videos(self, response):
        item = response.meta['item']
        if response.status == 200:
            item['images'] += [self.video_url_t.format(img["public_id"])
                               for img in json.loads(response.text)['resources']]
        item['images'] = ';'.join(item['images'])
        yield Request(self.large_img_url.format(item['sku']), callback=self.parse_result, meta={'item': item})

    def parse_result(self, response):
        item = response.meta['item']
        raw_data = json.loads(response.text)
        aux = [image['media']['extraLargeSquare']['link'] for image in raw_data['data']['items']]
        item['aux-image'] = ';'.join(aux)
        yield item
