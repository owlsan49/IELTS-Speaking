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
import os, time

from datetime import datetime
from pathlib import Path
from poe_api_wrapper import PoeApi

ptr_path = 'data_ptr.json'
cfg_path = '../config.json'
audios_path = './audios'
day_gaps = [1, 3, 7, 7, 14, 14, 14, 30]

# chat api
tokens = {
    'p-b': '7kM5SS9VHk4M-6J59hqtSg%3D%3D',
    'p-lat': 'qPIZSb1VF0PUuS70nhAzKvGb9P2GsOfiyXKZQvKSbg%3D%3D'
}

os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"
client = PoeApi(tokens=tokens)
print(client.get_chat_history()['data'])
chatId = 305781254
inst = ('基于下面这段英文做出修改，请保持修改的精准性和语法正确，并且符合日常交流的语言习惯，并将修改后的句子翻译成中文。\n'
        '下面是我的英文原文：{}')


def gen_reply(message):
    # while True:
    #     try:
    #         resp = ""
    #         for chunk in client.send_message('gpt4_o', message, chatId=chatId):
    #             resp += chunk["response"]
    #         break  # 如果成功执行了函数，退出循环
    #     except Exception as e:
    #         print(f"尝试失败：{str(e)}，正在重试...")
    #         time.sleep(25)  # 可以适当休眠一段时间再重试
    resp = ""
    for chunk in client.send_message('gpt4_o', message, chatId=chatId):
        resp += chunk["response"]
    time.sleep(2)
    return resp


def gen_gpt_reply(audio_text):
    gpt_reply = {}
    # key_list = list(audio_text.keys())
    # print(key_list)
    # for i, k_en in enumerate(key_list[::2]):
    #     t_cn = audio_text[key_list[2*i + 1]]
    #     t_en = audio_text[k_en]
    #     print(f"ccccc, {audio_text[k_en]}")
    #     message = inst.format(t_en)
    #     gpt_reply[k_en.split('_')[0]] = gen_reply(message)

    for k_en, v_en in audio_text.items():
        message = inst.format(v_en)
        gpt_reply[k_en.split('_')[0]] = gen_reply(message)
    # print(gpt_reply)
    return gpt_reply


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


def init_queue():
    query = "SELECT COUNT(*) FROM ques_queue"
    result = execute_cmd(query)
    if result[0][0] == 0:
        add_cmd = "INSERT IGNORE INTO ques_queue (id, ques_strs) VALUES ({}, NULL);"
        for i in range(sum(day_gaps)):
            execute_cmd(add_cmd.format(i+1))


def get_ques():
    src_ques = pop_n_ques(2)
    src_ques_list = [[str(sq[0])] + list(sq[1:]) for sq in src_ques]
    src_ques_str_list = [';'.join(q) for q in src_ques_list]
    src_ques_str = '|'.join(src_ques_str_list)

    get_ques_cmd = f"SELECT ques_strs FROM ques_queue WHERE id = {(ptrs['queue'] + 1)};"
    init_queue()
    org_ques = execute_cmd(get_ques_cmd)[0][0]
    ptrs['queue'] = (ptrs['queue'] + 1) % sum(day_gaps)
    write_json(ptr_path, ptrs)
    if org_ques is not None and len(org_ques) != 0:
        src_ques_list += parse_ques_strs(org_ques)

    strs_append(src_ques_str)
    return src_ques_list


def strs_append(src_ques_str):
    for i, _ in enumerate(day_gaps):
        queue_idx = (ptrs['queue'] + sum(day_gaps[:(i + 1)])) % sum(day_gaps)
        get_ques_cmd = f"SELECT ques_strs FROM ques_queue WHERE id = {(queue_idx + 1)};"
        org_i_ques = execute_cmd(get_ques_cmd)[0][0]
        if org_i_ques is not None and len(org_i_ques) != 0:
            comb_strs = [org_i_ques, src_ques_str]
            comb_strs = '|'.join(comb_strs)
        else:
            comb_strs = src_ques_str

        update_table_cmd = "UPDATE ques_queue SET ques_strs = %s WHERE id = %s;"
        execute_cmd(update_table_cmd, (comb_strs, (queue_idx+1)))


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
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=weba_data)

    if process.returncode != 0:
        return f"An error occurred during conversion: {stderr.decode()}"


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
        # store_text(key, temp_text, today_date.strftime("%Y-%m-%d"))

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
    # ts_list = store_text(1, 'nihao', '2024-03-23')
    ...
    init_queue()
