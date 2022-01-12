from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


def process_links(link):
    return link if 'download=specs' not in link else None


class WACLightingSpider(CrawlSpider):
    name = 'waclighting_crawl'
    allowed_domains = ['waclighting.com']
    start_urls = ['https://www.waclighting.com/']
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }
    listing_css = ['.sub-menu', '.l2-category-link', '.pagination']

    rules = (
        Rule(LinkExtractor(restrict_css=listing_css)),
        Rule(LinkExtractor(restrict_css='.type-product', process_value=process_links), callback='parse_item'),
    )

    def parse_item(self, response):
        if not response.css('.title-row'):
            return

        spec_sheet_css = 'a[href*="storage"]:contains("SPEC SHEET")::attr(href), a[href*="=specs"]::attr(href)'
        spec_sheet = response.css(spec_sheet_css).get()
        instructions = response.css('a:contains("INSTRUCTIONS")::attr(href)').get()
        ies_files = response.css('a:contains("IES FILES")::attr(href)').get()
        dimming_report = response.css('a:contains("DIMMING REPORT")::attr(href)').get()

        item = {
            'url': response.url,
            'title': response.css('.title-row h1::text').get(),
            'image': ';'.join(response.css('.thumbs ::attr(src)').extract()),
            'spec-sheet': response.urljoin(spec_sheet) if spec_sheet else None,
            'instructions': response.urljoin(instructions) if instructions else None,
            'ies-files': response.urljoin(ies_files) if ies_files else None,
            'dimming-report': response.urljoin(dimming_report) if dimming_report else None,
            'gallery': ';'.join([response.urljoin(g) for g in response.css('.gallery a::attr(href)').extract()]),
            'line-drawings': ';'.join(
                [response.urljoin(g) for g in response.css('.line-drawings ::attr(src)').extract()]),
        }
        for sku_s in response.css('.specifications-table tbody tr'):
            sku = item.copy()
            sku['sku'] = sku_s.css('::attr(data-order-number)').get()
            yield sku
