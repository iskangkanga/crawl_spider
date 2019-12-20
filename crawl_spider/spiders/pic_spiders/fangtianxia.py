# coding=utf-8
# author : yinkang
# data: 2019/12/20

# 图片数量不足时，不会找不到页面，但是最后一张图会一直重复

import os
import sys

par_dir = os.path.dirname(os.path.abspath(__file__)) + '/../..'
os.chdir(par_dir)
sys.path.append(par_dir)

import requests
import logging
from service import downloader, start
import re
from urllib import parse

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


class FangTianXia():
    def __init__(self, key, num):
        self.name = key
        # 编码是GBK，不然会乱码
        self.key = parse.quote(key, encoding='GBK')
        self.num = int(num)
        self.base_url = 'https://home.fang.com/album/search/?keyword={}&sortid=24&page={}'
        self.page = self.num // 36 + 1

    def spider_begin(self):
        pic_urls = []
        for i in range(1, int(self.page+1)):
            url = self.base_url.format(self.key, i)
            logging.info('[含有图片的链接] %s ', url)
            resp = requests.get(url)
            if resp.status_code >= 400:
                logging.info('未知原因引起的页面错误')
                sys.exit()
            content = resp.text
            urls = re.findall('src="(.*?jpg)"', content)
            for u in urls:
                u = 'http:' + u
                pic_urls.append(u)
        pic_urls = pic_urls[0:self.num]
        self.down(pic_urls)

    def parse_info(self):
        pass

    def down(self, pic_urls):
        path = '房天下' + self.name
        result = downloader.down_pic(path, pic_urls)
        if result:
            logging.info('[主题图片下载已完成] %s', self.name)
        else:
            logging.info('[主题图片下载异常] %s', self.name)


key, num = start.get_pic_params()
ftx = FangTianXia(key, num)
ftx.spider_begin()
