cd /d D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
python scripts\check_remote_data.py
python -m py_compile app.py src\matcher.py src\strategy_planner.py scripts\run_eval.py scripts\analyze_job_corpus.py scripts\eval_corpus_quality.py
python scripts\run_eval.py --split core
python scripts\run_eval.py --split stress
python scripts\analyze_job_corpus.py
python scripts\eval_corpus_quality.py
echo VERIFY_3060_DONE
