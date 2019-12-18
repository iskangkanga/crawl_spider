# coding=utf-8
# author : yinkang
# data: 2019/12/17

import base64
import binascii
import random

import requests
import logging
from service import downloader
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


class BanCiYuan():
    def __init__(self, url):
        self.start_url = url
        self.headers = headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        self.base_url = "https://ib.365yg.com/video/urls/v/1/toutiao/mp4/{}?r={}&s={}"

    def spider_begin(self):
        logging.info('[已选择下载链接] %s', self.start_url)
        requests.packages.urllib3.disable_warnings()
        resp = requests.get(self.start_url, headers=self.headers, verify=False)
        if len(resp.text) < 50:
            # 页面被删除
            # ip被限制等
            logging.info('未知原因引起的页面错误')
            return
        video_id, title = self.parse_info(resp.text)
        video_url = self.get_params(video_id)
        self.down(video_url, title)

    def parse_info(self, content):
        video_ids = re.findall(r'"video_info\\":{\\"vid\\":\\"(.*?)\\"', content, re.S)
        title = re.search('<title>(.*?)</title>', content, re.S).group(1).strip()
        video_id = video_ids[0]
        logging.info('[标题] %s  [视频id] %s', title, video_id)
        return video_id, title

    def get_params(self, video_id):
        # 参数r是16到18位的随机数
        r = []
        x = random.randint(16, 18)
        for i in range(x):
            a = random.randint(0, 9)
            a = str(a)
            r.append(a)
        r = "".join(r)
        # 参数s是crc32校验后的数字
        u = "/video/urls/v/1/toutiao/mp4/{}?r={}"
        t = bytes(u.format(video_id, r), encoding="utf-8")
        s = binascii.crc32(t)
        logging.info('[参数r] %s  [参数s] %s', r, s)
        requests.packages.urllib3.disable_warnings()
        resp = requests.get(self.base_url.format(video_id, r, s), verify=False)
        video_urls_base64 = re.findall(r'"backup_url_1":"(.*?)"', resp.text)
        # print(video_urls_base64)
        # 如果匹配到3或者3个以上的编码url
        # 清晰度分别为360 480 720 1080
        # 判断有几个链接，获取720
        if len(video_urls_base64) >= 3:
            video_url_base64 = video_urls_base64[2]
        # 无720，获取最高清晰度
        else:
            video_url_base64 = video_urls_base64[-1]
        video_url = base64.b64decode(video_url_base64.encode('utf-8'))
        video_url = str(video_url, 'utf-8')
        logging.info('[视频链接] %s ', video_url)
        return video_url

    def down(self, video_url, title):
        path = '{}.mp4'.format(title)
        result = downloader.down_file(video_url, path, self.headers)
        if result:
            logging.info('[视频下载已完成] %s', path)
        else:
            logging.info('[视频下载异常] %s', path)


# https://bcy.net/item/detail/6751173433834340622?_source_page=video&_sub_channel_name=%E8%90%8C%E5%AE%A0
url = input('请输入链接：')
bcy = BanCiYuan(url)
bcy.spider_begin()
