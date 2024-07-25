@echo off

set VUE_PORT=5177
set PYTHON=C:\CustomProgram\Anaconda3\envs\vocab\python.exe

cd ./back_end
start cmd.exe /k %PYTHON% app.py
cd ..
cd ./front_end
set RUN_VUE=npm run dev -- --port %VUE_PORT%
start cmd.exe /k %RUN_VUE%
start http://localhost:%VUE_PORT%/
cd ..