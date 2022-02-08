from scrapy.link import Link
from scrapy.spiders import CrawlSpider
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from w3lib.url import add_or_replace_parameter


class PaginationLE:
    page_size = 36

    def extract_links(self, response):
        no_of_products = response.css('#record-count::attr(value)').get()

        if not no_of_products:
            return []

        return [Link(add_or_replace_parameter(response.url, 'page', int(page)))
                for page in range(2, int(no_of_products)//self.page_size + 2)]


class AmericanLightingSpider(CrawlSpider):
    name = 'american_lighting_crawl'
    allowed_domains = ["framburg.com", "houseoftroy.com", "thumprints.com", "arroyocraftsman.com"]
    start_urls = [
        "https://framburg.com/categories",
        "https://houseoftroy.com/categories",
        "https://thumprints.com/categories",
        "https://arroyocraftsman.com/categories"
    ]

    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    rules = (
        Rule(PaginationLE()),
        Rule(LinkExtractor(restrict_css=".p-container + #container .item")),
        Rule(LinkExtractor(restrict_css="#products .item"), callback='parse_item'),
    )

    def parse_item(self, response):
        product_name = response.css("#product-details>h1.item-name::text").get()
        item = {
            "title": product_name,
            "sku": product_name.split()[-1],
            "url": response.url,
            "download_url": response.urljoin(response.css("#tearsheetVueApp>a")[1].css("::attr(href)").get()),
            "text": response.css("#details .item-description::text").get(),
            "image_urls": ';'.join([image_url.split('?')[0] for image_url in response.css("#alt-slideshow img::attr(src)").getall()]),
            "features": {},
        }

        for idx, feature in enumerate(response.css("#details li")):
            key, value = feature.css("::text").getall()
            item['features'][str(idx)] = {key[:-1]: value.strip()}

        return item
