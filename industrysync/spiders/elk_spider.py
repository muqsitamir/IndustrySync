import re
import urllib

import scrapy

from industrysync.utils import slugify

# Todo: This spider is not writen by softcreed, should be refactored.


class ElkSpider(scrapy.Spider):
    name = "elk_crawl"
    allowed_domains = ["www.elkgroupinternational.com"]
    start_urls = ["http://www.elkgroupinternational.com/"]
    productlist_url = "https://www.elkgroupinternational.com/ecomwgtproductlisting/pagedindex"
    widgetUniqueCode = "SdWlppw1TpFAaFHqsHbZSrnkUDJdN0iIBCSwZrYRytdGfw58QZXMAxfXlRP9GzqL"

    custom_settings = {
        'RETRY_HTTP_CODES': [407, 429, 502, 503, 504],
        'DOWNLOAD_DELAY': 1.5
    }

    def get_formdata(self, category_id, page):
        formdata = {
            "categoryId": category_id,
            "pageTo": page,
            "pageFrom": page,
            "displayMode": "grid",
            "userResultPerPage": "288",
            "widgetUniqueCode": self.widgetUniqueCode,
        }
        return urllib.parse.urlencode(formdata)

    def parse(self, response):
        brands = response.css(".nav :nth-child(1) li a::attr(href)").extract()
        for brand in brands:
            brand_url = response.urljoin(brand)
            yield scrapy.Request(brand_url, self.parse_brand)

    def parse_brand(self, response):
        categories = response.css("#menu-categories-options li")
        for category in categories:
            if not category.css("a b::text"):
                category_path = category.css("a::attr(href)").get()
                category_url = response.urljoin(category_path)
                yield scrapy.Request(category_url, self.parse_category)

    def parse_category(self, response):
        pattern = re.compile(r"var categoryId = \"(.*?)\";", re.MULTILINE | re.DOTALL)
        try:
            category_id = response.xpath('//script[contains(., "var categoryId")]/text()').re(pattern)[0]
        except IndexError:
            return self.parse_product(response)

        yield scrapy.Request(
            self.productlist_url,
            self.parse_productlist,
            method="POST",
            body=self.get_formdata(category_id, 1),
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            meta={"category_id": category_id, "page": 1, "cat": response.url}
        )

    def parse_productlist(self, response):
        category_id = response.meta["category_id"]
        next_page = response.meta["page"] + 1

        pattern = re.compile(r"lastPageNumber  = (.*?);", re.MULTILINE | re.DOTALL)
        last_page = response.xpath('//script[contains(., "ListingProduct.data.lastPageNumber")]/text()').re(pattern)[0]

        if next_page <= int(last_page):
            yield scrapy.Request(
                self.productlist_url,
                self.parse_productlist,
                method="POST",
                body=self.get_formdata(category_id, next_page),
                headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                meta={"category_id": category_id, "page": next_page}
            )

        products = response.css(".ejs-productitem img::attr(data-product-url)").extract()
        for product in products:
            product_url = response.urljoin(product)
            yield scrapy.Request(product_url, self.parse_product)

    def parse_product(self, response):
        item = {}
        item["url"] = response.url
        item["name"] = response.css("h1::text").get()
        item["sku"] = response.css(".product-details-code::text").get()
        item["product-highlights"] = response.css(".RadEDomMouseOver > tbody > tr:nth-child(3) > td::text").get()
        item["main-image"] = response.urljoin(response.css(".btn-downloadhighres::attr(href)").get())

        infos = response.xpath("//td[@class='attribute-title']/parent::tr")
        for info in infos:
            key = info.css("td strong::text").get()
            key = "product-information-" + slugify(key)
            item[key] = info.css("td::text").get()

        docs = response.css(".btn-ViewPDF")
        for doc in docs:
            key = doc.css("::text").get()
            key = "documentation-" + slugify(key)
            doc_path = doc.css("::attr(href)").get()
            item[key] = response.urljoin(doc_path)

        return item
