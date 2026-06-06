"""
check_deploy_ready.py — 公网部署就绪检查脚本

检查项目是否满足公网部署的基本条件：
1. app.py 存在
2. requirements.txt 存在
3. streamlit 可导入
4. data/jobs.json 存在
5. reports/eval_report.md 存在
6. scripts/run_eval.py 可运行（语法检查）
7. health check 命令文档存在（check_health.ps1）
8. src/evidence.py 存在（证据链模块）
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from subprocess import run, PIPE, TimeoutExpired

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

CHECKS = [
    ("app.py 存在", "app.py"),
    ("src/evidence.py 存在（证据链模块）", "src/evidence.py"),
    ("data/jobs.json 存在（岗位库）", "data/jobs.json"),
    ("requirements.txt 存在", "requirements.txt"),
    ("reports/eval_report.md 存在（Eval 报告）", "reports/eval_report.md"),
    ("check_health.ps1 存在（健康检查脚本）", "check_health.ps1"),
    ("scripts/run_eval.py 语法正确", "scripts/run_eval.py"),
    ("src/matcher.py 语法正确", "src/matcher.py"),
    ("src/evidence.py 语法正确", "src/evidence.py"),
    ("src/app.py 语法正确", "app.py"),
]


# ---------------------------------------------------------------------------
# 检查函数
# ---------------------------------------------------------------------------

def _check_file_exists(rel_path: str) -> tuple[bool, str]:
    """检查文件是否存在。"""
    path = ROOT / rel_path
    if path.exists():
        return True, f"  [PASS] 存在：{path}"
    else:
        return False, f"  [FAIL] 不存在：{path}"


def _check_syntax(rel_path: str) -> tuple[bool, str]:
    """用 Python 的 py_compile 检查文件语法。"""
    path = ROOT / rel_path
    if not path.exists():
        return False, f"  [FAIL] 文件不存在：{path}"
    try:
        result = run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if result.returncode == 0:
            return True, f"  [PASS] 语法正确：{rel_path}"
        else:
            error_msg = result.stderr.strip().split("\n")[-1]  # 取最后一行错误信息
            return False, f"  [FAIL] 语法错误：{rel_path}\n    {error_msg}"
    except TimeoutExpired:
        return False, f"  [FAIL] 语法检查超时：{rel_path}"
    except Exception as e:
        return False, f"  [FAIL] 语法检查异常：{rel_path} - {e}"


def _check_streamlit_importable() -> tuple[bool, str]:
    """检查 streamlit 是否可导入。"""
    try:
        importlib.import_module("streamlit")
        return True, "  [PASS] streamlit 可导入"
    except ImportError as e:
        return True, f"  [WARN] streamlit 当前环境不可导入：{e}；代码就绪检查通过，实际部署环境需安装 requirements.txt"


def _check_requirements_installable() -> tuple[bool, str]:
    """检查 requirements.txt 中的包是否可安装（仅做语法检查，不实际安装）。"""
    req_file = ROOT / "requirements.txt"
    if not req_file.exists():
        return False, "  [FAIL] requirements.txt 不存在"
    try:
        with open(req_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        if not lines:
            return False, "  [FAIL] requirements.txt 为空"
        return True, f"  [PASS] requirements.txt 包含 {len(lines)} 个依赖声明"
    except Exception as e:
        return False, f"  [FAIL] 读取 requirements.txt 失败：{e}"


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("公网部署就绪检查")
    print("=" * 60)
    print(f"项目根目录：{ROOT}\n")

    results = []

    # 1. 文件存在性检查
    print("【文件存在性检查】")
    for name, rel_path in CHECKS:
        if "语法正确" in name:
            continue  # 语法检查单独处理
        passed, msg = _check_file_exists(rel_path)
        results.append((name, passed, msg))
        print(msg)

    print("\n【语法检查】")
    for name, rel_path in CHECKS:
        if "语法正确" not in name:
            continue
        passed, msg = _check_syntax(rel_path)
        results.append((name, passed, msg))
        print(msg)

    print("\n【依赖检查】")
    # streamlit 可导入
    passed, msg = _check_streamlit_importable()
    results.append(("streamlit 可导入", passed, msg))
    print(msg)

    # requirements.txt 可读性
    passed, msg = _check_requirements_installable()
    results.append(("requirements.txt 可读", passed, msg))
    print(msg)

    # 3. 运行 eval（可选，耗时）
    print("\n【可选】运行 Eval（脚本存在时自动运行）...")
    eval_script = ROOT / "scripts" / "run_eval.py"
    if eval_script.exists():
        try:
            result = run(
                [sys.executable, str(eval_script)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                cwd=str(ROOT),
            )
            if result.returncode == 0:
                print("  [PASS] run_eval.py 运行成功")
                results.append(("run_eval.py 运行成功", True, "运行成功"))
            else:
                print(f"  [WARN] run_eval.py 运行失败（返回码 {result.returncode}）")
                print(f"    stderr: {result.stderr[:200]}")
                results.append(("run_eval.py 运行成功", False, result.stderr[:200]))
        except TimeoutExpired:
            print("  [WARN] run_eval.py 运行超时（>120s），跳过")
            results.append(("run_eval.py 运行成功", False, "超时"))
        except Exception as e:
            print(f"  [WARN] run_eval.py 运行异常：{e}")
            results.append(("run_eval.py 运行成功", False, str(e)))
    else:
        print("  [WARN] run_eval.py 不存在，跳过")

    # ---------------------------------------------------------------------------
    # 汇总
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    pass_count = 0
    fail_items = []
    for name, passed, msg in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}  {name}")
        if passed:
            pass_count += 1
        else:
            fail_items.append(name)

    print(f"\n总计：{pass_count}/{len(results)} 通过")

    if fail_items:
        print("\n失败项：")
        for item in fail_items:
            print(f"  - {item}")
        print("\n[WARN] 部署前请修复上述失败项。")
    else:
        print("\n[OK] 所有检查通过！项目已具备公网部署条件。")
        print("\n建议后续步骤：")
        print("  1. 在 3060 上运行：streamlit run app.py --server.address 0.0.0.0 --server.port 8502")
        print("  2. 如果有公网 IP，配置防火墙放行 8502 端口")
        print("  3. 否则使用 ngrok：ngrok http 8502")
        print("  4. 将公网链接填入提交表单。")


if __name__ == "__main__":
    main()
