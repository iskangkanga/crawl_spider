# coding=utf-8
# author : yinkang
# data: 2019/12/17

# 命令行运行：python hanjutv.py -u 链接

import os
import sys

par_dir = os.path.dirname(os.path.abspath(__file__)) + '/../..'
os.chdir(par_dir)
sys.path.append(par_dir)

import requests
import logging
from service import downloader, start
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

# https://www.hanjutv.com/player/35437.html
class HanJuTV():
    def __init__(self, url):
        self.start_url = url.strip()
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'referer': url,
            'sec-fetch-mode': 'nested-navigate',
            'sec-fetch-site': 'same-site',
            'upgrade-insecure-requests': '1'
        }

        self.headers2 = {
            'origin': 'https://ww4.hanjutv.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/78.0.3904.97 Safari/537.36 '
        }

    def spider_begin(self):
        logging.info('[已选择下载链接] %s', self.start_url)
        resp = requests.get(self.start_url)
        # 网页进行了gzip压缩
        content = resp.content.decode('UTF-8')
        if len(content) < 50:
            # 页面被删除
            # ip被限制等
            logging.info('未知原因引起的页面错误')
            return
        video_url, title = self.parse_info(content)
        self.down(video_url, title)

    def parse_info(self, content):
        # print(content)
        re_str = re.compile('<iframe.*?id="playPath".*?src="(.*?)".*?></iframe>')
        js_urls = re_str.findall(content)
        if js_urls:
            js_url = "https:" + js_urls[0]
            self.headers2['referer'] = js_url
            logging.info('[需请求的js链接] %s', js_url)
        else:
            logging.info('解析出现问题')
            return
        title = re.search('<title>(.*?)</title>', content, re.S).group(1).strip()
        title = re.sub(' ', '', title)
        logging.info('[标题] %s', title)
        resp = requests.get(js_url, headers=self.headers)
        video_url = re.search(r"url:'(.*?)'", resp.text, re.S).group(1).strip()
        logging.info('[视频链接] %s', video_url)
        return video_url, title

    def down(self, video_url, title):
        path = '{}.mp4'.format(title)
        # 加密m3u8下载方法（目前来说，只有该网站需要解密，故下载方法不一定具有通用性，如果后续遇见会加以更改）
        result = downloader.down_s_m3u8_file(video_url, path, self.headers2)
        if result:
            logging.info('[视频下载已完成] %s', path)
        else:
            logging.info('[视频下载异常] %s', path)


url = start.get_video_url()
hjtv = HanJuTV(url)
hjtv.spider_begin()