import os
import utils.opml as opml
import utils.rss as rss
import utils.txt as txt


# 转换秒数为时:分:秒格式
def convert_to_time(seconds):
    if seconds < 0 :
        return "无效的数字"
    # 将秒数的小数点转化为毫秒
    mseconds = int(seconds * 1000) % 1000
    seconds = int(seconds)
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{mseconds:03d}"

# 判断一个文件是否存在
def file_exists(file_path):
    return os.path.exists(file_path)

# 读取public/data/subtitles文件夹下的文件
def read_subtitle_files():
    subtitle_folder = "../public/data/subtitles"
    subtitle_files = [f for f in os.listdir(subtitle_folder) if f.endswith(".json")]
    for subtitle in subtitle_files:
        print(subtitle)



# 字幕文件夹
subtitle_folder = "../public/data/subtitles/"
# 音频文件夹
mp3_folder = "../public/data/mp3/"
# rss源文件夹
rss_folder = "../public/data/rss/"
# opml文件
opml_file = "../public/data/base.opml"

#rss_file = rss.get_file_names(rss_folder)[0]
#print(rss_file)
#episode = rss.get_rss_entries(rss_folder+rss_file)[0]

#print(episode)

#rss.download_audio(episode, mp3_folder+rss_file+"/")
#rss.download_audio_tmp(episode)


t = txt.get_subfolders(mp3_folder)
print(t)
