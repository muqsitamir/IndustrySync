import json

from scrapy import Request
from scrapy.spiders import CrawlSpider
from w3lib.url import add_or_replace_parameter


class ElkSpider(CrawlSpider):
    name = "elkhome_crawl"
    allowed_domains = ["elkhome.com"]
    start_urls = ["https://www.elkhome.com/api/v2/products?page=1&sort=1&pageSize=96"]
    high_res_url_t = 'https://www.elkhome.com/api/v1/products/{}/storeCompressedImages'

    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse_start_url(self, response):
        raw_pagination = json.loads(response.text)['pagination']

        for page_no in range(2, raw_pagination['numberOfPages']+1):
            yield Request(url=add_or_replace_parameter(response.url, 'page', page_no),
                          callback=self.product_requests)

        yield from self.product_requests(response)

    def product_requests(self, response):
        for product in json.loads(response.text)['products']:
            yield Request(response.urljoin(product['canonicalUrl']), callback=self.parse_item)

    def parse_item(self, response):
        prod_id = response.css('[data-test-selector*=productId]::attr(data-test-selector)').get()[25:]
        raw_item = json.loads(response.css('script:contains(initialReduxState)::text').re_first('({.*})'))['data']
        item = {
            "url": response.url,
            "name": response.css('[data-test-selector="ProductDetailsPageTitle"]::text').get(),
            "sku": response.css('[data-test-selector="ProductDetailsPartNumber"]::text').get(),
            "description": response.css('[data-test-selector="productDetails_htmlContent"]::text').get(),
            "dimensions": response.css('p:contains(Dimensions)::text').get(),
            "images": ';'.join([img['largeImagePath'] for img in raw_item['products']['byId'][prod_id]['images']]),
            "specifications": {},
            "downloads": {'high-resolution-images':  self.high_res_url_t.format(prod_id)}
        }

        for i, attr_s in enumerate(response.css('[data-test-selector="productDetails_attributes"] li')):
            key_css = '[data-test-selector="attributes_item_label"]::text'
            value_css = '[data-test-selector="attributes_item_value"]::text'
            item['specifications'][str(i)] = {attr_s.css(key_css).get(): attr_s.css(value_css).get()}

        for download_s in response.css('a[data-test-selector*=productDetails]'):
            key = download_s.css('::text').get().lower().replace(' ', '-')
            item['downloads'][key] = download_s.css('::attr(href)').get()

        return item
