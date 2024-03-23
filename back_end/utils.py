# -*- coding: utf-8 -*-
# Copyright (c) 2022, Shang Luo
# All rights reserved.
#
# Author: 罗尚
# Building Time: 2024/3/16
# Reference: None
# Description: None
import json
import pymysql
import subprocess
import whisper

from datetime import datetime
from pathlib import Path

ptr_path = 'data_ptr.json'
cfg_path = '../config.json'
audios_path = './audios'
day_gaps = [1, 3, 7, 7, 14, 14, 14, 30]


def read_json(data_path):
    try:
        with open(data_path, 'r', encoding='utf-8') as jf:
            data = json.load(jf)
    except Exception as e:
        print(e)
        print(f'{data_path} is Null')
        data = {}
    return data


def execute_cmd(cmd_lines: str, args=None):
    with connection.cursor() as cursor:
        cursor.execute(cmd_lines, args)
        connection.commit()
    return cursor.fetchall()


def pop_n_ques(n: int):
    src_len_cmd = "SELECT COUNT(*) FROM ques_source"
    src_len = execute_cmd(src_len_cmd)[0][0]
    if (ptrs['src'] + n) > src_len:
        n = max(src_len - ptrs['src'], 0)

    select_n_rows = f"SELECT * FROM ques_source WHERE id >= {ptrs['src'] + 1} LIMIT {n};"
    infos = execute_cmd(select_n_rows)
    ptrs['src'] += n
    write_json(ptr_path, ptrs)
    return infos


def get_ques():
    src_ques = pop_n_ques(2)
    src_ques_list = [list(str(sq[0])) + list(sq[1:]) for sq in src_ques]
    src_ques_str_list = [';'.join(q) for q in src_ques_list]
    src_ques_str = '|'.join(src_ques_str_list)

    get_ques_cmd = f"SELECT ques_strs FROM ques_queue WHERE id = {(ptrs['queue'] + 1)};"
    org_ques = execute_cmd(get_ques_cmd)[0][0]
    ptrs['queue'] = (ptrs['queue'] + 1) % sum(day_gaps)
    if len(org_ques) != 0:
        comb_strs = [org_ques, src_ques_str]
        comb_strs = '|'.join(comb_strs)
        src_ques_list += parse_ques_strs(org_ques)
    else:
        comb_strs = src_ques_str

    update_table_cmd = "UPDATE ques_queue SET ques_strs = %s WHERE id = %s;"
    execute_cmd(update_table_cmd, (comb_strs, (ptrs['queue'] + 1)))

    return src_ques_list


def parse_ques_strs(ques_strs: str):
    ques_strs = ques_strs.split('|')
    ques_strs = [qs.split(';') for qs in ques_strs]
    return ques_strs


def write_json(file_name, json_dict, mode='w'):
    with open(file_name, mode, encoding='utf-8') as jf:
        json.dump(json_dict, jf)


def convert_weba_to_mp3(weba_data, output_path):
    # 使用ffmpeg的pipe协议将字节流作为输入
    command = [
        'ffmpeg',
        '-i', 'pipe:0',  # 从标准输入读取数据
        '-acodec', 'libmp3lame',  # 指定MP3编码器
        '-f', 'mp3',  # 指定输出格式为MP3
        '-ab', '192k',  # 设定比特率为192k
        '-y',  # 覆盖输出文件
        '-loglevel', 'warning',
        output_path  # 输出文件路径
    ]

    # 启动子进程
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    process.communicate(input=weba_data)
    process.stdin.close()
    return_code = process.wait()

    if return_code != 0:
        raise Exception(f"ffmpeg process returned {return_code}")


def process_audios(request_files):
    audio_to_text = {}
    today_date = datetime.now()
    for key, value in request_files.items():
        file_path = Path(value.filename)
        change_path = (audios_path / file_path.with_name(f'{today_date.strftime("%y_%m_%d")}-' + file_path.name)
                       .with_suffix('.mp3'))
        convert_weba_to_mp3(value.read(), str(change_path))
        temp_text = model.transcribe(str(change_path))["text"]
        audio_to_text[key] = temp_text
        store_text(key, temp_text, today_date.strftime("%Y-%m-%d"))

    return audio_to_text


def store_text(src_id, text, today_date):
    push_text_cmd = "INSERT INTO every_day_text (src_id, date, text)" \
                    "VALUES (%s, %s, %s)" \
                    "ON DUPLICATE KEY UPDATE text = VALUES(text);"
    args = (src_id, today_date, text)
    execute_cmd(push_text_cmd, args)


db_config = read_json(cfg_path)['db_cfg']
connection = pymysql.connect(**db_config)
ptrs = read_json(ptr_path)
# tiny base small medium large
model = whisper.load_model("medium").to('cuda')

if __name__ == '__main__':
    # n_days = sum(day_gaps) + 1
    # add_new_line = "INSERT INTO ques_queue (ques_strs) VALUES ('')"
    # for _ in range(n_days):
    #     execute_cmd(add_new_line)
    # ceate_new = "CREATE TABLE ques_queue (id INT AUTO_INCREMENT PRIMARY KEY, ques_strs VARCHAR(1023));"
    # print(execute_cmd(ceate_new))
    # ts_list = get_ques()
    ts_list = store_text(1, 'nihao', '2024-03-23')
    ...
