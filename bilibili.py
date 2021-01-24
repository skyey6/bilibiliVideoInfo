import requests
from urllib.parse import urlencode
import configparser
import json
import pandas as pd
import time
import re

base_url = 'https://api.bilibili.com/x/space/arc/search?'
# str1 = 'https://api.bilibili.com/x/space/arc/search?mid=350456040&ps=30&tid=0&pn=1&keyword=&order=pubdate&jsonp=jsonp'
# str2 = 'https://api.bilibili.com/x/space/arc/search?mid=350456040&ps=30&tid=0&pn=2&keyword=&order=pubdate&jsonp=jsonp'
# str3 = 'https://api.bilibili.com/x/space/arc/search?mid=350456040&ps=30&tid=0&pn=3&keyword=&order=pubdate&jsonp=jsonp'
# 观察发现，请求的参数有7个，其中pn用来控制分页，pn=1代表第一页， mid代表b站的UID
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
}
# 获取up的uid
conf = configparser.ConfigParser()
conf.read('config.ini')
uid = conf.get('upinfo', 'uid')
# 获取up名称
up_url = 'https://space.bilibili.com/' + uid
res = requests.get(up_url, headers=headers)
pattern = re.compile(r'<title>(.+?)的个人空间.*?</title>')
up_name = re.search(pattern, res.text).group(1)


def get_page(page: int) -> dict:
    """
    获得单页中所有视频的信息。
    :param page: 要爬取第几页。
    :return: 视频信息的JSON数据（以字典的形式返回）。
    """
    params = {
        'mid': uid,
        'ps': 30,
        'tid': 0,
        'pn': page,
        'keyword': '',
        'order': 'pubdate',
        'jsonp': 'jsonp'
    }
    url = base_url + urlencode(params)  # 拼接url和参数
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()  # 将获得的json字符串以字典形式返回
    except requests.ConnectionError as e:
        print('ConnectionError:' + e.args)


def parse_page(datas: dict) -> dict:
    """
    从结果中提取需要的信息。
    :param datas: 原始数据。
    """
    parsed_data = {}
    if datas:
        items = datas.get('data').get('list').get('vlist')
        for item in items:
            parsed_data['标题'] = item.get('title')
            # parsed_data['up主'] = item.get('author')
            parsed_data['av号'] = item.get('aid')
            parsed_data['bv号'] = item.get('bvid')
            parsed_data['播放量'] = item.get('play')
            parsed_data['时长'] = item.get('length')
            parsed_data['弹幕数量'] = item.get('video_review')
            parsed_data['评论数'] = item.get('comment')
            parsed_data['爬取时间'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            yield parsed_data


if __name__ == '__main__':
    all_video = get_page(1).get('data').get('page').get('count')    # up视频总数
    print('up视频总数:', all_video)
    df = pd.DataFrame()     # DataFrame对象
    # 判断最大页数
    if all_video % 30 == 0:
        max_page = all_video // 30
    else:
        max_page = all_video // 30 + 1
    for page in range(1, max_page + 1):
        datas = get_page(page)

        # ----- 写入txt文件 -----
        # for parsed_data in parse_page(datas):
        #     with open(f'{up_name}.txt', 'a', encoding='utf-8') as file:
        #         file.write(json.dumps(parsed_data, indent=2, ensure_ascii=False))

        # ----- 写入csv文件 -----
        for parsed_data in parse_page(datas):
            # DataFrame的append()方法向dataframe对象中添加新的行，
            # 如果添加的列名不在dataframe对象中，将会被当作新的列进行添加
            df = df.append(parsed_data, ignore_index=True)
    df.to_csv(f'{up_name}.csv')  # 可设置 index=None 来去除列索引

    print('----- 爬取完毕！-----')
