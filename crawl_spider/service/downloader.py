# coding=utf-8
# author : yinkang

import datetime
import logging
import os
import re
import threading
import time
from queue import Queue
from moviepy.editor import VideoFileClip
from urllib import request

import requests
from Crypto.Cipher import AES

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


# 视频下载方法
def down_file(video_url, path, headers=None):
    root = 'cache/'
    flag = os.path.exists(root)
    if flag:
        pass
    else:
        os.mkdir(root)

    file_name = path
    start_time = time.time()
    url = video_url
    requests.packages.urllib3.disable_warnings()
    resp = requests.get(url, stream=True, verify=False)
    # 对链接发起请求，获取返回的头信息，包含链接对应的文件大小
    headers = resp.headers
    # 获取返回的头信息中文件大小，当前单位为B，转化为MB
    c_length = headers['Content-Length']
    if c_length:
        all_size = int(c_length) / 1024 / 1024
        all_size = ("%.2f" % all_size)
    else:
        all_size = '未知大小'
    # 下载尺寸初始为0
    down_size = 0
    with open('cache/' + file_name, 'wb') as f:
        for chunk in resp.iter_content(10240):
            if chunk:
                try:
                    f.write(chunk)
                    # 目前文件大小
                    now_size = down_size / 1024 / 1024
                    now_size = ("%.2f" % now_size)
                    # 每次写入，文件增加
                    down_size += len(chunk)
                    # 下载速度，这是总速度，注意初始时间的位置和文件置零的位置，都在循环外
                    down_speed = down_size / 1024 / (time.time() - start_time)
                    down_speed = ("%.2f" % down_speed)
                    # 单行打印
                    print("\r", file_name, ' 下载中',
                          ' {} KB/s - {} MB, 共 {} MB'.format(down_speed, now_size, all_size), end="", flush=True)
                except:
                    logging.info('下载异常')
                    return False
        print('\n')
        return True


# 文件写入方法
def write_file(path, content, author, dys=None):
    root = 'cache/'
    flag = os.path.exists(root)
    if flag:
        pass
    else:
        os.mkdir(root)
    file_name = path
    try:
        with open('cache/%s.txt' % file_name, 'a', encoding='utf-8') as fp:
            fp.write(author)
            fp.write('\n')
    except:
        logging.info('文件写入作者时异常')
        return False

    if dys:
        try:
            with open('cache/%s.txt' % file_name, 'a', encoding='utf-8') as fp:
                fp.write(dys)
                fp.write('\n')
        except:
            logging.info('文件写入朝代时异常')
            return False

    try:
        with open('cache/%s.txt' % file_name, 'a', encoding='utf-8') as fp:
            for c in content:
                fp.write(c)
                fp.write('\n')
    except:
        logging.info('文件写入内容时异常')
        return False
    return True


# 无加密m3u8文件下载
def down_m3u8_file(video_url, path, headers):
    root = 'cache/'
    flag = os.path.exists(root)
    if flag:
        pass
    else:
        os.mkdir(root)

    name = path
    url = video_url
    # 适用多数而非全部
    base_url = re.split(r"[a-zA-Z0-9-_\.]+\.m3u8", url)[0]
    start = datetime.datetime.now().replace(microsecond=0)
    logging.info('文件开始写入')
    s, concatfile = parse2(headers, url, base_url)
    print('\n')
    logging.info('文件写入结束')
    # 获取队列元素数量
    num = s.qsize()
    # 根据数量来开线程数，每五个元素一个线程
    # 最大开到50个
    logging.info('下载任务开始')
    if num > 5:
        t_num = num // 5
    else:
        t_num = 1
    if t_num > 20:
        t_num =20
    # print(s,concatfile)
    threads = []
    for i in range(t_num):
        t = threading.Thread(target=run, name='th-' + str(i), kwargs={'ts_queue': s, 'headers': headers})
        t.setDaemon(True)
        threads.append(t)
    for t in threads:
        time.sleep(0.4)
        t.start()
    for t in threads:
        t.join()
    print('\n')
    merge(concatfile, name)
    remove(concatfile)
    over = datetime.datetime.now().replace(microsecond=0)
    logging.info('[任务总时长：] %s ', over - start)
    result = get_video_legth(name)
    return result

# 预下载，获取m3u8文件，读出ts链接，并写入文档
def parse2(headers, url, base_url):
    # 当ts文件链接不完整时，需拼凑
    resp = requests.get(url, headers=headers)
    m3u8_text = resp.text
    # print(m3u8_text)
    # 按行拆分m3u8文档
    ts_queue = Queue(10000)
    lines = m3u8_text.split('\n')
    s = len(lines)
    # 找到文档中含有ts字段的行
    concatfile = 'cache/' + "s" + '.txt'
    for i,line in enumerate(lines):
        if '.ts' in line:
            if 'http' in line:
                # print("ts>>", line)
                ts_queue.put(line)
            else:
                line = base_url + line
                ts_queue.put(line)
                # print('ts>>',line)
            filename = re.search('([a-zA-Z0-9-_]+.ts)', line).group(1).strip()
            # 一定要先写文件，因为线程的下载是无序的，文件无法按照
            # 123456。。。去顺序排序，而文件中的命名也无法保证是按顺序的
            # 这会导致下载的ts文件无序，合并时，就会顺序错误，导致视频有问题。
            open(concatfile, 'a+').write("file %s\n" % filename)
            print("\r", '文件写入中', i, "/", s, end="", flush=True)
    return ts_queue, concatfile

