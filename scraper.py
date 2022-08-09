import os
import time
from flask import Flask, render_template, request
from flask_cors import cross_origin
from selenium import webdriver
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/scraper',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
                def scroll_to_end(wd):
                    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(sleep_between_interactions)

                # Google Search Link

                search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

                # load the page
                wd.get(search_url.format(q=query))

                image_urls = set()
                image_count = 0
                results_start = 0
                while image_count < max_links_to_fetch:
                    scroll_to_end(wd)

                    # get all image thumbnail results
                    thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
                    number_results = len(thumbnail_results)

                    print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

                    for img in thumbnail_results[results_start:number_results]:
                        try:
                            img.click()
                            time.sleep(sleep_between_interactions)
                        except Exception:
                            continue

                        # extract image url
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


            def persist_image(folder_path:str,url:str, counter):
                try:
                    image_content = request.get(url).content

                except Exception as e:
                    print(f"ERROR - Could not download {url} - {e}")

                try:
                    f = open(os.path.join(folder_path, 'jpg' + "_" + str(counter) + ".jpg"), 'wb')
                    f.write(image_content)
                    f.close()
                    print(f"SUCCESS - saved {url} - as {folder_path}")
                except Exception as e:
                    print(f"ERROR - Could not save {url} - {e}")


            def search_and_download(search_term: str, driver_path: str, target_path='./images', number_images=10):
                target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))

                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)

                with webdriver.Chrome(executable_path=driver_path) as wd:
                    res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5)

                counter = 0
                for elem in res:
                    persist_image(target_folder, elem, counter)
                    counter += 1


            DRIVER_PATH = r'chromedriver.exe'
            if request.form.get('action1') == 'search_term':
                search_term = ''

                search_and_download(search_term=search_term, driver_path=DRIVER_PATH, number_images=10)
        except Exception as e:
            print('The Exception message is: ', e)
            return 'something is wrong'
            # return render_template('results.html')
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8001, debug=True)
# app.run(debug=True)
