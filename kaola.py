import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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

  def scrapy_nav(self):
    nav = WebDriverWait(self.driver, 10).until(
      EC.visibility_of_element_located((By.XPATH, '//ul[@class="catitmlst j-catmenu f-switch-catitems"]'))
    )
    liList = nav.find_elements(By.XPATH, ".//li")
    for li in liList:
      title_element = li.find_element(By.XPATH, ".//span[@class='t']")
      all_category = title_element.text
      ActionChains(self.driver).move_to_element(title_element).perform()
      action = ActionChains(self.driver)
      action.move_to_element(title_element).perform()
      time.sleep(0.5)

      icon_elements = li.find_elements(By.XPATH, ".//img[contains(@class, 'icon') or contains(@class, 'iconhv')]")
      icons = []
      for icon in icon_elements:
        icons.append({
          "src": icon.get_attribute("src"),
          "srcset": icon.get_attribute("srcset")
        })

      big_category_contents = li.find_element(By.XPATH, ".//div[@class='m-ctgcard f-cb j-category_card']")
      brandList = big_category_contents.find_elements(By.XPATH, ".//div[contains(@class,'m-brandbox')]")
      brands = []
      for brand in brandList:
        brandElements = brand.find_elements(By.XPATH, ".//a")
        for brandElement in brandElements:
            brandHref = brandElement.get_attribute("href")
            picUrl = brandElement.find_element(By.XPATH, ".//img").get_attribute("src")
            brands.append({
              "href": brandHref,
              "picUrl": picUrl
            })
      more_brand_element = big_category_contents.find_element(By.XPATH, ".//div[contains(@class,'imgbox')]")
      more_brand_link = more_brand_element.find_element(By.XPATH, ".//a").get_attribute("href")
      more_brand_picUrl = more_brand_element.find_element(By.XPATH, ".//img").get_attribute("src")
      more_brand = MoreBrand(more_brand_link, more_brand_picUrl)

      litds = big_category_contents.find_elements(By.XPATH,"./div/div/div[@class='f-cb']/div[@class='litd']/div[@class='item']")
      litd_titles = []
      categories_list = []
      category_dict = {}
      for litd in litds: 
        litd_title = litd.find_element(By.XPATH, ".//p/a[starts-with(@class, 'cat2')]").text
        litd_titles.append(litd_title)
        ctgbox = litd.find_element(By.XPATH, ".//div[@class='ctgnamebox']")
        sub_categories = ctgbox.find_elements(By.XPATH, ".//a[starts-with(@class,'f-fcred')]")
        category_dict[litd_title] = [sub_category.text for sub_category in sub_categories]
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
  kaola.close_driver()
  kaola.print_nav()

if __name__ == "__main__":
  main()
