import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import lxml
from typing import List, Dict

class NavItem:
  def __init__(self, title: str, icons: List[Dict[str, str]], categories_title: List[str], brands: List['Brand'], more_brand: 'Brand'):
    self.title = title
    self.icons = icons
    self.categories_title = categories_title
    self.brands = brands
    self.more_brand = more_brand

class Brand:
  def __init__(self, link: str, imgUrl: str, desc:str=None, count:int =None):
    self.link = link
    self.imgUrl = imgUrl
    self.desc = desc
    self.count = count

class Zone:
  def __init__(self, name: str, hot_words: List[Dict[str, str]], activity: 'Activity', 
    part_list: List['Goods_info'], hot_sale: List['Goods'], hot_brands: List[Dict[str, str]]):
    self.name = name
    self.hot_words = hot_words
    self.activity = activity
    self.part_list = part_list
    self.hot_sale = hot_sale
    self.hot_brands = hot_brands

class Activity:
  def __init__(self, link: str, imgUrl: str, zone_list: List[Dict[str, str]]):
    self.link = link
    self.imgUrl = imgUrl
    self.zone_list = zone_list

class Goods:
  def __init__(self, title: str, link: str, imgUrl: str, old_price: float, price: float, talkCount:int = None):
    self.title = title
    self.link = link
    self.imgUrl = imgUrl
    self.old_price = old_price 
    self.price = price
    self.talkCount = talkCount

class Goods_info:
  def __init__(self, title: str, desc: str, link: str, imgUrl: str):
    self.title = title
    self.desc = desc
    self.link = link
    self.imgUrl = imgUrl

