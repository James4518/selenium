import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import lxml

class NavItem:
  def __init__(self, title, icons, categories_title, brands, more_brand):
    self.title = title
    self.icons = icons
    self.categories_title = categories_title
    self.brands = brands
    self.more_brand = more_brand

class MoreBrand:
  def __init__(self, link, picUrl):
    self.link = link
    self.picUrl = picUrl

class Kaola:
  def __init__(self):
    self.driver = None
    self.navList = []
    self.categories_dict = {}

  def setup_driver(self):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    self.driver = webdriver.Chrome(options=options)
    self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    })
    self.driver.get("https://www.kaola.com/")

  def setup_bs(self, page_source):
    self.soup = BeautifulSoup(page_source, 'lxml')

  def scrapy_nav(self):
    nav = self.driver.find_element(By.XPATH, '//ul[@class="catitmlst j-catmenu f-switch-catitems"]')
    liList = nav.find_elements(By.XPATH, ".//li")
    for li in liList:
      title_element = li.find_element(By.XPATH, ".//span[@class='t']")
      all_category = title_element.text
      ActionChains(self.driver).move_to_element(title_element).perform()
      time.sleep(0.5)

  def parse_nav(self):
    ul = self.soup.find('ul', class_='catitmlst j-catmenu f-switch-catitems')
    liList = ul.find_all('li')
    for li in liList:
      title_element = li.find('span', class_='t')
      all_category = title_element.get_text()

      icon_elements = li.find_all('img', class_='icon')
      icons = [{"src": icon['src'], "srcset": icon['srcset']} for icon in icon_elements]

      big_category_contents = li.find('div', class_='m-ctgcard f-cb j-category_card')
      brandList = big_category_contents.find_all('div', class_='m-brandbox')
      brands = []
      for brand in brandList:
        brandElements = brand.find_all('a')
        for brandElement in brandElements:
          brandHref = brandElement['href']
          picUrl = brandElement.find('img')['src']
          brands.append({"href": brandHref, "picUrl": picUrl})

      more_brand_element = big_category_contents.find('div', class_='imgbox')
      more_brand_link = more_brand_element.find('a')['href']
      more_brand_picUrl = more_brand_element.find('img')['src']
      more_brand = MoreBrand(more_brand_link, more_brand_picUrl)

      litds = big_category_contents.select('.litd .item')
      litd_titles = [litd.find('p').find('a', class_=lambda x: x and x.startswith('cat2')).get_text() for litd in litds]
      categories_list = []
      category_dict = {}
      for litd in litds:
        litd_title = litd.find('p').find('a', class_=lambda x: x and x.startswith('cat2')).get_text()
        ctgbox = litd.find('div', class_='ctgnamebox')
        sub_categories = ctgbox.find_all('a', class_=lambda x: x and x.startswith('f-fcred'))
        category_dict[litd_title] = [sub_category.get_text() for sub_category in sub_categories]
        categories_list.append(litd_title)

      self.categories_dict[all_category] = category_dict
      nav_item = NavItem(all_category, icons, litd_titles, brands, more_brand)
      self.navList.append(nav_item)

  def close_driver(self):
    if self.driver:
      self.driver.quit()

  def print_nav(self):
    for nav_item in self.navList:
      print("Title:", nav_item.title)
      print("Icons:", nav_item.icons)
      print("Brands:")
      for brand in nav_item.brands:
          print("pic:", brand["picUrl"], "href", brand["href"])
      print("More Brands:")
      print("pic:", nav_item.more_brand.picUrl, "href", nav_item.more_brand.link)
      print("Subcategories:")
      for category in nav_item.categories_title:
          print(category, ":", self.categories_dict[nav_item.title][category])
      print("\n")

def main():
  kaola = Kaola()
  kaola.setup_driver()
  kaola.scrapy_nav()
  page_source = kaola.driver.page_source
  kaola.setup_bs(page_source)
  kaola.parse_nav()
  kaola.close_driver()
  kaola.print_nav()

if __name__ == "__main__":
  main()