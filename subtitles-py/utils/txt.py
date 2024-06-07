# 生成字幕

import os
import json

from dotenv import load_dotenv
load_dotenv()


# 字幕文件夹
subtitle_folder = os.getenv("subtitle_folder")
# 音频文件夹
mp3_folder = os.getenv("mp3_folder")


# 检查文件是否为音频文件，根据常见的音频文件扩展名列表
def is_audio_file_by_extension(filename):
    # 定义常见的文件扩展名列表
    extensions = ['.mp3', '.wma', '.flac', '.aac']
    # 检查文件名是否以列表中的任何一个扩展名结尾
    return any(filename.lower().endswith(ext) for ext in extensions)

# 判断一个文件是否存在
def file_exists(file_path):
    return os.path.exists(file_path)


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


# 读取mp3_folder文件夹下所有的子文件夹名
def get_subfolders(folder):
    mp3_subfolders = [f.name for f in os.scandir(folder) if f.is_dir()]
    return mp3_subfolders


# 把mp3_folder文件夹下的所有音频生成生成字幕，保存到subtitle_folder文件夹下
def generate_txts(mp3_folder,subtitle_folder):
   import whisper
   model = whisper.load_model("base.en")
   # 读取mp3_folder文件夹中的所有子文件夹
   mp3_subfolders = get_subfolders(mp3_folder)
   print(mp3_subfolders)
   for mp3_subfolder in mp3_subfolders:
        # 读取文件夹中的所有文件
        files = [f for f in os.listdir(mp3_folder+mp3_subfolder) if os.path.isfile(os.path.join(mp3_folder+mp3_subfolder, f))]
        print(mp3_subfolder,files)
        for filename in files:
            # 检查文件是否为音频 是否不存在对应的字幕文件
            if is_audio_file_by_extension(filename) and (not file_exists(f'{subtitle_folder}{mp3_subfolder}/{filename.split(".")[0]}.json')) :
                print('whisper启动识别：',filename)
                result = model.transcribe(mp3_folder+mp3_subfolder+'/'+filename)
                print('whisper结束识别：',filename)
                print('正在生成字幕：',filename)
                result = result["segments"]
                result_list = [];
                #result_for_save = ''
                #遍历result并读取start、end、text
                for segment in result:
                    result_dict = {};
                    start = segment["start"]
                    end = segment["end"]
                    start_time = convert_to_time(start)
                    end_time = convert_to_time(end)
                    text = segment["text"]
                    segment_for_save = f"{start_time} -- {end_time}"
                    #result_for_save += segment_for_save + "\n"
                    #result_object.append({"start":start,"end":end,"interval":segment_for_save,"text":text});
                    result_dict['start'] = start
                    result_dict['end'] = end
                    result_dict['interval'] = segment_for_save
                    result_dict['text'] = text
                    result_list.append(result_dict)

                # 如果保存的文件夹不存在，则创建
                if not os.path.exists(subtitle_folder+mp3_subfolder):
                    os.makedirs(subtitle_folder+mp3_subfolder)
                
                # 将结果result_object写入对应文件中
                with open(f'{subtitle_folder}{mp3_subfolder}/{filename.split(".")[0]}.json', 'w') as f:
                    json.dump(result_list, f)
                print('字幕完成：',filename)
            else:
                print('跳过：',filename)


