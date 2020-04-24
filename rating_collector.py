from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from multiprocessing import Process, Manager
import time
import csv
import logging
from pymongo import MongoClient

DELAY = 0.3
DRIVER_PATH = '/Users/xing/Executable/chromedriver'
GOODREADS_SEARCH = 'https://www.goodreads.com/search?q='
PUNCT = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
CREDENTIAL = 'credential.txt'
logging.basicConfig(level=logging.INFO)


def remove_punct_n_lower(str):
    no_punct = ""
    for char in str:
        if char not in PUNCT:
            no_punct = no_punct + char
    return no_punct.lower()


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
        t = remove_punct_n_lower(title)
        chrome.get(GOODREADS_SEARCH + t.replace(' ', '+'))
        time.sleep(DELAY)
        print('======== ******** ========')
        print('Title: {}'.format(t))
        rating = 1.00
        rating_count = 0
        # Get the rating and rating_count (to-do).
        try:
            table = chrome.find_element_by_xpath('//table[@class="tableList"]/tbody')
            candidates = table.find_elements_by_xpath('./tr')
        except NoSuchElementException:
            print('Element not found!')
            coll.update_one({'title': title}, {'$set': {'rating': rating, 'rating_count': rating_count}})
            continue

        for book in candidates:
            # The second td label contains rating and rating_count info
            book = book.find_elements_by_xpath('./td')[1]
            # Title of the candidate
            str = book.find_element_by_xpath('./a[@class="bookTitle"]/span').text
            str = remove_punct_n_lower(str)
            print('Searched result: {}'.format(str))
            if t in str:  # If title of the candidate contains the book title, it's the right one
                rating_field = book.find_elements_by_xpath('./div')[0]  # First div lable contains rating info
                # Raw text containig info "3.69 avg rating — 124 ratings"
                raw_text = rating_field.find_element_by_xpath('./span/span[@class="minirating"]').text
                try:
                    rating = float(raw_text[:4])
                    i = raw_text.find('rating ')
                    j = raw_text.find(' ratings')
                    rating_count = int(raw_text[i+9:j])
                except:
                    print('Converting rating failed!')
                break
        print('{}: rating: {} count: {}'.format(t, rating, rating_count))
        print()
        db_handle.update_one({'title': title}, {'$set': {'rating': rating, 'rating_count': rating_count}})
    chrome.quit()


if __name__ == '__main__':
    # Get mongodb connection
    client = MongoClient('localhost', 27017)
    db = client['books']
    coll = db['books']

    # Credential used to crawl data.
    with open(CREDENTIAL) as f:
        vals = f.readline().split(' ')
    cred = {'email': vals[0], 'pass': vals[1]}

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
