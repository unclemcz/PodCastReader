

import xml.etree.ElementTree as ET
import hashlib
import requests
import time


# 解析opml文件
def parse_opml(opml_file):
    tree = ET.parse(opml_file)
    root = tree.getroot()
    result=[]
    for outline in root.iter('outline'):
        tmp = {}
        tmp['title'] = outline.get('title')
        tmp['text'] = outline.get('text')
        tmp['xmlUrl'] = outline.get('xmlUrl')
        tmp['htmlUrl'] = outline.get('htmlUrl')
        tmp['type'] = outline.get('type')
        result.append(tmp)
    return result

# 生成播客rss的md5值
def url2md5(url):
    m = hashlib.md5()
    m.update(url.encode('utf-8'))
    return m.hexdigest()

# 根据url下载播客rss文件到特定地址，并命名为新的名称
def download_rss(url, save_path):
    print(f"下载开始：{url}")
    r = requests.get(url)
    with open(save_path+url2md5(url), 'wb') as f:
        f.write(r.content)
        print(f"下载完成：{url}，重命名为：{url2md5(url)}")


# 从opml文件中下载所有rss文件
def download_rss_from_opml(opml_file, save_path):
    opml_list = parse_opml(opml_file)
    for opml in opml_list:
        if opml['type'] == 'rss':
            download_rss(opml['xmlUrl'], save_path)
            # 暂停1秒钟后再下载下一个
            time.sleep(1)
        else:
            print(f"{opml['xmlUrl']}不是一个标准的RSS文件。")

