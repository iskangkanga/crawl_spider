# coding=utf-8
# author : yinkang
# data: 2019/12/17
# 说明：对于重名古诗，优先下载网站给出的优先级最高的，搜索结果与网站有关，与代码无关
# 个别古诗在搜索关键字时，返回结果不正确，系网站搜索结果，如：搜索‘无衣’，返回结果第一篇为‘乌衣巷’

import logging
import re
import requests
from service import downloader

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


class GuShiWen():
    def __init__(self, keyword):
        self.keyword = keyword
        # https://so.gushiwen.org/search.aspx?value=%E8%B5%A0%E6%B1%AA%E4%BC%A6
        self.base_url = 'https://so.gushiwen.org/search.aspx?value={}'
        self.real_url = self.base_url.format(self.keyword)
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }

    def spider_begin(self):
        logging.info('[需要下载的古诗为：] %s', self.keyword)
        logging.info('[对应链接为：] %s', self.real_url)
        resp = requests.get(self.real_url, headers=self.headers)
        if len(resp.text) < 7000:
            # 页面被删除
            # ip被限制等
            logging.info('未知原因引起的页面错误')
            return
        poems, author, dys = self.parse_info(resp.text)
        self.down(poems, author, dys)

    def parse_info(self, content):
        # print(content)
        poems = re.search('<div class="contson".*?>(.*?)</div>', content, re.S).group(1).strip()
        poems = re.sub('<p>|</p>', '', poems)
        poems = poems.split('<br />')
        logging.info('[诗文：] %s', poems)
        author = re.search(r'<div class="cont">.*?<p class="source">.*?<a.*?>.*?</a>.*?<a.*?>(.*?)</a>', content,
                           re.S).group(1).strip()
        dys = re.search(r'<div class="cont">.*?<p class="source">.*?<a.*?>(.*?)</a>', content, re.S).group(1).strip()
        logging.info('[作者：] %s [朝代：] %s ', author, dys)
        return poems, author, dys

    def down(self, poems, author, dys):
        title = self.keyword
        result = downloader.write_file(title, poems, author, dys)
        if result:
            logging.info('[文件下载已完成] %s', title)
        else:
            logging.info('[文件下载异常] %s', title)


keyword = input('请输入古诗名：')
gushiwen = GuShiWen(keyword)
gushiwen.spider_begin()
