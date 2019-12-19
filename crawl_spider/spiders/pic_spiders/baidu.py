# coding=utf-8
# author : yinkang
# data: 2019/12/18

# 命令行运行：python baidu.py -k 关键词 -n 需求图片数量

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


class BaiDuPic():
    def __init__(self, key, num):
        self.key = key
        self.num = num
        self.base_url = "https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&f" \
                "p=result&{}&cl=2&lm=-1&ie=utf-8&oe=utf-8" \
                "&adpicid=&st=&z=&ic=&hd=&latest=&copyright=&{}&" \
                "s=&se=&tab=&width=&height=&face=&istype=&qc=&nc=&fr=&expermode=&force=&pn={}&rn=30"

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0'
                          '.3440.75 Safari/537.36',
            'Host': 'image.baidu.com'
        }


    def spider_begin(self):
        logging.info('[需要下载的图片关键字为：] %s', self.key)
        pic_urls = self.parse_info()
        self.down(pic_urls)

    def parse_info(self):
        pic_urls = []
        x = int(self.num) // 30 + 1
        data1 = {
            'queryWord': self.key
        }
        data1 = parse.urlencode(data1)
        data2 = {
            'word': self.key
        }
        data2 = parse.urlencode(data2)
        for i in range(x):
            s = i*30
            pic_ajax_url = self.base_url.format(data1, data2, s)
            logging.info('[百度图片ajax链接：] %s ', pic_ajax_url)
            resp = requests.get(pic_ajax_url, headers=self.headers)
            content = resp.text
            # 每组ajax链接对应的30张图片链接
            urls = re.findall(r'"thumbURL":"(.*?)"', content, re.S)
            for i in urls:
                pic_urls.append(i)
        # logging.info(pic_urls)
        return pic_urls

    def down(self, pic_urls):
        path = '百度' + self.key
        pic_urls = pic_urls[0:int(self.num)]
        result = downloader.down_pic(path, pic_urls, self.headers)
        if result:
            logging.info('[主题图片下载已完成] %s', self.key)
        else:
            logging.info('[主题图片下载异常] %s', self.key)


key, num = start.get_pic_params()
bdp = BaiDuPic(key, num)
bdp.spider_begin()