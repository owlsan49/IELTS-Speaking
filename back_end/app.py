# -*- coding: utf-8 -*-
# Copyright (c) 2022, Shang Luo
# All rights reserved.
# 
# Author: 罗尚
# Building Time: 2024/3/16
# Reference: None
# Description: None
from flask import Flask, jsonify, request
from flask_cors import CORS
from utils import (read_json, get_ques,
                   process_audios, gen_gpt_reply)

app = Flask(__name__)
CORS(app)


@app.route('/get_today_info', methods=['GET'])
def get_today_info():
    results = {'resCode': 0}
    ques = get_ques()
    results['ques_info'] = ques
    print(ques)
    return jsonify(results)


@app.route('/post_audios', methods=['POST'])
def post_audios():
    results = {'resCode': 0}
    results['audio_text'] = process_audios(request.files)
    results['gpt_reply'] = gen_gpt_reply(results['audio_text'])
    # print(results['audio_text'])
    return jsonify(results)


if __name__ == '__main__':
    port = read_json('../config.json')['flask_port']
    app.run(debug=True, port=port)
