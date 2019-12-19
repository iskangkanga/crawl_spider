# coding=utf-8
# author : yinkang
# data: 2019/12/16

# 命令行运行：python 163.py -u 链接

import os
import sys

par_dir = os.path.dirname(os.path.abspath(__file__)) + '/../..'
os.chdir(par_dir)
sys.path.append(par_dir)

import re
import requests
from Crypto.Cipher import AES
import base64
import logging
from service import downloader,start

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


class WangYiYun():
    # https://music.163.com/video?id=6BCF37708A8DE2B5A6D8487D519CC02D
    def __init__(self, url):
        self.start_url = url
        self.info_url = 'https://music.163.com/weapi/cloudvideo/playurl?csrf_token='
        self.first_param = r'{ ids: "[\"%s\"]", resolution: "1080", csrf_token: "" }'
        self.second_param = "010001"
        self.third_param = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        self.forth_param = "0CoJUm6Qyw8W8jud"
        self.iv = '0102030405060708'
        self.key = 16 * 'F'
        self.encSecKey = "257348aecb5e556c066de214e531faadd1c55d814f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3881736d94a02ca919d952872e7d0a50ebfa1769a7a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0dba6d6f7249b06f5965ecfff3695b54e1c28f3f624750ed39e7de08fc8493242e26dbc4484a01c76f739e135637c"
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'referer': self.start_url,
        }

    def spider_begin(self):
        # 爬虫开始，调用需要调用的方法，获取需要获取的参数
        logging.info('[已选择下载链接] %s', self.start_url)
        requests.packages.urllib3.disable_warnings()
        resp = requests.get(self.start_url, headers=self.headers)
        if len(resp.text) < 50:
            # 页面被删除
            # ip被限制等
            logging.info('未知原因引起的页面错误')
            return
        # 获取标题与视频id
        title, video_id = self.parse_info(resp.text)
        # 获取需要上传的post表单参数一
        h_encText = self.get_params(video_id)
        # 获取视频原链
        video_url = self.get_real_url(h_encText)
        # 执行下载
        self.download(video_url, title)

    def parse_info(self, content):
        title = re.search('<title>(.*?)</title>', content, re.S).group(1).strip()
        video_id = re.search('id=(.*?)$', self.start_url, re.S).group(1).strip()
        logging.info('[标题] %s  [视频id] %s', title, video_id)
        return title, video_id

    def get_params(self, video_id):
        h_encText = self.AES_encrypt(self.first_param % video_id, self.forth_param, self.iv)
        h_encText = self.AES_encrypt(h_encText, self.key, self.iv)
        logging.info('[上传表单参数] %s', h_encText)
        return h_encText

    def AES_encrypt(self, text, key, iv):
        if type(text) == type(b'123'):  # 这是判断当前变量的类型是bytes还是字符串，因为pycryptodome要求参数要是字节类型
            text = text.decode('utf-8')
        pad = 16 - len(text) % 16  # 加密的位数是16的位数，不够的话进行补上

        text = text + pad * chr(pad)

        iv = iv.encode('utf-8')
        key = key.encode('utf-8')
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        text = text.encode('utf-8')
        encrypt_text = encryptor.encrypt(text)
        encrypt_text = base64.b64encode(encrypt_text)
        return encrypt_text

    def get_real_url(self, h_encText):
        p = {
            'params': h_encText,

            'encSecKey': self.encSecKey

        }
        resp = requests.post(self.info_url, params=p, headers=self.headers)
        video_url = re.search('"url":"(.*?)"', resp.text, re.S).group(1).strip()
        logging.info('[视频链接] %s', video_url)
        return video_url

    def download(self, video_url, title):
        path = '{}.mp4'.format(title)
        result = downloader.down_file(video_url, path, self.headers)
        if result:
            logging.info('[视频下载已完成] %s', path)
        else:
            logging.info('[视频下载异常] %s', path)


url = start.get_video_url()
WangYispider = WangYiYun(url)
WangYispider.spider_begin()
