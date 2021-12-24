from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from w3lib.url import add_or_replace_parameter


class LightologySpider(CrawlSpider):
    name = 'lightology_crawl'
    allowed_domains = ['lightology.com']
    start_urls = [
        "https://www.lightology.com/index.php?module=cat&search=basic&top_cat_id=1&vend_id=858"
    ]
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }
    listing_css = ['.next']
    rules = (
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css='.product-grid'), callback='parse_item'),
    )

    def parse_item(self, response):
        item = {
            'mfr-id': response.css(".dyn_prod_sku::text").get(),
            'item-no': response.css(".dyn_prod_code::text").get(),
            'url': response.url,
            'title': response.css(".dyn_prod_name::text").get(),
            'images': ';'.join(response.css('.gallery-thumb::attr(data-img-link)').extract()),
            'product-details-spec': response.css('.pdf_specsheet::attr(href)').get(),
            'product-details': '\n'.join(response.css('.desc-detail::text').extract()),
            'product-details-finish': response.css('.dyn_finish_name::text').get(),
            'product-details-size': response.css('.dyn_prod_dimensions::text').get(),
            'product-details-attr': response.css('.dyn_attribute_name::text').get(),
            'product-details-color': response.css('.dyn_color_name::text').get(),
            'product-details-dimmer': response.css('.dyn_dimmer_name > span + span ::text').get(),
            'product-details-label': response.css('.labels-text::text').get().strip(),
            'product-details-lamp-source': response.css('.dyn_lamp_source_name::text').get(),
            'product-details-bulb': response.css('.bulb_string::text').get(),
            'price': response.css(".dyn_price span+span::text").get()
        }
        yield item

        for prod_id in response.css('#options ::attr(data-display-prod-id)').extract():
            yield Request(add_or_replace_parameter(response.url, 'prod_id', prod_id), callback=self.parse_item)
