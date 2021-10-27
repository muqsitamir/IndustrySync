import re
import scrapy
import math
from scrapy.spiders import CrawlSpider


class EliteFixturesSpider(CrawlSpider):
    name = 'elitefixtures_crawl'
    allowed_domains = ['schonbek.com', 'elitefixtures.com']
    start_urls = ['https://www.elitefixtures.com/index.cfm/Schonbek-Lighting/m120']
    custom_settings = {
        'CRAWLERA_ENABLED': False,
        'DOWNLOAD_DELAY': 3
    }

    def parse_start_url(self, response, **kwargs):
        page_count = math.ceil(int(response.css('#paging_top span::text').get())/30)
        i = 1
        while i <= page_count:
            yield scrapy.Request(url=self.start_urls[0] + '?page=' + str(i), callback=self.parse_pagination)
            i = i + 1

    def parse_pagination(self, response):
        url_temp = 'https://www.elitefixtures.com/'
        for link in response.css('.product_item3x4 h4 > a::attr(href)').getall():
            yield scrapy.Request(url=url_temp+link, callback=self.parse_item)

    def parse_item(self, response):
        for ele in response.css('.urls_container > div > a'):
            spec_sheet = ele.css('::attr(href)').get().replace('//', '') if ele.css('a > div:contains("Specification Sheet")').get() else None
        for sku_data in [x for x in response.css('#multiSelect script:nth-child(2)::text').re("({ (\n|.)*?})") if x.strip()]:
            sku = dict(re.findall(r"(\w*)\s?:\s'(.*)'", sku_data))
            sku['spec-sheet'] = spec_sheet
            identity = sku['id']
            yield scrapy.Request(url=f'https://www.elitefixtures.com/index.cfm?dsp=public.products.detail_pure&keyID={identity}', callback=self.parse_sku, meta={'item': sku})

    def parse_sku(self, response):
        item = response.meta['item']
        item['name'] = response.css("#bigCaption::text").get().strip()
        item['sku'] = response.css("#sku_numb::text").get().strip()
        item['price'] = response.css('.price::text').get().replace('Price: ', '')
        item['stock-availablility'] = response.css('.inStockMsg::text').get()
        item['stock-present'] = response.css('.stock_content::text').get().strip()
        item['make'] = response.css('.availabilityMsg::text').get()
        item['images'] = ';'.join([x.replace('//', '') for x in response.css('.theImage a::attr(href)').getall()])
        for ele in response.css('#dsp_product_description table tr'):
            item[[x.strip() for x in ele.css('td::text').getall()][0]] = [x.strip() for x in ele.css('td::text').getall()][1]
        item['product-details'] = response.css('#dsp_product_description_2 p:contains("Product Details") + p span::text').get().strip()
        item['detailed-description'] = response.css('#dsp_product_description_2 p:contains("Detailed Description") span::text').get().strip() + '\n' + '\n'.join(response.css('#dsp_product_description_2 ul li::text').getall())
        yield item
