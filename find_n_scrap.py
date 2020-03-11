import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
import os 
import time
import io
from PIL import Image
from selenium.webdriver.chrome.options import Options

chrome_options = Options()  
chrome_options.add_argument("--headless")

DRIVER_PATH = 'chromedriver.exe'
amount_of_picture = 10
# test
# wd.get('https://google.com')
# search_box = wd.find_element_by_css_selector('input.gLFyf')
# search_box.send_keys('cats')

def fetch_image_urls(query:str, max_links_to_fetch:int, wd:webdriver, sleep_between_interactions:int=1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)    
    
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    wd.get(search_url.format(q=query))

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)
        
        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")
        
        for img in thumbnail_results[results_start:number_results]:
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} image links, done!")
                break
        else:
            print("Found:", len(image_urls), "image links, looking for more ...")
            time.sleep(30)
            return
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        results_start = len(thumbnail_results)

    return image_urls

idx = 0
def persist_image(folder_path:str,url:str):
    global idx
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path,str(idx) + '.jpg')
        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=85)
        print(f"Saved {url} - as {file_path}")
        idx +=1
    except Exception as e:
        print(f"Could not save {url} - {e}")
    
def search_and_download(search_term:str,driver_path:str,target_path='images',number_images=amount_of_picture):
    target_folder = os.path.join(target_path,'_'.join(search_term.lower().split(' ')))

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    with webdriver.Chrome(executable_path=driver_path,chrome_options=chrome_options) as wd:
        res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5)
        
    for elem in res:
        persist_image(target_folder,elem)

wikipage = "https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_ng%C3%A2n_h%C3%A0ng_t%E1%BA%A1i_Vi%E1%BB%87t_Nam"
result = requests.get(wikipage)
print(result)

if result.status_code == 200:
    soup = BeautifulSoup(result.content, "html.parser")
    
new_table = []
for ta in soup.find_all('table',{'class':'wikitable sortable'}):
    for row in ta.find_all('tr')[1:]:
        column_marker = 0
        columns = row.find_all('td')
        new_table.append([column.get_text() for column in columns])  

bank_name = []
df = pd.DataFrame(new_table, columns=['stt','ten ngan hang','ten ngan hang tieng anh','ten giao dich','von dieu le','trang chu','ngay cap nhat'])
# print(df.head())
for col in df['ten giao dich']: 
    if col != '\n':
        bank_name.append(col)

for i in bank_name:
    search_and_download(search_term=i,driver_path=DRIVER_PATH)