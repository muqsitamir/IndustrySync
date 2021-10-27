import time
import math
import json
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
import scrapy


class EichholtzUSASpider(scrapy.Spider):
    name = 'eichholtzusa_spider'
    allowed_domains = ['eichholtzusa.com']
    start_urls = ['https://eichholtzusa.com/']
    custom_settings = {
        'CRAWLERA_ENABLED': False
    }

    def proxy_add(self):
        f = open("proxies.txt", "r")
        list_of_lines = f.readlines()
        if not any(
                "x " in s for s in list_of_lines):  # add locator to first item in file when running for first the time
            list_of_lines[0] = "x " + list_of_lines[0]
        for index, line in enumerate(list_of_lines):
            if "x " in line:
                next_index = index + 1
                if index == len(list_of_lines) - 1:
                    next_index = 0

                list_of_lines[index] = list_of_lines[index].split("x ").pop()  # update current line
                proxy = list_of_lines[index]
                list_of_lines[next_index] = "x " + list_of_lines[next_index]  # update next line
                return proxy

    def start_requests(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f'--proxy-server={self.proxy_add()}')
        MAX_LOAD_WAIT = 10
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.get("https://eichholtzusa.com/")
        username = "jon.mcmahan@ktrlighting.com"
        password = "@Winner8248"
        wait = WebDriverWait(driver, MAX_LOAD_WAIT)
        my_account = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.action.toggle.switcher-trigger'))).click()
        username_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='login[username]']")))
        password_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='login[password]']")))
        username_field.clear()
        password_field.clear()
        username_field.send_keys(username)
        password_field.send_keys(password)
        login = driver.find_element_by_css_selector("#send2").click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".customer-account-logout")))

        for i in range(1, 4):
            time.sleep(2)
            menu = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-1 > a")))
            ActionChains(driver).move_to_element(menu).perform()
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f".nav-1 .level1:nth-child({i}).ui-menu-item > a"))).click()
            i = 1
            page_count = math.ceil(int(driver.find_element_by_css_selector('.toolbar-number:nth-of-type(3)').text) / 48)
            url = driver.current_url + '?p='
            while i <= page_count:
                driver.get(url + str(i))
                for product in [x.get_attribute('href') for x in driver.find_elements_by_css_selector('a.product-item-link')]:
                    driver.get(product)
                    time.sleep(3)
                    item = {
                        'price': driver.find_element_by_css_selector('.currency-sign').text + driver.find_element_by_css_selector('span.price-final_price .whole').text,
                        'downloads': ';'.join([ele.get_attribute('href') for ele in driver.find_elements_by_css_selector('.downloads-container div a')]),
                        'images': []
                    }
                    count = 1
                    for ele in driver.find_elements_by_css_selector('.stock-container ul li'):
                        if '\n' not in ele.text:
                            item[f'availability{count}'] = ele.text
                        else:
                            item[f'availability{count}'] = ele.text.split('\n')[0]
                        count = count + 1
                    yield scrapy.Request(url=driver.current_url, callback=self.parse_item, meta={'item': item})
                i = i + 1

    def parse_item(self, response):
        item = response.meta['item']
        for ele in json.loads(response.css('div.product.media > script::text').get())[
            '[data-gallery-role=gallery-placeholder]'][
            'mage/gallery/gallery']['data']:
            item['images'].append(ele['full'])
        item['images'] = ';'.join(item['images'])
        for ele in response.css('#product-attribute-specs-table tbody tr'):
            item[ele.css('th::text').get()] = ele.css('td::text').get()
        if response.css('img.dimensions-image::attr(src)').get():
            item['dimensions-image'] = response.css('img.dimensions-image::attr(src)').get()
        item['measurement-cm'] = response.css('.measurement-cm::text').get()
        item['measurement-inch'] = response.css('.measurement-inch::text').get()
        item['url'] = response.url
        item['title'] = response.css('[data-ui-id="page-title-wrapper"]::text').get(),
        item['description'] = response.css('div.product-information::text').get(),
        item['sku'] = response.css('[itemprop="sku"]::text').get(),
        item['finish'] = response.css('.finish p::text').get(),
        item['measurement-cm'] = response.css('.measurement-cm::text').get(),
        item['measurement-inch'] = response.css('.measurement-inch::text').get(),
        item['details'] ='\n'.join(response.css('.product-info-main .usp-title::text').getall()),
        yield item
