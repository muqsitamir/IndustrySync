import json
import re

from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class BusterAndPunchSpider(CrawlSpider):
    name = 'busterandpunch_crawl'
    allowed_domains = ['busterandpunch.com', 'fast.wistia.com']
    start_urls = [
        "https://www.busterandpunch.com/extraordinary-home-details/"
    ]
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }
    listing_css = ['.wp-block-button__link', '.page-numbers']
    rules = (
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css='.products'), callback='parse_item'),
    )

    def parse_item(self, response):
        product_id = response.css('[property="product:retailer_item_id"]::attr(content)').get()
        item = {
            'url': response.url,
            'title': response.css('.product_title::text').get(),
            'price': int(response.css('.summary bdi::text').get()),
            'description': '\n'.join(response.css('.product-description__content p::text').extract()),
            'images': ';'.join(response.css('#gallery a::attr(href)').extract()),
            'line-drawing': response.css('.technical_spec_image::attr(src)').get(),
            'included-in-the-box': ';'.join(response.css('#tab-included-in-the-box ::attr(src)').extract()),
            'finish': response.css('.iconic-was-swatch--selected::attr(data-finish)').get(),
            'finish-img-url': response.css('.iconic-was-swatch--selected img::attr(src)').get(),
        }

        for bulb_s in response.css('#tab-which-bulbs li'):
            sku = item.copy()
            sku['sku'] = f'{product_id}_{bulb_s.css("::attr(data-clerk-product-id)").get()}'
            sku['price'] += int(bulb_s.css('bdi::text').get())
            sku['images'] += f';{bulb_s.css(" img::attr(src)").get()}'
            sku['next_requests'] = self.next_requests(response)
            yield self.item_or_next_requests(sku)

        yield from [Request(url=url, callback=self.parse_item)
                    for url in response.css('.iconic-was-swatches [data-finish]::attr(href)').extract()]

    def parse_installation(self, response):
        item = response.meta['item']
        item['installation-video'] = json.loads(re.search('\"assets\"\:(\[.*?\])', response.text).group(1))[0]['url']
        yield self.item_or_next_requests(item)

    def parse_product_video(self, response):
        item = response.meta['item']
        item['product-video'] = json.loads(re.search('\"assets\"\:(\[.*?\])', response.text).group(1))[0]['url']
        yield self.item_or_next_requests(item)

    def parse_finish(self, response):
        item = response.meta['item']
        finish_col = '-'.join(response.meta['finish_col'].lower().split())
        item[finish_col] = json.loads(re.search(r'"assets":(\[.*?\])', response.text).group(1))[0]['url']
        yield self.item_or_next_requests(item)

    def next_requests(self, response):
        requests = []

        install_css = '[aria-labelledby="tab-title-installation-video"] script::attr(src)'
        installation = response.css(install_css).get()

        if installation:
            requests.append(Request(response.urljoin(installation),
                                    callback=self.parse_installation, dont_filter=True))

        product_video_css = '.product__main-video__wrapper script::attr(src)'
        product_video = response.css(product_video_css).get()

        if product_video:
            requests.append(Request(response.urljoin(product_video),
                                    callback=self.parse_product_video, dont_filter=True))

        finish_url_css = '.which-finish__media-wrapper ::attr(src)'

        for finish_item in response.css('.which-finish__grid-item'):
            requests.append(
                Request(url=response.urljoin(finish_item.css(finish_url_css).get()), callback=self.parse_finish,
                        dont_filter=True, meta={'finish_col': finish_item.css('h3::text').get()})
            )

        return requests

    def item_or_next_requests(self, item):
        requests = item.pop('next_requests')

        if not requests:
            return item

        request = requests.pop()
        item['next_requests'] = requests
        request.meta['item'] = item
        return request
