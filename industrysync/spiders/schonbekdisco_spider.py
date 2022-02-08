from urllib.parse import quote_plus

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy import FormRequest, Request
from datetime import datetime, timedelta


class SchonbekDiscoSpider(CrawlSpider):
    name = 'schonbek_disco_crawl'
    allowed_domains = ['schonbek.com']
    start_urls = ["https://ws.schonbek.com/ws/ext/login.html"]

    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def start_requests(self):
        form_data = {
            "Name": "jkrupp",
            "password": "@Chloe071135@",
            "Submit": "login",
            "action": "login",
        }
        return [FormRequest(url=self.start_urls[0], formdata=form_data, callback=self.parse_login)]

    def parse_login(self, response):
        return scrapy.Request("https://ws.schonbek.com/ws/ext/z_retired-fixtures-list.html",
                              self.parse_fixtures_form)

    def parse_fixtures_form(self, response):
        url = "https://ws.schonbek.com/ws/ext/z_retired-fixtures-list.html"
        date_to = datetime.today()
        date_from = date_to.replace(year=date_to.year-10)
        payload = 'electrics=100&electrics=110&electrics=120-240&electrics=127V&electrics' \
                  '=12V&electrics=220&electrics=24V&electrics=CANDLE&electrics=LOW+VOLT&' \
                  f'electrics=NONE&datefrom={quote_plus(date_from.strftime("%d/%m/%y"))}&d' \
                  f'ateto={quote_plus(date_to.strftime("%d/%m/%y"))}&action=submit'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        return Request(url=url, method='POST', body=payload,
                       headers=headers, callback=self.parse_data)

    def parse_data(self, response):
        for row in response.css(".tableTbody tr"):
            data = row.css("td")
            item = {
                "product_line": data[0].css('::text').get(),
                "core": data[1].css('::text').get().replace('\'', ''),
                "fixture": data[2].css('::text').get().replace('\'', ''),
                "description": data[3].css('::text').get(),
                "voltage/electrics": data[4].css('::text').get(),
                "discontinued date": data[5].css('::text').get(),
            }
            yield item
