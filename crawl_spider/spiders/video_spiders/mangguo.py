# coding=utf-8
# author : yinkang
# data: 2019/12/17

# 命令行运行：python mangguo.py -u 链接

import os
import sys

par_dir = os.path.dirname(os.path.abspath(__file__)) + '/../..'
os.chdir(par_dir)
sys.path.append(par_dir)

import base64
import time

import requests
import logging
from service import downloader, start
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

class MangGuo():
    def __init__(self, url):
        self.start_url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36 Maxthon/5.1.3.2000',
            'Referer': self.start_url,
            'Cookie': 'PM_CHKID=1'
        }
        # 第一个接口，返回tk2和pm2两个重要参数
        # https://pcweb.api.mgtv.com/player/video?
        # did=f8fdc5ea-bbf8-439d-abc9-e0cf5526e296& (固定参数，短期不改变，可不要)
        # suuid=b2a902c7-0591-450f-8289-4598df77a3a7&  （该参数可以不要）
        # cxid=&   （可不要）
        # tk2=5kDNyADOzcTNx0Ddpx2Y8FDMzAjLz4CM9IXZ2xHMzATM98mbwxnN5ITZ2ITN1Y2YwUWL5MmYh1CZ5MDNtgjZiJWLhVWNjRmZ4YWPklGZ     （主要参数，动态生成）
        # &video_id=6872640  （主要参数，视频id）
        # &type=pch5  （可不要）
        # &_support=10000000  （可不要）
        # &callback=jsonp_1573802499794_75476  （可不要）
        self.base_url1 = 'https://pcweb.api.mgtv.com/player/video?tk2={}&video_id={}'

        # 上一步获取的两个参数，构造新接口
        # https://pcweb.api.mgtv.com/player/getSource?
        # _support=10000000&  （可不要）
        # tk2=5QTN3kzNzcTNx0Ddpx2Y8FDMzAjLz4CM9IXZ2xHMzATM98mbwxnN5ITZ2ITN1Y2YwUWL5MmYh1CZ5MDNtgjZiJWLhVWNjRmZ4YWPklGZ
        # &pm2=Cy64ZkV~ia6XZlAVnC6C~YudJOehxE2YJTsGOS022aQ7YHd9nfIB9183zCmZ_SrZWQjWhaHKZUhOSg5qiPsQpSo~XOxfSML4QslvZJBOVAXuIF82vGtJLZEFggGYiFKONAPFtBW315eO6pq5rr9oAOJn7KaCsJzZS02tBDK8ZA1KiW9afhTVDEQKnD5Z~Dqt8ZubP~fuvCOrWxog8nUfXHnaxcoo9N2zu62qDnnbCI3XrOPwTDkRsFcd2CXpyXVUJ6hrIniJl2RjhJo67FV2idFQ2dWY0rU~ZE5SQtJx6pbsKFBOqx6wsszu7SuEvlRrf9nB40k4IhI-
        # &video_id=6872640&type=pch5
        # &callback=jsonp_1573797549382_37402  （可不要）
        self.base_url2 = "https://pcweb.api.mgtv.com/player/getSource?tk2={}&pm2={}&video_id={}"

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
        # print(content)
        title = re.search('<title>(.*?)</title>', content, re.S).group(1).strip()
        # 空白符会导致ffmpeg合并失败
        title = re.sub(' ', '', title)
        video_id = re.search('(\d+)\.html', self.start_url).group(1).strip()
        logging.info('[标题] %s  [视频id] %s', title, video_id)
        return video_id, title


    def get_params(self, video_id):
        # tk2生成
        t = int(time.time())
        clit = "clit=" + str(t)
        s = "did=f8fdc5ea-bbf8-439d-abc9-e0cf5526e296|pno=1030|ver=0.3.0301|" + clit
        s64 = base64.b64encode(s.encode(encoding='utf-8')).decode(encoding='utf-8')
        s64 = list(s64.replace("/\+/g", "_").replace("/\//g", "~").replace("/=/g", "-"))
        s64.reverse()
        s64 = "".join(s64)
        tk2 = s64
        logging.info('[第一个tk2：] %s ', tk2)

        resp_1 = requests.get(self.base_url1.format(tk2, video_id), headers=self.headers)
        pm2 = re.search('"pm2":"(.*?)"', resp_1.text, re.S).group(1).strip()
        tk2_2 = re.search('"tk2":"(.*?)"', resp_1.text, re.S).group(1).strip()
        logging.info('[第二个tk2：] %s [pm2] %s ', tk2_2, pm2)

        resp_2 = requests.get(self.base_url2.format(tk2_2, pm2, video_id), headers=self.headers)
        # print(resp_2.text)
        urls = re.findall('"url":"(.*?)"', resp_2.text, re.S)
        domins = re.findall('(http://web-disp\d?.titan.mgtv.com)', resp_2.text, re.S)

        # 根据域名和链接构造新接口
        # 域名都可以用，最后一个链接是清晰度最高的
        info_url = domins[1] + urls[-1]
        logging.info('[info_url：] %s ', info_url)
        resp_3 = requests.get(info_url, headers=self.headers)
        # print(resp_3.text)
        # 从返回的数据找到真实的m3u8链接
        # 这个链接浏览器打不开，校验了数据
        m3u8_url = re.search('"info":"(.*?)"', resp_3.text, re.S).group(1).strip()
        logging.info('[video_url] %s ', m3u8_url)
        return m3u8_url

    def down(self, video_url, title):
        path = '{}.mp4'.format(title)
        result = downloader.down_m3u8_file(video_url, path, self.headers)
        if result:
            logging.info('[视频下载已完成] %s', path)
        else:
            logging.info('[视频下载异常] %s', path)


# https://www.mgtv.com/b/331915/6872640.html
url = start.get_video_url()
mg = MangGuo(url)
mg.spider_begin()