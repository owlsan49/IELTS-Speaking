# -*- coding: utf-8 -*-
# Copyright (c) 2022, Shang Luo
# All rights reserved.
# 
# Author: 罗尚
# Building Time: 2024/7/23
# Reference: None
# Description: None
import pymysql
import json
import pandas as pd

cfg_path = '../config.json'

def read_json(data_path):
    try:
        with open(data_path, 'r', encoding='utf-8') as jf:
            data = json.load(jf)
    except Exception as e:
        print(e)
        print(f'{data_path} is Null')
        data = {}
    return data

# 读取Excel文件
df = pd.read_excel("ielts.xlsx")

db_config = read_json(cfg_path)['db_cfg']
connection = pymysql.connect(**db_config)

# 插入数据的SQL语句
insert_query = '''
INSERT IGNORE INTO ques_source (id, part, topics, questions)
VALUES (%s, %s, %s, %s);
'''


with connection.cursor() as cursor:
    for index, row in df.iterrows():
        cursor.execute(insert_query, tuple(row))
    connection.commit()

connection.close()
if __name__ == '__main__':
    ...
