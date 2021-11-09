import json
from scrapy import Request
from scrapy.spiders import CrawlSpider


class JdgSpider(CrawlSpider):
    name = 'jdg_crawl'
    allowed_domains = ['jdg.com']
    start_urls = ['https://www.jdg.com/']
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse_start_url(self, response, **kwargs):
        yield response.follow(url=response.css('.menu-item-1932 > a::attr(href)').get(), callback=self.parse_all_products)

    def parse_all_products(self, response):
        yield response.follow(url=response.css('.next.page-numbers::attr(href)').get(), callback=self.parse_all_products)
        for link in response.css('.woocommerce-LoopProduct-link::attr(href)').getall():
            yield response.follow(url=link, callback=self.parse_item)

    def parse_item(self, response):
        raw_item = json.loads(response.css('.variations_form.cart::attr(data-product_variations)').get())
        if raw_item:
            item = {
                'title': response.css('.product_title::text').get().replace('\n\t', ''),
                'shade-shape': ';'.join(response.css('#pa_shade-shape option:nth-of-type(n+2)::text').getall()),
                'metal-finish': ";".join([
                    x.re_first("'(.*)'") for x in
                    response.css('[aria-label="Metal Finish"] li::attr(style)')]
                    ),
                'lamping': ";".join(response.css('[aria-label=Lamping] li img::attr(alt)').getall()),
                'shade-finish': ";".join(response.css('#pa_shade-finish option:nth-of-type(n+2)::text').getall()),
                'images': '',
                'item': '',
                'finial-option': ';'.join(response.css('#pa_finial-option option:nth-of-type(n+2)::text').getall()),
                'ies-file': '',
                'ies-file-pdf': ''
            }
            for ele_s in response.css('.resource-item'):
                if '.ies' in str(ele_s.css('a span::text').get()):
                    item['ies-file'] = ele_s.css('a::attr(href)').get()
                elif '.pdf' in str(ele_s.css('a span::text').get()):
                    item['ies-file-pdf'] = ele_s.css('a::attr(href)').get()
            for ele_s in response.css('.woocommerce-product-attributes-item'):
                item[ele_s.css('.woocommerce-product-attributes-item__label::text').get().replace(':', '').replace(' ', '-').lower()] = ele_s.css('a::text, p::text').get()
                if ele_s.css('li::text').get():
                    for li in ele_s.css('li::text').getall():
                        item[ele_s.css('.woocommerce-product-attributes-item__label::text').get().replace(':', '').replace(' ', '-').lower()] += '\n' + li
            if isinstance(raw_item, list):
                for sku in raw_item:
                    final_item = item.copy()
                    final_item['item'] = sku['sku']
                    final_item['images'] += sku['image']['url']
                    yield Request(method='POST', url="https://www.jdg.com/wp-admin/admin-ajax.php", meta={'item': final_item}, headers={
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
                    }, body=f"action=get_variation_alternate_images&variation_id={sku['variation_id']}&product_id={int(response.css('form[data-product_id]::attr(data-product_id)').get())}",
                                         callback=self.yield_result)
        else:
            item = {
                'title': response.css('.product_title::text').get().replace('\n\t', ''),
                'metal-finish': ";".join([
                    x.re_first("'(.*)'") for x in
                    response.css('[aria-label="Metal Finish"] li::attr(style)')]
                ),
                'cord-option': ';'.join([x.replace('150x150', '300x300') for x in response.css('ul[aria-label="Cord Option"] img::attr(src)').getall()]),
                'ceramic-finish': {},
                'lamping': ";".join(response.css('[aria-label=Lamping] li img::attr(alt)').getall()),
                'images': ";".join(response.css('div.woocommerce-product-gallery img::attr(src)').getall()),
                'ies-file': '',
                'ies-file-pdf': ''
            }
            for ele_s in response.css('.resource-item'):
                if '.ies' in str(ele_s.css('a span::text').get()):
                    item['ies-file'] = ele_s.css('a::attr(href)').get()
                elif '.pdf' in str(ele_s.css('a span::text').get()):
                    item['ies-file-pdf'] = ele_s.css('a::attr(href)').get()
            for ele_s in response.css('.woocommerce-product-attributes-item'):
                item[ele_s.css('.woocommerce-product-attributes-item__label::text').get().replace(':', '').replace(' ',
                                                                                                                   '-').lower()] = ele_s.css(
                    'a::text, p::text').get()
                if ele_s.css('li::text').get():
                    for li in ele_s.css('li::text').getall():
                        item[ele_s.css('.woocommerce-product-attributes-item__label::text').get().replace(':',
                                                                                                          '').replace(
                            ' ', '-').lower()] += '\n' + li
            for ele in response.css('div.main_attribute_group .shade-finish.group_sub_item'):
                item['ceramic-finish'][ele.css('label::text').get().strip()] = ';'.join(ele.css('li > img::attr(src)').getall())
            shade_finishes = [x.upper() for x in response.css('div.main_attribute_group .shade-finish.group_sub_item li::attr(data-value)').getall()]
            metal_finishes = [x.upper() for x in response.css('[aria-label="Metal Finish"] li::attr(data-value)').getall()]
            cord_options = [x.upper() for x in response.css('ul[aria-label="Cord Option"] li::attr(data-value)').getall()]
            configured_fixture = response.css('.sku::text').get().strip()
            for shade_finish in shade_finishes:
                for metal_finish in metal_finishes:
                    for cord_option in cord_options:
                        sku = item.copy()
                        sku['item'] = configured_fixture + '-' + shade_finish + '-' + metal_finish + '-' + cord_option
                        yield sku

    def yield_result(self, response):
        item = response.meta['item']
        if response.css('a').get():
            item['images'] += ';' + ';'.join(response.css('a::attr(href)').getall())
            yield item
        else:
            yield item
