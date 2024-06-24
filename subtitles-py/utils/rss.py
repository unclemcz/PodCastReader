import xml.etree.ElementTree as ET
import requests
import os
import time
import utils.opml as opml
import json

from dotenv import load_dotenv
load_dotenv()

# 字幕文件夹
subtitle_folder = os.getenv("subtitle_folder")
mp3_download_index = os.getenv('mp3_download_index')
# 将mp3_download_index转为整数
mp3_download_index = int(mp3_download_index)

# 获取特定文件夹下的所有文件名
def get_file_names(folder_path):
    file_names = []
    for file_name in os.listdir(folder_path):
        file_names.append(file_name)
    return file_names

# 获取一个播客rss文件的所有条目，该rss文件已下载到在本地
def get_rss_entries(rss_file_path):
    rss_entries = []
    tree = ET.parse(rss_file_path)
    root = tree.getroot()
    for item in root.findall('channel/item'):
        episode = {}
        episode['title'] = item.find('title').text
        if(item.find('link')):
            episode['link'] = item.find('link').text
        else:
            episode['link'] = ''
        episode['enclosure_url'] = item.find('enclosure').attrib['url']
        rss_entries.append(episode)
    return rss_entries

# 下载一个播客音频mp3到本地，如果本地已存在该音频，则不下载
def download_audio(episode, save_path):
    title = episode['title'];
    link = episode['link'];
    enclosure_url = episode['enclosure_url'];
    if not os.path.exists(save_path+opml.url2md5(title)+'.mp3'):
        print('努力下载中： '+title+'.mp3')
        try:
            r = requests.get(enclosure_url,stream=True,allow_redirects=True)
            # 判断下载是否成功
            if r.status_code == 200:
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                # 如果保存的文件夹不存在，则创建
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                with open(save_path+opml.url2md5(title)+'.mp3', 'wb') as f:
                    for data in r.iter_content(chunk_size=1024):
                        f.write(data)
                        downloaded_size += len(data)
                        progress = int(50 * downloaded_size / total_size)
                        print(f"\r[{'#' * progress}{'.' * (50 - progress)}] {progress * 2}%", end="")
                        #print()
                    print()
                    print(f"下载完成:{title}:{opml.url2md5(title)}.mp3")
                # 检查文件完整性
                if os.path.getsize(save_path+opml.url2md5(title)+'.mp3') == total_size:
                    print("文件下载完成，校验正常。")
                    print("本地文件大小:",os.path.getsize(save_path+opml.url2md5(title)+'.mp3'))
                    print("源文件大小:",total_size)
                else:
                    print("文件下载完成，但校验异常。")
            else:
                print(f"{title}下载失败，错误码：",r.status_code)
        except requests.exceptions.RequestException as e:
            print(f"下载时出错{enclosure_url}: {e}")

# 下载所有rss文件中的音频到本地
def download_all_audio(rss_folder, mp3_folder):
    rss_files = get_file_names(rss_folder)
    #print(rss_files)
    for rss_file in rss_files:
        rss_entries = get_rss_entries(rss_folder+rss_file)
        mp3json = [] #记录mp3和文件名md5的对应关系
        for index, episode in enumerate(rss_entries):
            if index < mp3_download_index:
                mp3json.append({'title':episode['title'],'md5':opml.url2md5(episode['title'])})
                # 检查本地是否已存在该音频
                print('检查同名音频mp3',mp3_folder+rss_file+'/'+opml.url2md5(episode['title'])+'.mp3')
                print('检查同名字幕',subtitle_folder+rss_file+'/'+opml.url2md5(episode['title'])+'.json')
                mp3_exists = os.path.exists(mp3_folder+rss_file+'/'+opml.url2md5(episode['title'])+'.mp3')
                subtitle_exists = os.path.exists(subtitle_folder+rss_file+'/'+opml.url2md5(episode['title'])+'.json')
                if not (mp3_exists or subtitle_exists):
                    download_audio(episode, mp3_folder+rss_file+'/')
                    time.sleep(5)
                else:
                    print(rss_file+'/'+episode['title']+'音频或者字幕已存在，跳过下载。')
            else:
                print(f'当前音频索引为{index+1},默认不下载。')
                break
        #将mp3json保存到本地mp3_folder文件夹下
        with open(mp3_folder+rss_file+'/mp3.json', 'w', encoding='utf-8') as f:
            json.dump(mp3json, f, ensure_ascii=False, indent=4)

