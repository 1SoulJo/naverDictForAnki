# -*- coding: utf-8 -*-
import re
import scrapy
import time
from urllib.parse import urlparse, parse_qs

from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class NavermydictSpider(scrapy.Spider):
    name = 'naverMyDict'

    start_urls = [
        'https://learn.dict.naver.com/wordbook/enkodict/#/my/cards?'
        'wbId=b7ea85d9bc734c79bbab0028db15a8d5&qt=0&st=0&name=daily%20voca&tab=list'
    ]

    def __init__(self, name=None, **kwargs):
        options = Options()
        # options.add_argument('--headless')
        options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(chrome_options=options, executable_path='D:\Downloads\chromedriver.exe')

    def parse(self, response):
        self.driver.implicitly_wait(1)

        self.driver.get(response.url)
        # self.driver.get('file:///C:/Users/hansoljo/Desktop/voca_sample.html')

        titles = list()
        data = list()
        try:
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, "section_word_card")))

            while True:
                res = HtmlResponse(self.driver.current_url, body=self.driver.page_source, encoding='utf-8', request=None)

                cards = res.css('.inner_card')
                for card in cards:
                    word = dict()

                    title = card.css('.title::text').get()
                    title = re.sub('·', '', title).rstrip()

                    if title in titles:
                        continue
                    else:
                        titles.append(title)

                    word['title'] = title
                    word['means'] = list()

                    means = card.css('.item_mean')
                    for mean in means:
                        single_mean = dict()
                        pos = mean.css('.part_speech::text').get()
                        cont = ''.join(mean.xpath('.//*[contains(@class, "cont")]/text()').getall()).strip()

                        single_mean['pos'] = pos
                        single_mean['cont'] = cont
                        single_mean['exams'] = list()
                        exams = mean.css('.item_example')
                        for exam in exams:
                            org = exam.css('.origin::text').get()
                            trans = exam.css('.translate::text').get()
                            single_mean['exams'].append((org, trans))
                        word['means'].append(single_mean)

                    data.append(word)

                try:
                    next_btn = self.driver.find_element_by_css_selector('button.btn_next')
                    if next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(1)
                    else:
                        break
                except StaleElementReferenceException:
                    # try 1 more time
                    next_btn = self.driver.find_element_by_css_selector('button.btn_next')
                    if next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(1)
                    else:
                        break

            print(len(data))

            parts = urlparse(self.driver.current_url.replace('/#', ''))

            file_name = parse_qs(parts.query)['name'][0]

            with open('{}.tsv'.format(file_name), 'w', encoding='utf8') as f:
                for word in data:
                    means = word['means']
                    content_str = ''
                    for i, mean in enumerate(means):
                        content_str += '{}. <b>{}</b> {}<br>'.format((i+1), mean['pos'], mean['cont'])
                        if len(mean['exams']) > 0:
                            content_str += 'ex) {}<br>{}<br>'.format(mean['exams'][0][0], mean['exams'][0][1])
                        else:
                            content_str += '<br>'
                        content_str += '<br>'
                    f.write('{}\t{}'.format(word['title'], content_str))
                    f.write('\n')
        finally:
            self.driver.quit()

