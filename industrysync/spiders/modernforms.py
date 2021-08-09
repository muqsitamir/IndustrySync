import scrapy
from scrapy.spiders import CrawlSpider
import json


class ModernformsSpider(CrawlSpider):
    name = 'modernforms_spider'
    allowed_domains = ['modernforms.com']
    start_urls = ['https://modernforms.com/']
    custom_settings = {
        "CRAWLERA_ENABLED": False
    }
    payload = 'data={}&page={}&catID={}'

    def parse_start_url(self, response):
        for fan_category_link in response.css('.FANS .first-level a::attr(href)').getall():
            yield response.follow(url=fan_category_link,
                                  callback=self.parse_categories) if 'ultra' not in fan_category_link else response.follow(
                url=fan_category_link, callback=self.parse_item)
        for light_category_link in response.css('section.group figure a::attr(href)').getall():
            yield response.follow(url=light_category_link, callback=self.parse_categories)

    def parse_categories(self, response):
        for link in response.css('aside.product-box > a::attr(href)').getall():
            yield response.follow(link, callback=self.parse_item)
        total_products = int(response.css('idunfiltered::attr(data-total)').get()) if response.css(
            'idunfiltered::attr(data-total)').get() is not None else 0
        if total_products > 12:
            total_products -= 12
            while total_products % 12 != 0:
                total_products += 1
            for number in range(int((total_products / 12) + 1)):
                if number != 0:
                    payload = self.payload.format(response.css('idunfiltered::text').get(), str(number * 12),
                                                  str(response.css(
                                                      'form[data-id]::attr(data-id)').get()))
                    yield scrapy.Request(method='POST',
                                         url='https://modernforms.com/wp-admin/admin-ajax.php?action=lazyUnfiltered',
                                         callback=self.parse_excessive,
                                         headers={
                                             'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                                         body=payload)

    def parse_excessive(self, response):
        text = json.loads(response.text)
        for dict in text:
            yield response.follow(url=dict['link'], callback=self.parse_item)

    def parse_item(self, response):
        item = {
            'product-url': response.url,
            'order-number': '',
            'title': response.css('h2[data-ppid]::text').get(),
            'images': ';'.join(response.css('section.product-thumbs img.ppid-thumbnail::attr(data-src)').getall()),
            'video': ';'.join(response.css('.model-video source::attr(src)').getall()).replace('\n', ''),
            'spec-sheet': response.css('ul li a:contains("Spec Sheet")::attr(href)').get(),
            'instructions': response.css('ul li a:contains("Instructions")::attr(href)').get(),
            'revit': response.css('ul li a:contains("Revit")::attr(href)').get(),
            'dimming-report': response.css('ul li a:contains("Dimming Report")::attr(href)').get(),
            'IES-file': response.css('ul li a:contains("IES File")::attr(href)').get(),
            'features': ';'.join(response.css('.WAC-LIGHTING-FEATURE-LIST li::text').getall()),
            'cct': response.css('section[data-panel=second] img::attr(data-src)').get(),
            'certifications': ';'.join(response.css('.sertcs img::attr(data-src)').getall()),
            'smart-fans': ';'.join(['https://modernforms.com' + x for x in response.css('section [data-panel=Fifth]  noscript +img::attr(data-src)').getall()]) if response.css('ul.feature-nav li:contains("Smart")').get() is not None else ""
        }
        order_numbers = json.loads(response.css('script:contains("all_models")::text').re_first("all_models = (.*);"))
        for order_number in order_numbers:
            sku = item.copy()
            sku['order-number'] = list(order_number)[0]
            yield sku
