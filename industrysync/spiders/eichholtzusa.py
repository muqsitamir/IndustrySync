import scrapy
import json


class EichholtzusaSpider(scrapy.Spider):
    name = 'eichholtzusa_spider'
    allowed_domains = ['eichholtzusa.com']
    start_urls = ['https://eichholtzusa.com//']
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse(self, response):
        for link in response.css('.nav-1 > ul > li > a::attr(href)').getall():
            yield response.follow(url=link, callback=self.parse_category) if link != '#' else None

    def parse_category(self, response):
        i = 1
        while i <= int(response.css('#am-page-count::text').get()):
            yield response.follow(url=response.url + '?p=' + str(i), callback=self.parse_pages)
            i = i + 1

    def parse_pages(self, response):
        for item in response.css(' a.product-item-link::attr(href)').getall():
            yield response.follow(url=item, callback=self.parse_item)

    def parse_item(self, response):
        item = {
            'url': response.url,
            'title': response.css('[data-ui-id="page-title-wrapper"]::text').get(),
            'description': response.css('div.product-information::text').get(),
            'sku': response.css('[itemprop="sku"]::text').get(),
            'finish': response.css('.finish p::text').get(),
            'measurement-cm': response.css('.measurement-cm::text').get(),
            'measurement-inch': response.css('.measurement-inch::text').get(),
            'details': '\n'.join(response.css('.product-info-main .usp-title::text').getall()),
            'images': [],
        }
        for ele in json.loads(response.css('div.product.media > script::text').get())[
            '[data-gallery-role=gallery-placeholder]'][
            'mage/gallery/gallery']['data']:
            item['images'].append(ele['full'])
        item['images'] = ';'.join(item['images'])
        for ele in response.css('#product-attribute-specs-table tbody tr'):
            item[ele.css('th::text').get()] = ele.css('td::text').get()
        if response.css('img.dimensions-image::attr(src)').get():
            item['dimensions-image']: response.css('img.dimensions-image::attr(src)').get()
        yield item