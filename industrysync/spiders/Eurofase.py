import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class EurofaseSpider(CrawlSpider):
    name = 'eurofase_spider'
    allowed_domains = ['eurofase.com', 'Eurofase.com']
    start_urls = ['http://Eurofase.com/']
    rules = (
        Rule(LinkExtractor(restrict_css="#nav-menu-item-11535 li a")),
        Rule(LinkExtractor(restrict_css='.eltd-product-title-holder a'), callback='parse_item')
    )
    custom_settings = {
        "CRAWLERA_ENABLED": False,
    }

    def parse_item(self, response):
        product_detail_list = []
        light_source_list = []
        technical_detail_list = []
        download_resource_list = []
        for eles in response.css('.DetailTitle:contains("PRODUCTS DETAILS") + ul li'):
            product_detail_list.append('   :   '.join(eles.css('span::text').getall()))
        for eles in response.css('.DetailTitle:contains("LIGHT SOURCE DETAILS") + ul li'):
            light_source_list.append('   :   '.join(eles.css('span::text').getall()))
        for eles in response.css('.DetailTitle:contains("TECHNICAL DETAILS") + ul li'):
            technical_detail_list.append('   :   '.join(eles.css('span::text').getall()))
        for eles in response.css('.DetailTitle:contains("Download Resources") + div a'):
            download_resource_list.append(eles.css('::text').get() + ':  ' + eles.css('::attr(href)').get())
        yield {
            'title': response.css('h4.eltd-single-product-title::text').get(),
            'description': response.css('.summary.entry-summary .eltd-single-product-subtitle::text').get(),
            'copy': response.css('.summary.entry-summary .woocommerce-product-details__short-description p::text').get(),
            'product-details': '\n'.join(product_detail_list),
            'light-source-details': '\n'.join(light_source_list),
            'technical-details': '\n'.join(technical_detail_list),
            'where-to-buy': response.css('.DetailTitle:contains("Where To Buy") + div a::attr(href)').get(),
            'download-resources': '\n'.join(download_resource_list),
            'additional-finishes': ';'.join(response.css('.DetailTitle:contains("ADDITIONAL FINISHES") + ul a::attr(href)').getall()),
            'images': ';'.join(response.css('.woocommerce-product-gallery__wrapper a::attr(href)').getall())
        }
