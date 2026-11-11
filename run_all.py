"""Run every program of Assignment 5 and save its output next to the source file (takes a few minutes)."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PROGRAMS = [
    ("B1", "make_october.py", None), ("B1", "pipeline.py", "output.txt"), ("B1", "complete_the_code.py", "complete_output.txt"),
    ("B1", "alt_pandas.py", "alt_output.txt"),
    ("B2", "complete_the_code.py", "complete_output.txt"), ("B2", "adversarial.py", "output.txt"),
    ("B3", "loops_pandas_sql.py", "output.txt"),
    ("B4", "make_complaints.py", None), ("B4", "complete_the_code.py", "complete_output.txt"), ("B4", "evaluate.py", "output.txt"),
    ("B4", "index_test.py", "index_output.txt"),
    ("A1", "csv_vs_sql.py", "output.txt"), ("A2", "missing_strategies.py", "output.txt"), ("A3", "daily_summary.py", "output.txt"),
    ("A4", "debug_overhead.py", "output.txt"), ("A5", "chatbot.py", "output.txt"),
]
for folder, script, out in PROGRAMS:
    print(f"Running {folder}/{script} ...", flush=True)
    res = subprocess.run([sys.executable, script], cwd=os.path.join(ROOT, folder), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out:
        with open(os.path.join(ROOT, folder, out), "w", encoding="utf-8") as f:
            f.write(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(f"{folder}/{script} failed")
print("All programs ran successfully. Now run:  python build_report.py --github <your repository URL>")
