# coding=utf-8
# author : yinkang
# data: 2019/12/17

import requests
import logging
from service import downloader
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

# 三种链接
# 1，时光网 ： 有特殊接口    http://video.mtime.com/76535/?mid=258576
# 2，猫眼 ： 无特殊接口，可直接在源代码获取   http://imovie.ewang.com/films/342146/preview?videoId=104305
# 3，苹果： 有接口： https://trailers.apple.com/trailers/paramount/gemini-man/
# 根据传入链接判断


class YuGaoPian():
    def __init__(self, url):
        # 'apple'站点不接受链接中有特殊空白
        self.start_url = url.strip()
        # 时光网会校验cookie，cookie维持时间暂时未知
        self.mtime_cookie = '_tt_=24614A24A168F8099AE24C5837A40B8B; yd_cookie=c49ee3d5-28bd-47e9c308a65c839b81188ef5fa417bd2f084; DefaultCity-CookieKey=364; DefaultDistrict-CookieKey=0; defaultCity=%25E5%25B9%25BF%25E4%25B8%259C%257C364; Hm_lvt_6dd1e3b818c756974fb222f0eae5512e=1576553900; _ydclearance=3c2000e3dad9267e493171e0-8ce8-41bb-a698-2d0a7db53c6b-1576568955; session_id=6683ABDD06EA03DCA8EF6E68ACBB69DD; userId=undefined; Hm_lpvt_6dd1e3b818c756974fb222f0eae5512e=1576561757'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
        }

    def spider_begin(self):
        if 'mtime' in self.start_url:
            self.headers['Cookie'] = self.mtime_cookie
        resp = requests.get(self.start_url, headers=self.headers)
        if len(resp.text) < 2000:
            # 页面被删除
            # ip被限制等
            logging.info('未知原因引起的页面错误')
            return
        video_url, title = self.parse_info(resp.text)
        self.down(video_url, title)

    def parse_info(self, content):
        # print(content)
        if "mtime.com" in self.start_url:
            title = re.search(r'"keywords":"(.*?)"', content, re.S).group(1)
            video_id = re.search(r'com/(.*?)/', self.start_url).group(1).strip()
            logging.info('[标题] %s  [视频id] %s', title, video_id)
            base_url = "http://shortvideo.mtime.cn/play/getPlayUrl?videoId={}&source=1&scheme=https"
            real_url = base_url.format(video_id)
            logging.info('[含有视频链接的链接信息] %s', real_url)
            resp = requests.get(real_url)
            video_urls = re.findall(r'"url":"(.*?)"', resp.text, re.S)
            video_urls = list(set(video_urls))
            for u in video_urls:
                if "_480" and "_1080" not in u:
                    video_url = u
                    break
                elif "_1080" in u:
                    video_url = u
                else:
                    video_url = u
            logging.info('[视频链接] %s', video_url)

        elif "imovie.ewang.com" in self.start_url:
            title = re.search(r'<title>(.*?)</title>', content).group(1)
            logging.info('[标题] %s', title)
            video_url = re.search(r'<source src="(.*?)" ', content).group(1)
            logging.info('[视频链接] %s', video_url)

        else:
            base_url = "https://trailers.apple.com/trailers/feeds/data/{}.json"
            title = re.search(r'paramount/(.*?)/', content, re.S).group(1).strip()
            video_id = re.search(r'/detail/(.*?)"', content, re.S).group(1).strip()
            logging.info('[标题] %s  [视频id] %s', title, video_id)
            real_url = base_url.format(video_id)
            logging.info('[含有视频链接的链接信息] %s', real_url)
            response = requests.get(real_url)
            video_urls = re.findall(r'"srcAlt":"(.*?)"', response.text, re.S)
            for u in video_urls:
                if "a720p" in u:
                    video_url = u
                    break
                else:
                    video_url = u
            logging.info('[视频链接] %s', video_url)
        return video_url, title

    def down(self, video_url, title):
        path = '{}.mp4'.format(title)
        result = downloader.down_file(video_url, path)
        if result:
            logging.info('[视频下载已完成] %s', path)
        else:
            logging.info('[视频下载异常] %s', path)


url = input('请输入链接：')
yugaopian = YuGaoPian(url)
yugaopian.spider_begin()
