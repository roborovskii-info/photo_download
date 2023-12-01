import os
import time
from urllib import request, error

import bs4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

EVENT_ID = os.environ.get('EVENT_ID')
EVENT_PASSWORD = os.environ.get('EVENT_PASSWORD')
REQUEST_URL = os.environ.get('REQUEST_URL')


def collect_image_url():
    options = webdriver.ChromeOptions()
    # 「Chromeは自動テストソフトウェアによって制御されています」を非表示
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    # ログインページを開く
    driver.get(REQUEST_URL)
    # name event_id にID入力
    driver.find_element(By.NAME, 'event_id').send_keys(EVENT_ID)
    # name event_pass にパスワード
    driver.find_element(By.NAME, 'event_pass').send_keys(EVENT_PASSWORD)
    # loginPane__button をクリック
    driver.find_element(By.CLASS_NAME, 'loginPane__button').click()

    # item__links から aタグを抽出
    item_link_wrapper = driver.find_element(By.CLASS_NAME, 'item__links')
    item_link_list = item_link_wrapper.find_elements(By.TAG_NAME, 'a')

    page_url_map = {}
    for item_link in item_link_list:
        # aタグのテキストからフォルダ名 / URLを取得
        page_url_map[item_link.text] = item_link.get_attribute('href')
    print(page_url_map)

    # 各アルバムへ移動
    for key in page_url_map.keys():
        # ディレクトリを作成
        os.makedirs(f'dist/{EVENT_ID}/{key}', exist_ok=True)

        driver.get(page_url_map[key])
        time.sleep(1)

        # class pagination__selected から 総ページ数を取得
        page_str = driver.find_element(By.CLASS_NAME, 'pagination__selected').text
        total_page = scrape_total_page(page_str)
        for i in range(total_page):
            print(f'{key} : {i + 1} / {total_page}')
            request_url = f'{page_url_map[key]}/{i + 1}'
            driver.get(request_url)
            print(f'Page URL : {request_url}')
            time.sleep(1)

            soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
            images = soup.select('img[draggable="false"]')
            for image in images:
                image_url = image['data-magnify-src']
                print(f'Image URL = {image_url}')
                dst_file_name = f'{image["alt"][:4]}.jpg'
                download_file(image_url, f'{EVENT_ID}/{key}/{dst_file_name}')


def scrape_total_page(raw_str: str) -> int:
    pages = raw_str.split('/')
    return int(pages[1].strip())


def download_file(url, dst_path):
    try:
        with request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode='wb') as local_file:
                local_file.write(data)
    except error.URLError as e:
        print(e)


if __name__ == '__main__':
    collect_image_url()
