# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class IndustrysyncPipeline:
    def process_item(self, item, spider):
        if spider.name == 'elk_crawl':
            return item

        if item['model-number']:
            return item

        raise DropItem('Dropping out of stock item as it has no "model-number" and "list-price"')
