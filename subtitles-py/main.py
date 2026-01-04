import os
import sys
import select
import time
import utils.opml as opml
import utils.rss as rss
import utils.txt as txt

from dotenv import load_dotenv
load_dotenv()


# 字幕文件夹
subtitle_folder = os.getenv("subtitle_folder")
# 音频文件夹
mp3_folder = os.getenv("mp3_folder")
# rss源文件夹
rss_folder = os.getenv("rss_folder")
# opml文件
opml_file = os.getenv("opml_file")


def main():

    # 程序运行后根据窗口输入判断是否要执行以下代码（y:是，n：否）
    # 如果超过10秒没有输入，则默认y
    if input_with_timeout('本次是否更新RSS源？(y/n):',10) == "y":
        # 从opml文件中读取rss源并保存到rss_folder文件夹
        opml.download_rss_from_opml(opml_file, rss_folder)
    else:
        print("使用上一次RSS源。")

    # 下载rss源中的音频文件并保存到mp3_folder文件夹
    rss.download_all_audio(rss_folder, mp3_folder)

    # 把mp3_folder下的音频生成字幕保存到subtitle_folder下
    txt.generate_txts(mp3_folder,subtitle_folder)



def input_with_timeout(prompt, timeout=10):
    print(prompt, end='', flush=True)
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.readline().strip()
    else:
        print(f"\n等待{timeout}秒未操作，默认开始更新RSS源。")
        return 'y'

if __name__ == '__main__':
    main()

    