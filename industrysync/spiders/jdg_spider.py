import json
import scrapy


class JdgSpider(scrapy.Spider):
    name = 'jdg_spider'
    allowed_domains = ['jdg.com']
    start_urls = ['https://www.jdg.com/']
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse(self, response):
        yield response.follow(url=response.css('.menu-item-1932 a::attr(href)').get(), callback=self.parse_products)

    def parse_products(self, response):
        for link in response.css('.woocommerce-LoopProduct-link::attr(href)').getall():
            yield response.follow(url=link, callback=self.parse_item)
        next_page = response.css('.next.page-numbers::attr(href)').get()
        if next_page:
            yield response.follow(url=next_page, callback=self.parse_products)

    def parse_item(self, response):

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
                    item[ele_s.css('.woocommerce-product-attributes-item__label::text').get().replace(':', '').replace(' ', '-').lower()] = item[ele_s.css('.woocommerce-product-attributes-item__label::text').get().replace(':', '').replace(' ', '-').lower()] + '\n' + li
        raw_item = json.loads(response.css('.variations_form.cart::attr(data-product_variations)').get())
        if isinstance(raw_item, list):
            for sku in raw_item:
                final_item = item.copy()
                final_item['item'] = sku['sku']
                final_item['images'] = final_item['images'] + sku['image']['url']
                yield scrapy.Request(method='POST', url="https://www.jdg.com/wp-admin/admin-ajax.php", meta={'item': final_item}, headers={
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
                }, body=f"action=get_variation_alternate_images&variation_id={sku['variation_id']}&product_id={int(response.css('form[data-product_id]::attr(data-product_id)').get())}", callback=self.yield_result)

    def yield_result(self, response):
        item = response.meta['item']
        if response.css('a').get():
            item['images'] = item['images'] + ';' + ';'.join(response.css('a::attr(href)').getall())
            yield item
        else:
            yield item
