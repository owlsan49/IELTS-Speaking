# -*- coding: utf-8 -*-
# Copyright (c) 2022, Shang Luo
# All rights reserved.
# 
# Author: 罗尚
# Building Time: 2024/3/21
# Reference: None
# Description: None
import ffmpeg
import whisper

if __name__ == '__main__':
    model = whisper.load_model("base")
    result = model.transcribe("audio.webm")
    print(result["text"])
