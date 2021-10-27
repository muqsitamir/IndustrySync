import re
from scrapy.spiders import CrawlSpider


class SolaraSpider(CrawlSpider):
    name = 'solara_crawl'
    allowed_domains = ['solaracustomdoorsandlighting.com']
    start_urls = ['https://solaracustomdoorsandlighting.com/lighting/']

    def parse_start_url(self, response, **kwargs):
        for link in response.css('.box-link::attr(href)').getall():
            if 'outdoor' in link:
                yield response.follow(url=link, callback=self.parse_outdoor)
            if 'indoor' in link:
                yield response.follow(url=link, callback=self.parse_indoor)

    def parse_outdoor(self, response):
        for link in response.css('.box-link::attr(href)').getall():
            yield response.follow(url=link, callback=self.parse_outdoor_categories)

    def parse_indoor(self, response):
        for link in response.css('.box-link::attr(href)').getall():
            yield response.follow(url=link, callback=self.parse_indoor_categories)

    def parse_outdoor_categories(self, response):
        for link in response.css('.box-link::attr(href)').getall():
            yield response.follow(url=link, callback=self.parse_links)

    def parse_indoor_categories(self, response):
        yield response.follow(url=response.css('.regular-button::attr(href)').get(), callback=self.parse_links)

    def parse_links(self, response):
        for product in response.css('ul .product-wrap > a::attr(href)').getall():
            yield response.follow(url=product, callback=self.parse_item)
        if response.css('.next.page-numbers'):
            yield response.follow(url=response.url + f"page/{str(int(response.css('.page-numbers.current::text').get()) + 1)}/", callback=self.parse_links)

    def parse_item(self, response):
        item = {
            'url': response.url,
            'title': response.css('.product_title::text').get(),
            'description': response.css('.woocommerce-product-details__short-description > p:nth-child(1)::text').get(),
            'attributes': ";".join(response.css('.woocommerce-product-details__short-description > ul li::text').getall()),
            'sku': response.css('.woocommerce-product-details__short-description > p:contains("SKU")::text').get().replace("SKU:", "") if response.css('.woocommerce-product-details__short-description > p:contains("SKU")::text').get() else None,
            'sizes': response.css('.woocommerce-product-details__short-description > p:contains("Sizes")::text').get().replace("Sizes:", "") if response.css('.woocommerce-product-details__short-description > p:contains("Sizes")::text').get() else None,
            'images': []
        }
        key = ""
        for ele in response.css('div#tab-description>div:nth-child(n + 2)'):
            if ele.css('h4::text').get():
                key = ele.css('h4::text').get().replace(":", "")
                item[key] = ""
            if ele.css('h3'):
                vals = []
                for elem in ele.css('.wpb_wrapper'):
                    if elem.css('h3::text').get():
                        vals.append(elem.css('h3::text').get() + " - image: " + elem.css('a::attr(href)').get())
                item[key] = ";".join(set(vals))
            if key == "Product Downloads":
                vals = []
                for down_ele in ele.css('.tilt-button-inner'):
                    vals.append(down_ele.css('span::text').get() + ": " + down_ele.css('a::attr(href)').get())
                item[key] = ";".join(vals)

        for img in response.css('.thumb-inner > img'):
            highest_resolution = max([int(x) for x in re.findall(r"g (.*?)w", img.css('::attr(data-lazy-srcset)').get())])
            item['images'].append(img.css('::attr(data-lazy-src)').get().replace("150x150", f"{highest_resolution}x{highest_resolution}"))
        item['images'] = ";".join(item['images'])
        yield item