class Kaola:
  def __init__(self):
    self.driver = None
    self.navList = []
    self.categories_dict = {}
    self.all_zone = []
    self.hot_brands_banner = []
    self.hot_brands_list = []
    self.guest_list = []

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
      icons = [icon['src'].replace('//','https://').split('?')[0] for icon in icon_elements]

      big_category_contents = li.find('div', class_='m-ctgcard f-cb j-category_card')
      brandList = big_category_contents.find_all('div', class_='brandlist')
      brands = []
      for brand in brandList:
        brandElements = brand.find_all('a')
        for brandElement in brandElements:
          brand_link = brandElement['href'].replace('//','https://')
          brand_imgUrl = brandElement.find('img')['src'].replace('//','https://')
          brands.append(Brand(brand_link,brand_imgUrl))

      more_brand_element = big_category_contents.find('div', class_='imgbox')
      more_brand_link = more_brand_element.find('a')['href'].replace('//','https://')
      more_brand_imgUrl = more_brand_element.find('img')['src'].replace('//','https://')
      more_brand = Brand(more_brand_link, more_brand_imgUrl)

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

  def parse_article(self):
    articles = self.soup.find_all('article', class_='m-productfloor pc-index-module')
    for article in articles:
      article_title = article.find('span', class_='big').get_text()
      hot_words = [
        {
          'title': li.find('a').get_text(),
          'link': li.find('a')['href']
        }
        for li in article.find('ul', class_='w-taglist clearfix').find_all('li', class_='last')
      ]
      
      main_part = article.find('div', class_='cont clearfix').contents[0]
      main_link = main_part.find('a')['href']
      main_imgUrl = main_part.find('img')['src']
      mainpart_list = [
        {
          'text': li.find('span').get_text(),
          'imgUrl': li.find('a')['href']
        }
        for li in main_part.find_all('ul')
      ]
      activity = Activity(main_link, main_imgUrl, mainpart_list)

      content_part = article.find('div', class_='cont clearfix').find('div', class_='partm')
      part_list = [
        Goods_info(
          li.next_element.find('h3').get_text(),
          li.next_element.find('p').get_text(),
          li.next_element['href'],
          li.next_element.find('img')['src']
        )
        for li in content_part.find('ul').find_all('li')
      ]

      hot_sale = [
        Goods(
          itemsale.find('a', 'protitle').get_text(),
          itemsale.find('a', 'protitle')['href'].replace('//', 'https://'),
          itemsale.find('a')['href'].replace('//', 'https://'),
          itemsale.find('p', 'curprice').find('strong').get_text(),
          itemsale.find('p', 'curprice').find('del').get_text()
        )
        for itemsale in article.find_all('div', class_='itemgroup')
      ]

      hot_brands = [
        {
          'imgUrl': brand.find('img')['src'].replace('//', 'https://'),
          'link': brand['href']
        }
        for brand in article.find('div', class_='brandListContainer').find_all('a')
      ]
      self.all_zone.append(Zone(article_title, hot_words, activity, part_list, hot_sale, hot_brands))

  def parse_hot(self):
    hot_section = self.soup.find('section', class_='cnt f-cb')
    left = hot_section.find('div', class_='fixedBrandWrap not-support-filter')
    left_ul = left.find('ul', class_='fixedBrand f-cb')
    for li in left_ul.find_all('li'):
      a = li.find('a')
      link = a['href'].replace('//','https://')
      imgUrl = a.find('img')['src'].split('?')[0]
      text = li.find('div',class_='txt')
      title = text.find_all('p')[0].get_text()
      desc = text.find_all('p')[1].get_text()
      self.hot_brands_banner.append(Goods_info(title, desc, link, imgUrl))
    recommend = hot_section.find('ul', class_='recomBrand f-cb')
    for li in recommend.find_all('li'):
      info = li.find('div', class_='info')
      imgUrl = info.find('img')['src'].split('?')[0]
      desc = info.find('p').string
      actions = li.find('div', class_='actions')
      count = actions.find('p').string.replace('人关注该品牌','')
      lilnk = actions.find('a')['href'].replace('//', 'https://')
      self.hot_brands_list.append(Brand(link,imgUrl,desc,count))

  def parse_guest(self):
    guest_like = self.soup.find('div', class_='m-reclst clearfix')
    for content in guest_like.find_all('div'):
      link = content.find('a', class_='itemImg')['href'].split('?')[0].replace('//', 'https://')
      imgUrl = content.find('img')['src']
      content_title = content.find('p', class_='itemTitle')
      title = content_title.find('a').get_text()
      info = content.find('div', class_='itemInfo clearfix')
      price = info.find('p', class_='price').select_one('.price').get_text()
      old_price = info.find('p', class_='price').select_one('.marprice del').get_text()
      talkCount = info.find('a').get_text()
      print((title,link,imgUrl,old_price,price,talkCount))
      self.guest_list.append(Goods(title,link,imgUrl,old_price,price,talkCount))

  def close_driver(self):
    if self.driver:
      self.driver.quit()

  def print_nav(self):
    for nav_item in self.navList:
      print("Title:", nav_item.title)
      print("Icons:", nav_item.icons)
      print("Brands:")
      for brand in nav_item.brands:
        print("pic:", brand.imgUrl, "href", brand.link)
      print("More Brands:")
      print("pic:", nav_item.more_brand.imgUrl, "href", nav_item.more_brand.link)
      print("Subcategories:")
      for category in nav_item.categories_title:
        print(category, ":", self.categories_dict[nav_item.title][category])
      print("\n")

  def print_article(self):
    for zone in self.all_zone:
      print("区域名称:", zone.name)
      print("热词:")
      for hot_word in zone.hot_words:
        print("  标题:", hot_word['title'])
        print("  链接:", hot_word['link'])
      print("活动链接:", zone.activity.link)
      print("活动图片地址:", zone.activity.imgUrl)
      print("主要内容部分:")
      for part in zone.part_list:
        print("  商品标题:", part.title)
        print("  商品描述:", part.desc)
        print("  商品链接:", part.link)
        print("  商品图片地址:", part.imgUrl)
      print("热门商品:")
      for goods in zone.hot_sale:
        print("  商品标题:", goods.title)
        print("  商品链接:", goods.link)
        print("  商品图片地址:", goods.imgUrl)
        print("  原价:", goods.old_price)
        print("  现价:", goods.price)
      print("热门品牌:")
      for brand in zone.hot_brands:
        print("  品牌图片地址:", brand['imgUrl'])
        print("  品牌链接:", brand['link'])
    
  def print_hot_brands(self):
    print("Hot Brands Banner:")
    for goods_info in self.hot_brands_banner:
      print("Title:", goods_info.title)
      print("Description:", goods_info.desc)
      print("Link:", goods_info.link)
      print("Image URL:", goods_info.imgUrl)
    print("Hot Brands List:")
    for brand in self.hot_brands_list:
      print("Description:", brand.desc)
      print("Image URL:", brand.imgUrl)
      print("Number of Followers:", brand.count)
      print("Link:", brand.link)

  def print_guest(self):
    print('guest:')
    for guest in self.guest_list:
      print(guest.title,guest.link,guest.imgUrl,guest.old_price,guest.price,guest.talkCount)

def main():
  kaola = Kaola()
  kaola.setup_driver()
  kaola.scrapy_nav()
  page_source = kaola.driver.page_source
  kaola.setup_bs(page_source)
  kaola.parse_nav()
  kaola.parse_article()
  kaola.parse_hot()
  kaola.print_guest()
  kaola.close_driver()
  kaola.print_nav()
  kaola.print_article()
  kaola.print_hot_brands()
  kaola.print_guest()

if __name__ == "__main__":
  main()