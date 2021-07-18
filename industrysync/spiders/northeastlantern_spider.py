import itertools
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class NortheastlanternSpider(CrawlSpider):
    name = 'northeastlantern_crawl'
    allowed_domains = ['www.northeastlantern.com']
    start_urls = ['https://www.northeastlantern.com/view/category/']
    rules = (
        Rule(LinkExtractor(restrict_css='[title="View products in this category"]')),
        Rule(LinkExtractor(restrict_css='[title="View product"]'), callback='parse_item')
    )
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def parse_item(self, response):
        spec_sheet = response.css('.spec-sheet::attr(href)').get()
        css = '.productdetails :contains("{}")::text'
        item = {
            'url': response.url,
            'product-code': f'{response.css(".ProductCode::Text").get()[:-1]}',
            'title': response.css('.productseperator h2::text').get(),
            'images': ';'.join([response.urljoin(url) for url in response.css('.sidethumbs li img::attr(src)').getall()]),
            'details-dimensions': (response.css(css.format("Dimensions")).get() or '').replace("Dimensions: ", ''),
            'details-mounting-height': (response.css(css.format("Mounting height")).get() or '').replace('Mounting height: ', ''),
            'details-bulb-type': (response.css(css.format("Bulb")).get() or '').replace('Bulb type: ', ''),
            'details-suitable-location': (response.css(css.format("Suitable")).get() or '').replace('Suitable location: ', ''),
            'details-mounting-area': (response.css(css.format("Mounting Area")).get() or '').replace('Mounting Area: ', ''),
            'Other-sizes-available': ';'.join([size.strip() for size in response.css('.relatedsizes li::text').getall()]),
            'finish-options': ';'.join([response.urljoin(url) for url in response.css('.finishoptions ::attr(src)').getall()]),
            'glass-options': ';'.join([response.urljoin(url) for url in response.css('.glassoptions ::attr(src)').getall()]),
            'Details-spec-sheet': response.urljoin(spec_sheet) if spec_sheet else '',
            'image-accessories': ';'.join([response.urljoin(url) for url in response.css('.associated-opts img::attr(src)').getall()]),
            'finish': '',
            'socket': '',
            'glass': ''
        }
        finishes = response.css('#Form_productForm_Finish :not([value=""])::attr(value)').getall()
        sockets = response.css('#Form_productForm_Socket :not([value=""])::attr(value)').getall()
        glasses = response.css('#Form_productForm_Glass :not([value=""])::attr(value)').getall()

        product_combo = {'finish': finishes, 'socket': sockets, 'glass': glasses}
        product_combo = {k: v for k, v in product_combo.items() if v}

        for combo in list(itertools.product(*product_combo.values())):
            sku = item.copy()
            for value in combo:
                sku['product-code'] += f"-{value}"
                for k, vs in product_combo.items():
                    if value in vs:
                        sku[k] = response.css(f'[value={value}]::text').get()
            yield sku
