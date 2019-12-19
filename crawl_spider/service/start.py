import argparse
import sys

parser = argparse.ArgumentParser()
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

def get_video_url():
    parser.add_argument("-u","--url", help="链接", type=str)
    args = parser.parse_args()
    if args.url:
        pass
    else:
        logging.info('缺少必要的参数')
        sys.exit()
    return args.url

def get_pic_params():
    parser.add_argument("-k", "--key", help="关键词", type=str)
    parser.add_argument("-n", "--num", help="数量", type=str)
    args = parser.parse_args()
    if args.key and args.num:
        pass
    else:
        logging.info('缺少必要的参数')
        sys.exit()
    return args.key, args.num


def get_text_params():
    parser.add_argument("-k", "--key", help="关键词", type=str)
    args = parser.parse_args()
    if args.key:
        pass
    else:
        logging.info('缺少必要的参数')
        sys.exit()
    return args.key