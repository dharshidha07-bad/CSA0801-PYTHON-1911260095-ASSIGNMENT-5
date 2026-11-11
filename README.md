# CSA08-1911260095-Assignment5

**Name:** Dharshidha S  **Register number:** 1911260095
**Course:** Python Programming (CSA08) - Assignment 5 (CO5): data acquisition, cleaning, analysis and AI applications

## Environment
- Python 3.12; libraries (see `requirements.txt`): pandas 3.0, numpy 2.5, matplotlib 3.11, reportlab 5.0 (the report builder only);
  the programs also use csv, sqlite3, statistics, re, logging, cProfile from the standard library.
- **The data are synthetic.** The board's real files are not available, so `common/gen_data.py` generates 12 stations with the faults of the case
  study; the true values are known, which lets the cleaning rules be measured. The 60 complaints in `B4/complaints.csv` were written for this
  assignment; **the labels in the column `my_label` are the reference reading - read them and change any you disagree with, then run `B4/evaluate.py` again.**

## Folders, commands and results
| Task | Folder | Command (run inside the folder) | Result |
|---|---|---|---|
| A1-A5 designs | report PDF | - | designs, rules, pseudocode, chart choices, debugging/profiling plan, AI designs (no code in Part A) |
| A1 CSV vs SQL | `A1` | `python csv_vs_sql.py` | indexed SQL Q1 about thousands of times faster than re-reading the CSV at 1 million rows |
| A2 missing values | `A2` | `python missing_strategies.py` | drop / forward fill / median compared against known truth |
| A3 daily summary | `A3` | `python daily_summary.py` | 372-row summary table; SQL GROUP BY vs loops |
| A4 debugging | `A4` | `python debug_overhead.py` | assert, logging, pdb on a deliberate bug; print vs logging cost |
| A5 chatbot | `A5` | `python chatbot.py` | keyword chatbot over the SQLite database |
| B1 cleaning pipeline | `B1` | `python make_october.py`, `python pipeline.py`, `python complete_the_code.py`, `python alt_pandas.py` | every fault handled; 8,928 clean rows in SQLite; 6 charts; pandas 2.7x faster at 1 million rows |
| B2 adversarial data | `B2` | `python complete_the_code.py`, `python adversarial.py` | bad files rejected or repaired; `?` placeholder stops injection; sentiment failures recorded |
| B3 loops/pandas/SQL | `B3` | `python loops_pandas_sql.py` | all methods agree; cProfile shows statistics.mean dominates |
| B4 final decision | `B4` | `python make_complaints.py`, `python complete_the_code.py`, `python evaluate.py`, `python index_test.py` | lexicon agrees with my labels 37/60; index makes Q1 about 500x faster |

Run everything (takes about 10 minutes because of the 1,000,000-row experiments) and rebuild the PDFs:

    pip install -r requirements.txt
    python run_all.py
    python build_report.py --github https://github.com/<your-username>/CSA08-1911260095-Assignment5

Put your own terminal screenshots of each run in a `screenshots/` folder inside each task folder.
