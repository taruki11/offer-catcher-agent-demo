#!/usr/bin/env python
"""
3060_pycompile.py — 3060 远程 py_compile 检查
运行方式：python 3060_pycompile.py
（在 3060 上直接执行）
"""
import sys, py_compile, pathlib

base = pathlib.Path(r"D:\Pycharm_workplace\offer_catcher_agent_demo_20260602")
py_files = list(base.glob("*.py")) + list((base / "src").glob("*.py")) + list((base / "scripts").glob("*.py"))

print(f"开始检查 {len(py_files)} 个 .py 文件...")
errors = []
for fp in py_files:
    try:
        py_compile.compile(str(fp), doraise=True)
        print(f"  ✅ {fp.relative_to(base)}")
    except Exception as e:
        errors.append((fp, e))
        print(f"  ❌ {fp.relative_to(base)}: {e}")

print()
if errors:
    print(f"❌ 有 {len(errors)} 个文件语法错误：")
    for fp, e in errors:
        print(f"  {fp.relative_to(base)}: {e}")
    sys.exit(1)
else:
    print("✅ 全部 PY_COMPILE 通过")
    print("PY_COMPILE_OK")
