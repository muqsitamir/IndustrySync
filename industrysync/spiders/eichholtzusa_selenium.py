import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains

MAX_LOAD_WAIT = 10
scraped_products = []
driver = webdriver.Chrome(ChromeDriverManager().install())
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


for i in range(1, 5):
    time.sleep(2)
    menu = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-1 > a")))
    ActionChains(driver).move_to_element(menu).perform()
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f".nav-1 .level1:nth-child({i}).ui-menu-item"))).click()
