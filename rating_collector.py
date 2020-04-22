from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from multiprocessing import Process, Manager
import time
import csv
import logging
from pymongo import MongoClient


DELAY = 0.5
DRIVER_PATH = '/Users/xing/Executable/chromedriver'
GOODREADS_SEARCH = 'https://www.goodreads.com/search?q='
logging.basicConfig(level=logging.INFO)
PUNCT = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''


def remove_punct(str):
    no_punct = ""
    for char in str:
        if char not in PUNCT:
            no_punct = no_punct + char
    return no_punct


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def write_csv(data_list, fields_list, filename):
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields_list)
        writer.writeheader()
        for data in data_list:
            writer.writerow(data)


def crawling_worker(email, password, titles, db_handle):
    options = webdriver.ChromeOptions()

    prefs = {
        'profile.default_content_setting_values': {
            'notifications': 2
        }
    }
    # Don't show GUI.
    options.add_argument('headless')
    # Ignore browser prompts.
    options.add_experimental_option('prefs', prefs)
    chrome = webdriver.Chrome(DRIVER_PATH, options=options)
    chrome.get('https://www.goodreads.com')
    time.sleep(DELAY)
    email_form = chrome.find_element_by_name('user[email]')
    password_form = chrome.find_element_by_name('user[password]')
    email_form.send_keys(email)
    password_form.send_keys(password)
    try:
        login_button = chrome.find_element_by_xpath('//input[@type="submit"]')
    except NoSuchElementException:
        login_button = chrome.find_element_by_xpath('//input[@value="登录"]')
    login_button.click()
    time.sleep(DELAY)

    # Crawl book ratings.
    for title in titles:
        # Opens a new tab.
        # chrome.execute_script("window.open()")
        # Switch to the newly opened tab.
        # chrome.switch_to.window(chrome.window_handles[1])
        # Search book in the search bar.
        t = remove_punct(title)
        chrome.get(GOODREADS_SEARCH + t.replace(' ', '+'))
        time.sleep(DELAY)

        # Get the rating and rating_count (to-do).
        table = chrome.find_element_by_xpath('//table[@class="tableList"]')
        candidates = table.find_elements_by_xpath('//tbody/tr')
        rating = -1
        for book in candidates:
            # The second td label contains info
            book = book.find_elements_by_xpath('//td')[1]
            # Title of the candidate
            str = book.find_element_by_xpath('//a[@class="bookTitle"]/span').text
            str = remove_punct(str)
            if t.lower() in str.lower():  # If title of the candidate contains the book title, it's the right one
                rating_field = book.find_elements_by_xpath('//div')[0]  # First div lable contains info
                # Raw text containig info "3.69 avg rating — 124 ratings"
                raw_text = rating_field.find_element_by_xpath('//span/span[@class="minirating"]').text
                try:
                    rating = float(raw_text[:4])
                except:
                    print('Converting rating failed!')
                break
        print('{}: {}'.format(title, rating))
        coll.update_one({'title': title}, {'$set': {'rating': rating}})
    chrome.quit()


if __name__ == '__main__':
    # Get mongodb connection
    client = MongoClient('localhost', 27017)
    db = client['books']
    coll = db['book']

    # Credential used to crawl data.
    cred = {'email': '***', 'pass': '***'}

    # Get book title list
    title_list = list()
    for title in coll.find({}, {'title': 1, '_id': 0}):
        title_list.append(title['title'])
    # title_chunks = list(divide_chunks(title_list, 600))

    print('Started crawling...')
    crawling_worker(cred['email'], cred['pass'], title_list, coll)

    # Start to crawl ratings in different chunks using multi processing.
    # manager = Manager()
    # result_list = manager.list()
    # jobs = list()
    # for chunk in title_chunks:
    #     p = Process(target=crawling_worker, args=(cred['email'],
    #                                               cred['pass'],
    #                                               chunk,
    #                                               result_list))
    #     jobs.append(p)
    #     p.start()
    #
    # # Wait for all processes finish.
    # for proc in jobs:
    #     proc.join()

    print('Finished crawling!')