# 线程模式，执行线程下载
def run(ts_queue, headers):
    num = 3
    while not ts_queue.empty():
        url = ts_queue.get()
        filename = re.search('([a-zA-Z0-9-_]+.ts)', url).group(1).strip()
        try:
            requests.packages.urllib3.disable_warnings()
            r = requests.get(url, stream=True, headers=headers, verify=False)
            with open('cache/' + filename, 'wb') as fp:
                for chunk in r.iter_content(5242):
                    if chunk:
                        fp.write(chunk)
            print("\r", '任务文件 ', filename, ' 下载成功', end="", flush=True)
        except:
            logging.info('[任务文件 ], %s, [ 下载失败]', filename)
            ts_queue.put(url)
            num -= 1


# 加密的m3u8视频多线程下载方法, 包括合并与删除冗余等操作
def down_s_m3u8_file(video_url, path, headers):
    root = 'cache/'
    flag = os.path.exists(root)
    if flag:
        pass
    else:
        os.mkdir(root)
    name = path
    url = video_url
    start = datetime.datetime.now().replace(microsecond=0)
    logging.info('文件开始写入')
    ts_queue, concatfile, key_url = parse(url, headers)
    print('\n')
    logging.info('文件写入结束')
    # 把key链接传给方法解析key值
    cryptor = get_key(key_url, headers)
    # 获取队列元素数量
    num = ts_queue.qsize()
    # 根据数量来开线程数，每五个元素一个线程
    # 最大开到20个
    logging.info('下载任务开始')
    if num > 5:
        t_num = num // 5
    else:
        t_num = 1
    if t_num > 20:
        t_num = 20
    threads = []
    for i in range(t_num):
        t = threading.Thread(target=down, name='th-' + str(i),
                             kwargs={'ts_queue': ts_queue, 'headers': headers, 'cryptor': cryptor})
        t.setDaemon(True)
        threads.append(t)
    for t in threads:
        # time.sleep(0.4)
        t.start()
    for t in threads:
        t.join()
    print('\n')
    logging.info('下载任务结束')
    merge(concatfile, name)
    remove(concatfile)
    over = datetime.datetime.now().replace(microsecond=0)
    logging.info('[任务总时长：] %s ', over - start)
    result = get_video_legth(name)
    return result


# 传入链接，完成写文件操作及获取key链接
def parse(url, headers):
    resp = requests.get(url, headers=headers)
    # 匹配key链接
    key_url = re.search('"(.*?key.key)"', resp.text).group(1).strip()
    m3u8_text = resp.text
    ts_queue = Queue(10000)
    lines = m3u8_text.split('\n')
    s = len(lines)
    # 找到文档中含有ts字段的行
    concatfile = 'cache/' + "zzz" + '.txt'
    for i, line in enumerate(lines):
        if '.js' in line:
            line = re.sub('\.js', '.ts', line)
            if 'http' in line:
                # print("ts>>", line)
                ts_queue.put(line)
            filename = re.search('([a-zA-Z0-9-_]+\.ts)', line).group(1).strip()
            # 一定要先写文件，因为线程的下载是无序的，文件无法按照
            # 123456。。。去顺序排序，而文件中的命名也无法保证是按顺序的
            # 这会导致下载的ts文件无序，合并时，就会顺序错误，导致视频有问题。
            open(concatfile, 'a+').write("file %s\n" % filename)
            print("\r", '文件写入中', i, "/", s, end="", flush=True)
    return ts_queue, concatfile, key_url


# 传入key链接，对key进行相关操作，到214行
def get_key(key_url, headers):
    k = requests.get(key_url, headers=headers)
    key = k.content
    cryptor = AES.new(key, AES.MODE_CBC, key)
    return cryptor


# 下载操作
def down(ts_queue, headers, cryptor):
    num = 3
    tt_name = threading.current_thread().getName()
    while not ts_queue.empty():
        url = ts_queue.get()
        filename = re.search('([a-zA-Z0-9-_]+\.ts)', url).group(1).strip()
        try:
            requests.packages.urllib3.disable_warnings()
            resp = requests.get(url, headers=headers)
            data = cryptor.decrypt(resp.content)
            with open('cache/' + filename, 'ab+') as f:
                f.write(data)
            print("\r", tt_name, '下载任务文件 ', filename, ' 成功', end="", flush=True)
        except:
            logging.info('[任务文件 ], %s, [ 下载失败]', filename)
            ts_queue.put(url)
            num -= 1


# 合并操作
def merge(concatfile, name):
    path = 'cache/' + name
    # command = 'ffmpeg -y -f concat -i %s -crf 18 -ar 48000 -vcodec libx264 -c:a aac -r 25 -g 25 -keyint_min 25 -strict -2 %s' % (concatfile, path)
    command = 'ffmpeg -y -f concat -i %s -bsf:a aac_adtstoasc -c copy %s' % (concatfile, path)
    os.system(command)


# 删除操作
def remove(concatfile):
    dir = 'cache/'
    for line in open(concatfile):
        line = re.search('file (.*?\.ts)', line).group(1).strip()
        os.remove(dir + line)
    try:
        os.remove(concatfile)
    except:
        logging.info('文件删除出现异常，请检查并手动删除冗余文件')


# 通过获取长度来判错
def get_video_legth(name):
    video_path = 'cache/' + name
    clip = VideoFileClip(video_path)
    length = clip.duration
    logging.info('[视频时长] %s s', length)
    if length < 1:
        return False
    else:
        return True


# 图片下载方法
def down_pic(path, pic_urls, headers=None):
    root = 'cache/'
    flag = os.path.exists(root)
    if flag:
        pass
    else:
        os.mkdir(root)
    for i, url in enumerate(pic_urls):
        file_name = path + str(i) + '.jpg'
        try:
            request.urlretrieve(url, 'cache/' + file_name)
            print("\r", '下载任务文件 ', file_name, ' 成功', end="", flush=True)
        except:
            logging.info('下载异常')
            return False
    return True
