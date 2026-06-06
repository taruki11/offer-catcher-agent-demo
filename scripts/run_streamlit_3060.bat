@echo off
cd /d D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
set PYTHONIOENCODING=utf-8
D:\anaconda3\envs\pytorch123\python.exe -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502 --server.headless true > streamlit_output.log 2>&1
