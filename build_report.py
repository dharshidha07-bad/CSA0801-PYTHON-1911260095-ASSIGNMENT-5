"""Build the two PDFs for the portal (max 2 files, 10 MB each).

    python run_all.py
    python build_report.py --github https://github.com/<you>/CSA08-1911260095-Assignment5

PDF 1 = report (Part A designs and Part B evidence).  PDF 2 = source code, data samples, outputs.
"""
import argparse
import ast
import datetime
import os
import platform
import re
import textwrap

import sqlite3

import matplotlib
import numpy
import pandas
import reportlab
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

import make_figures

ROOT = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser()
parser.add_argument("--github", default="https://github.com/<your-username>/CSA08-1911260095-Assignment5")
parser.add_argument("--name", default="Dharshidha S")
parser.add_argument("--reg", default="1911260095")
parser.add_argument("--date", default=datetime.date.today().strftime("%d %B %Y"))
args = parser.parse_args()
PYVER = platform.python_version()

fdir = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
for nm, fn in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
               ("DVM", "DejaVuSansMono.ttf"), ("DVM-B", "DejaVuSansMono-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(nm, os.path.join(fdir, fn)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-B")
pdfmetrics.registerFontFamily("DVM", normal="DVM", bold="DVM-B", italic="DVM", boldItalic="DVM-B")

BODY = ParagraphStyle("body", fontName="DV", fontSize=8.8, leading=12.2, spaceAfter=4)
H1 = ParagraphStyle("h1", fontName="DV-B", fontSize=14, leading=18, spaceBefore=4, spaceAfter=6, textColor=colors.HexColor("#1f3b63"))
H2 = ParagraphStyle("h2", fontName="DV-B", fontSize=10.2, leading=13, spaceBefore=8, spaceAfter=3, textColor=colors.HexColor("#2c5d8f"))
CAP = ParagraphStyle("cap", fontName="DV-I", fontSize=7.8, leading=10, alignment=TA_CENTER, spaceAfter=6)
MONO = ParagraphStyle("mono", fontName="DVM", fontSize=6.6, leading=7.9, backColor=colors.HexColor("#f4f4f4"), borderPadding=3, spaceAfter=6)
TITLE = ParagraphStyle("title", fontName="DV-B", fontSize=22, leading=28, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor("#1f3b63"))
CENTER = ParagraphStyle("center", parent=BODY, alignment=TA_CENTER, fontSize=10.5, leading=15)
M = "<font name='DVM'>%s</font>"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(t, style=BODY):
    return Paragraph(t, style)


def bullets(items):
    return [Paragraph("•&nbsp;&nbsp;" + t, ParagraphStyle("b", parent=BODY, leftIndent=12, firstLineIndent=-9, spaceAfter=2)) for t in items]


def code(text, width=118):
    lines = []
    for ln in text.rstrip("\n").split("\n"):
        lines += textwrap.wrap(ln, width, subsequent_indent="      ", replace_whitespace=False, drop_whitespace=False) or [""]
    return Preformatted("\n".join(lines), MONO)


def table(rows, widths=None, font=7.8):
    cell = ParagraphStyle("cell", fontName="DV", fontSize=font, leading=font + 2.6)
    head = ParagraphStyle("head", parent=cell, fontName="DV-B")
    rows = [[c if not isinstance(c, str) else Paragraph(c, head if i == 0 else cell) for c in row] for i, row in enumerate(rows)]
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f2")), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    return [t, Spacer(1, 6)]


def img(name, width_cm, caption):
    path = os.path.join(ROOT, "figures", name)
    w, h = PILImage.open(path).size
    return [KeepTogether([Image(path, width=width_cm * cm, height=width_cm * cm * h / w), P(caption, CAP)])]


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def funcs(path, names):
    src = read(path)
    out = []
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            out.append(ast.get_source_segment(src, node))
    return "\n\n".join(out)


def lines_of(path, start, end):
    return "\n".join(read(path).split("\n")[start:end])


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(1.6 * cm, 1.0 * cm, f"Python Programming - Assignment 5 (CO5) - {args.name} - {args.reg}")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


import json as _json


def J(path):
    with open(os.path.join(ROOT, path)) as f:
        return _json.load(f)


def between(path, a, b=None):
    t = read(path)
    i = t.index(a)
    j = t.index(b, i + len(a)) if b else len(t)
    return t[i:j].rstrip()


def ms(x):
    return f"{x * 1000:.1f} ms" if x < 1 else f"{x:.2f} s"


def cover(story, second=False):
    story += [Spacer(1, 2.6 * cm), P("PYTHON PROGRAMMING", TITLE),
              P("Assignment 5 - CO5", ParagraphStyle("t2", parent=TITLE, fontSize=16, leading=20)),
              P("Data acquisition, cleaning, analysis and AI applications", ParagraphStyle("t3", parent=CENTER, fontName="DV-I")),
              Spacer(1, 1.0 * cm)]
    rows = [["Student name", esc(args.name)], ["Register number", esc(args.reg)], ["Course", "Python Programming (CSA08)"],
            ["GitHub repository", esc(args.github)], ["Python version", PYVER],
            ["Libraries", f"pandas {pandas.__version__}, numpy {numpy.__version__}, matplotlib {matplotlib.__version__}, "
                          f"reportlab {reportlab.Version}; csv, sqlite3 {sqlite3.sqlite_version}, statistics, re, logging, cProfile (standard library)"],
            ["Document", "Source code, data samples, outputs" if second else "Report - Part A (design) and Part B (implementation and investigation)"],
            ["Date", esc(args.date)]]
    rows = [[P("<b>%s</b>" % a), P(b)] for a, b in rows]
    t = Table(rows, colWidths=[4.2 * cm, 12.3 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3fa"))]))
    story += [t, Spacer(1, 0.6 * cm)]
    if not second:
        story += [P("<b>Important note on the data.</b> The real files of the pollution control board are not available, so every program in this "
                    "assignment works on <b>synthetic data generated by common/gen_data.py</b>: 12 stations with the same kinds of faults as in the case "
                    "study (blank and NA values, negative and impossible readings, duplicates, two stations in Fahrenheit, mixed name cases and date formats). "
                    "Because the true values are known, the effect of each cleaning rule can be measured. The numbers and chart interpretations describe this "
                    "synthetic data, not the real city. The 60 complaints in B4 were written for this assignment and labelled by hand.", BODY),
                  P("<b>Contents.</b> Part A (25): A1 data acquisition · A2 cleaning and normalisation · A3 analysis and visualisation · A4 debugging and "
                    "profiling · A5 AI application. Part B (25): B1 cleaning pipeline · B2 adversarial data · B3 loops vs libraries vs SQL · B4 final decision. "
                    "Pseudocode convention: ALGORITHM / INPUT / OUTPUT / BEGIN … END, upper-case keywords, &lt;- for assignment. No Python code appears in Part A.",
                    ParagraphStyle("n", parent=BODY, fontSize=8.6, alignment=TA_CENTER))]
    story.append(PageBreak())


# ============================================================================= PART A
def part_a(story):
    a1, a2, a3, a4 = J("A1/results.json"), J("A2/results.json"), J("A3/results.json"), J("A4/results.json")
    story += [P("PART A - DATA AND PROGRAM DESIGN (25 marks)", H1)]
    story += img("workflow.png", 16, "Fig. A - The workflow used throughout: Acquire → Inspect → Clean → Normalise → Store → Query → Visualise → Profile → Interpret.")
    # ------------------------------------------------------------------ A1
    story += [P("Task A1 - Design the data acquisition (K3 - Apply, 7 marks)", H2), P("A1.1 - Inspect the source (2 marks)", H2),
              P("<b>Structure of a station file.</b> One text file per station per day, comma separated, a header line "
                "<font name='DVM'>station,date,hour,pm25,pm10,no2,temp</font> and one line for every hour (24 lines): station name, date, hour 0-23, "
                "PM2.5, PM10 and NO₂ in µg/m³ and temperature (°C, or °F for two stations). Expected problems:")]
    story += table([["#", "Problem", "Example in the file"],
                    ["1", "Missing value: blank or 'NA'", "<font name='DVM'>Adyar,2026-10-01,2,,79,29,26.8</font> and <font name='DVM'>…,NA,80,…</font>"],
                    ["2", "Impossible value: negative sensor fault", "<font name='DVM'>pm10 = -5</font>, <font name='DVM'>pm25 = -999</font>"],
                    ["3", "Impossible value: far too large", "<font name='DVM'>pm25 = 9999</font>, <font name='DVM'>99999</font>"],
                    ["4", "Text where a number is expected", "<font name='DVM'>pm25 = abc</font>"],
                    ["5", "Duplicate rows (device resent a line)", "the same station, date and hour twice"],
                    ["6", "Temperature in Fahrenheit (two stations)", "Manali: 80.6 instead of 27.0"],
                    ["7", "Inconsistent station names", "'adyar', ' ADYAR ', 'Adyar'"],
                    ["8", "Inconsistent or invalid dates and hours", "'01/10/2026' instead of 2026-10-01; '2026-13-01'; hour 25"],
                    ["9", "File-level problems", "different delimiter (';'), different encoding (Windows-1252, UTF-16, BOM), a missing column, an empty file"],
                    ["10", "Rows out of order / gaps in time", "hours missing for several hours in a row (outage)"]], [0.7 * cm, 6 * cm, 9.9 * cm], font=7.4)
    story += [P("A1.2 - Design the storage (3 marks)", H2)]
    story += img("er.png", 13, "Fig. A1 - Two tables: stations (one row per station) and readings (one row per station, day and hour).")
    story += table([["CSV column", "Becomes", "Type", "Transformation"],
                    ["station", "stations.name (once) → readings.station_id", "TEXT / INTEGER FK", "normalised name (Title Case, single spaces) looked up in stations; the number is stored, not the text, so a name is stored once"],
                    ["date", "readings.day", "TEXT 'YYYY-MM-DD'", "all formats converted to ISO (sorts correctly as text; SQLite has no date type)"],
                    ["hour", "readings.hour", "INTEGER with CHECK 0..23", "validated"],
                    ["pm25, pm10, no2", "readings.pm25, pm10, no2", "REAL, NULL allowed", "NULL = no valid value (never 0)"],
                    ["temp", "readings.temp_c", "REAL", "converted to °C where needed"],
                    ["(derived)", "readings.pm25_imputed", "INTEGER 0/1", "1 when the PM2.5 value was filled, not measured"],
                    ["(metadata)", "stations.reports_fahrenheit", "INTEGER 0/1", "1 for the two Fahrenheit stations"]], [2.6 * cm, 4.6 * cm, 3 * cm, 6.4 * cm], font=7.2)
    story += [P("<b>Keys.</b> stations: PRIMARY KEY station_id (name UNIQUE). readings: PRIMARY KEY (station_id, day, hour) - a reading is identified by station, "
                "day and hour, so the database itself rejects a duplicate, and the key's index also makes 'one station, one period' queries fast. The "
                "schema is created by common/store.py (Part B).")]
    story += [P("A1.3 - CSV or SQL? (2 marks)", H2)]
    rows = [["Question of the board", "From the CSV files", "From SQLite"],
            ["Q1 Average PM2.5 of one station in October", "read all files (or the station's file), convert to numbers, filter by date, average - a full scan every time",
             "<font name='DVM'>WHERE station = ? AND day BETWEEN …</font> + AVG; uses the (station, day) index"],
            ["Q2 Which station has the highest mean PM2.5?", "read everything, keep a sum and count per station", "<font name='DVM'>GROUP BY station ORDER BY AVG DESC LIMIT 1</font> - one line"],
            ["Q3 Which hours of the day are the worst?", "read everything, sums per hour", "<font name='DVM'>GROUP BY hour ORDER BY AVG DESC LIMIT 3</font>"]]
    story += table(rows, [4.6 * cm, 6 * cm, 6 * cm], font=7.4)
    story += [P(f"Measured on {a1[0]['rows']:,} rows (12 stations, one year) the three questions took {ms(a1[0]['Q1']['pandas'])}, {ms(a1[0]['Q2']['pandas'])} and "
                f"{ms(a1[0]['Q3']['pandas'])} with a fresh pandas read each time and {ms(a1[0]['Q1']['sql_idx'])}, {ms(a1[0]['Q2']['sql_idx'])} and {ms(a1[0]['Q3']['sql_idx'])} in SQLite "
                f"(Q1 with the index). SQL states <i>what</i> is wanted, keeps the data in one checked place (types, primary key) and can be shared by many programs; CSV files need "
                "no server and suit a one-time look at a single file.")]
    story += [P("Alternative concept and complexity analysis (A1)", H2),
              P("<b>CSV only, loaded into a pandas DataFrame for every question.</b> Each question starts with <font name='DVM'>read_csv</font> and then filters or groups. "
                "Time per question: reading and parsing n rows is <b>O(n)</b> every time, even for a question about one station, so n grows with every day of data. "
                "With SQLite the data are loaded once (O(n) once), Q1 then uses the (station, day) index and costs <b>O(log n + k)</b> for the k matching rows; whole-table "
                "questions (Q2, Q3) are still O(n) but are computed inside the database without creating Python objects. Space: the CSV design needs the CSV on disk "
                "plus the DataFrame in memory for the duration of the question; SQLite needs one database file on disk and only the pages being read in memory.")]
    story += table([["Rows", "CSV file", "SQLite file", "DataFrame in memory", "Q1 pandas", "Q1 SQL + index", "One-off SQLite load"]] +
                   [[f"{x['rows']:,}", f"{x['csv_mb']:.1f} MB", f"{x['db_mb']:.1f} MB", f"{x['df_mb']:.0f} MB", ms(x['Q1']['pandas']), ms(x['Q1']['sql_idx']), ms(x['load'])] for x in a1],
                   [2.2 * cm, 2 * cm, 2.2 * cm, 2.8 * cm, 2.4 * cm, 2.6 * cm, 2.6 * cm], font=7.2)
    story += [P(f"At {a1[1]['rows']:,} rows the indexed Q1 is about {a1[1]['Q1']['pandas'] / a1[1]['Q1']['sql_idx']:,.0f} times faster than re-reading the CSV; the "
                "load cost is paid back after one or two questions. (Experiment: A1/csv_vs_sql.py.)")]
    # ------------------------------------------------------------------ A2
    story += [P("Task A2 - Design the cleaning and normalisation (K4 - Analyse, 5 marks)", H2), P("A2.1 - Cleaning rules (2 marks)", H2)]
    story += table([["Problem", "Rule", "Justification"],
                    ["Missing PM2.5, PM10, NO₂ (blank, NA, text)", "<b>Forward fill</b> from the previous valid value of the same station for at most 3 consecutive hours; "
                     "a longer gap stays missing (NULL). Every filled PM2.5 value is flagged (pm25_imputed = 1).",
                     "Air quality changes slowly from hour to hour, so a short carry-forward is a reasonable estimate; a long outage must not be invented. "
                     "A median would ignore the time of day (the evening peak). The flag keeps the data honest."],
                    ["Missing temperature", "Fill with the <b>median temperature of that station and day</b>", "Temperature follows the sun, so the day's median is a "
                     "better guess than the previous hour; median is not disturbed by one faulty value."],
                    ["Impossible values: PM2.5, PM10, NO₂ outside 0-999; temperature outside -10 to 60 °C", "Treat as <b>missing</b> (then the rule above applies); count them in the report",
                     "A value no sensor can produce is a fault, not a measurement; deleting the whole row would also lose the valid pollutants in it."],
                    ["Duplicate rows", "Key = (station, date, hour); keep the <b>first</b>, drop the rest", "A resent line is not a second measurement; the primary key demands one row."],
                    ["Fahrenheit temperatures", "For stations flagged as reporting °F (stations.reports_fahrenheit) convert with C = (F - 32) × 5/9 <i>before</i> the range check",
                     "Without conversion 80 °F would be rejected as impossible and good data lost; the flag is the board's knowledge, not a guess."],
                    ["Names, dates, hours", "Trim and Title-Case names; accept 4 date formats and write ISO; hour must be 0-23, else the row is rejected and counted", "A single standard makes grouping and joining reliable."]],
                   [3.6 * cm, 6.5 * cm, 6.5 * cm], font=7.2)
    story += [P("A2.2 - Normalisation (2 marks)", H2)]
    story.append(code("""ALGORITHM MinMax(values)                             ALGORITHM ZScore(values)
    lo <- minimum of values;  hi <- maximum              m <- mean of values;  s <- standard deviation (population)
    IF hi = lo THEN RETURN list of 0.0                   IF s = 0 THEN RETURN list of 0.0
    RETURN [ (v - lo) / (hi - lo) FOR EACH v ]           RETURN [ (v - m) / s FOR EACH v ]"""))
    story += bullets([
        "<b>Min-max</b> gives values between 0 and 1 and keeps the shape of the data; it is appropriate to compare pollutants of different units on one chart, "
        "for algorithms that need a fixed range (neural networks, distance-based methods) and for a 'relative pollution index'. It is sensitive to outliers: one value of 999 "
        "squeezes all other values towards 0 - so impossible values must be removed first.",
        "<b>Z-score</b> gives mean 0 and standard deviation 1; it is appropriate when the data are roughly bell-shaped, when outliers must be recognised (|z| > 3 is unusual) "
        "and for statistical methods that assume a standard scale. It has no fixed range."])
    story += [P("A2.3 - Standard formats (1 mark)", H2)]
    story += table([["Item", "Standard in the cleaned data"],
                    ["Date", "ISO 8601 text <font name='DVM'>YYYY-MM-DD</font>; hour a separate integer 0-23"],
                    ["Station name", "Trimmed, single spaces, Title Case (<font name='DVM'>Anna Nagar</font>, <font name='DVM'>T. Nagar</font>); stored once in stations"],
                    ["Numbers", "Decimal point, no units or thousands separators, one decimal place (µg/m³ for pollutants, °C for temperature); missing = NULL, never 0 or the text 'NA'"],
                    ["Text files", "UTF-8, comma delimiter, header in lower case, newline-terminated lines"]], [3.2 * cm, 13.4 * cm], font=7.6)
    st = a2["strategies"]
    story += [P("Alternative concept and complexity analysis (A2)", H2),
              P("<b>Drop missing readings instead of filling them.</b> The rule becomes: remove every row (or value) that is missing and compute averages from what is left. "
                "In the experiment (A2/missing_strategies.py) the true values are known: 12 stations × 31 days, "
                f"{8928 - st['drop missing']['kept']:,} of 8,928 readings were removed at random (5%) or in outages of 5-8 hours.")]
    story += table([["Strategy", "Readings kept", "Error of the daily mean (µg/m³)", "Bias", "Error of the filled values"],
                    ["drop", f"{st['drop missing']['kept']:,}", f"{st['drop missing']['mae']:.3f}", f"{st['drop missing']['bias']:+.3f}", "-"],
                    ["forward fill (≤ 3 h)", f"{st['forward fill (at most 3 hours)']['kept']:,}", f"{st['forward fill (at most 3 hours)']['mae']:.3f}", f"{st['forward fill (at most 3 hours)']['bias']:+.3f}",
                     f"{st['forward fill (at most 3 hours)']['fill_err']:.1f} ({st['forward fill (at most 3 hours)']['filled']} values)"],
                    ["median fill", f"{st['fill with the station median']['kept']:,}", f"{st['fill with the station median']['mae']:.3f}", f"{st['fill with the station median']['bias']:+.3f}",
                     f"{st['fill with the station median']['fill_err']:.1f} ({st['fill with the station median']['filled']} values)"]],
                   [3.6 * cm, 2.6 * cm, 4 * cm, 2 * cm, 4.4 * cm], font=7.4)
    t = a2["timing"]
    story += [P("<b>Effect on the daily averages:</b> in this data all three give daily means within about 0.8 µg/m³ of the truth, so for a <i>daily average</i> dropping is almost as good. "
                "Dropping has two other costs: the number of valid readings per day varies (the daily mean then rests on fewer hours, and outages at the evening peak bias it), and "
                "hour-by-hour questions (worst hour of the day) lose their rows. Filling keeps a complete hourly series but invents values (a typical filled value is "
                f"{st['forward fill (at most 3 hours)']['fill_err']:.0f}-{st['fill with the station median']['fill_err']:.0f} µg/m³ away from the truth), which is why they are flagged.")]
    story += [P(f"<b>Time and space.</b> Dropping and forward fill are one pass, O(n); a median needs sorting, O(n log n): for n = {t[1]['n']:,} the times were "
                f"{ms(t[1]['drop'])} (drop), {ms(t[1]['ffill'])} (forward fill) and {ms(t[1]['median'])} (median). Space: drop O(n) for the filtered copy, forward fill O(n) for the output, "
                f"median O(n) extra for the sorted copy (peak {t[1]['mem_median'] / 1e6:.1f} MB against {t[1]['mem_ffill'] / 1e6:.1f} MB).")]
    # ------------------------------------------------------------------ A3
    story += [P("Task A3 - Design the analysis and visualisation (K4 - Analyse, 5 marks)", H2), P("A3.1 - Choose the charts (3 marks)", H2)]
    story += table([["Question", "Chart", "Why this chart"],
                    ["Trend of PM2.5 over a month", "<b>Line chart</b> (daily mean on y, day on x; one line per station)", "Time is an ordered continuous axis; a line shows direction, steps and peaks."],
                    ["Comparison of stations", "<b>Bar chart</b> of the monthly mean per station, sorted, with the 60 µg/m³ standard as a line; a <b>box plot</b> for the spread", "Categories without order: bar length is read accurately; the box plot adds median, spread and outliers that a mean hides."],
                    ["Relationship between temperature and PM2.5", "<b>Scatter plot</b> with the correlation coefficient in the title", "Two numeric variables; each point is one hour; the cloud shows direction, strength and outliers."],
                    ["Hours with the worst air", "<b>Bar chart</b> of the mean PM2.5 for each hour 0-23 (a histogram would show the distribution of values, not the hours)", "24 ordered categories on a repeating cycle; the highest bars name the worst hours."]],
                   [3.8 * cm, 6.2 * cm, 6.6 * cm], font=7.4)
    story += [P("A3.2 - The daily summary table (2 marks)", H2),
              P("<b>Columns:</b> station, day, min_pm25, max_pm25, mean_pm25, valid_readings (number of non-missing PM2.5 readings; 24 means a complete day). <b>Key:</b> (station, day).")]
    story.append(code("""ALGORITHM DailySummary
INPUT : table readings (station_id, day, hour, pm25, ...), table stations
OUTPUT: one row per (station, day)
BEGIN
    JOIN readings with stations on station_id               // to show station names
    GROUP the rows by (station name, day)                    // the database forms the groups
    FOR EACH group compute  MIN(pm25), MAX(pm25), AVG(pm25) rounded to 2 decimals, COUNT(pm25)     // NULL values are ignored
    SORT by station, day
    RETURN the rows                                          // 12 stations x 31 days = 372 rows for October
END"""))
    story += [P("The aggregate functions ignore NULL, so missing hours do not count as zero, and COUNT(pm25) states how many hours the mean rests on. Produced by an SQL "
                "<font name='DVM'>GROUP BY</font> query (A3/daily_summary.py: 372 rows printed in the evidence).")]
    story += [P("Alternative concept and complexity analysis (A3)", H2),
              P("<b>Python loops after reading all rows.</b> Read every row, append each reading to a dictionary of lists keyed by (station, day), then compute min, max, mean and count for every list. "
                "Time: reading is O(n), the statistics are O(n) in total, so <b>O(n)</b>; memory: <b>O(n)</b> because every reading is kept. The SQL query is also O(n) in time (one scan with a "
                "temporary grouping structure) but its memory is O(number of groups) - one running aggregate per (station, day) - and nothing is converted to Python objects. Measured (same results, compared):")]
    story += table([["Rows", "Loops: time", "Loops: peak memory", "SQL: time", "SQL: peak Python memory"]] +
                   [[f"{x['rows']:,}", ms(x['loops']), f"{x['mem_loops'] / 1e6:.1f} MB", ms(x['sql']), f"{x['mem_sql'] / 1e6:.1f} MB"] for x in a3], [3 * cm, 3 * cm, 3.8 * cm, 3 * cm, 3.8 * cm], font=7.4)
    # ------------------------------------------------------------------ A4
    story += [P("Task A4 - Plan debugging and profiling (K4 - Analyse, 4 marks)", H2), P("A4.1 - Debugging plan (2 marks)", H2)]
    story += bullets([
        "<b>print statements</b> - for the first quick look: print the raw row and the cleaned row for a few suspicious lines (for example the Fahrenheit station). Temporary only.",
        "<b>assert</b> - state what must always be true after cleaning: <font name='DVM'>assert -10 &lt;= temp_c &lt;= 60</font>, <font name='DVM'>assert 0 &lt;= hour &lt;= 23</font>, "
        "'no duplicate keys', 'row count after cleaning ≤ before'. A wrong assumption stops the program at the exact line with a message (shown in A4/output.txt).",
        "<b>logging</b> - permanent: <font name='DVM'>logging.debug</font> for every row decision, <font name='DVM'>logging.info</font> for the summary of each file (rows read, fixed, dropped), "
        "<font name='DVM'>logging.warning</font> for a file that is rejected. Messages carry level, time and module and go to a file; the level is changed in one place.",
        "<b>pdb</b> - when the cause is not obvious: <font name='DVM'>python -m pdb script.py</font>, <font name='DVM'>b</font> to set a breakpoint on the cleaning line, "
        "<font name='DVM'>c</font> to continue, <font name='DVM'>p temp</font> to print a variable, <font name='DVM'>n</font> to step. A scripted session on a deliberate bug "
        "(a Fahrenheit conversion that converts back again) is in the evidence; an IDE debugger offers the same with a mouse."])
    story += [P("A4.2 - Profiling plan (2 marks)", H2)]
    story += bullets([
        "<b>time.perf_counter()</b> - wrap each stage (read, clean, store, query, chart) to find which stage is slowest.",
        "<b>timeit</b> - repeat a small piece (one cleaning rule, one SQL query) many times and take the best, to compare two ways of writing it fairly.",
        "<b>cProfile</b> - run the whole stage under the profiler, sort by internal time (tottime) and cumulative time, and read which function is called how often and costs most; used in B3.3.",
        "Rule: measure first, change one thing, measure again, on data large enough (100,000+ rows) for the differences to show."])
    ra = {r[0]: r[1] for r in a4["rows"]}
    base = ra["no debugging output (baseline)"]
    story += [P("Alternative concept and complexity analysis (A4)", H2),
              P("<b>print statements for all debugging instead of logging and a debugger.</b> Every question is answered by adding a print and re-running; to find a fault in a loop over "
                "n rows one prints inside the loop, so the output grows with n. Measured for 20,000 loop iterations (A4/debug_overhead.py):")]
    story += table([["Variant", "Time", "Extra per call"]] +
                   [[esc(k), f"{v:.4f} s", f"{(v - base) / 20000 * 1e6:.2f} µs"] for k, v in a4["rows"]], [8.6 * cm, 3.4 * cm, 4.6 * cm], font=7.4)
    story += [P(f"A print to a file costs about {(ra['print() to a file on every iteration'] - base) / 20000 * 1e6:.1f} µs per call, logging at DEBUG level about "
                f"{(ra['logging.debug, level DEBUG, file handler'] - base) / 20000 * 1e6:.1f} µs (formatting, time stamp, handler), so thousands of calls add a time proportional to the "
                f"number of calls, O(n), and printing to a console is slower still. When the program is finished: <b>print</b> statements must be deleted or hidden behind "
                "<font name='DVM'>if DEBUG:</font> (a test remains, and a forgotten print still floods the output); <b>logging</b> stays in the code and is switched off by setting the level to "
                f"WARNING, after which a call costs only {(ra['logging.debug, level WARNING (switched off)'] - base) / 20000 * 1e6:.2f} µs; <b>assert</b> is removed completely by running "
                f"<font name='DVM'>python -O</font>; a <b>debugger</b> has nothing to switch off. Note that <font name='DVM'>logging.debug(f'...')</font> still builds the string; "
                "<font name='DVM'>logging.debug('%s', x)</font> defers the formatting.")]
    # ------------------------------------------------------------------ A5
    b4 = J("B4/results.json")
    story += [P("Task A5 - Design an AI application for citizen complaints (K3 - Apply, 4 marks)", H2), P("A5.1 - Sentiment and summary (2 marks)", H2)]
    story.append(code("""ALGORITHM Sentiment(text)                                        ALGORITHM Summarise(text, freq, k)
INPUT : text, word lists POSITIVE, NEGATIVE, NEGATORS            INPUT : text, table freq of word counts over all complaints
OUTPUT: label                                                    OUTPUT: the k best sentences, in original order
BEGIN                                                            BEGIN
    words <- lower-case words of text                                sentences <- split text at . ! ?
    total <- 0                                                       FOR EACH sentence DO
    FOR i FROM 0 TO length(words) - 1 DO                                 important <- distinct words of the sentence that are not stop words and have freq >= 2
        value <- +1 IF words[i] IN POSITIVE                              score <- sum of freq[w] FOR EACH w IN important
                 -1 IF words[i] IN NEGATIVE ELSE 0                   END FOR
        IF i > 0 AND words[i-1] IN NEGATORS THEN value <- -value     sort sentences by score (highest first; ties: earlier sentence)
        total <- total + value                                       RETURN the first k sentences, put back in original order
    END FOR                                                      END
    IF total > 0 THEN RETURN "positive"
    IF total < 0 THEN RETURN "negative"                          // frequency table built once: count every non-stop word of
    RETURN "neutral"                                             // every complaint, O(total words)
END"""))
    story += [P("<b>Negation:</b> 'not good' flips +1 to -1 because the word before the sentiment word is a negator. <b>Extractive summary:</b> sentences are not rewritten, the "
                "ones that contain the words most citizens use are selected, so a greeting ('Hello sir, I live in Velachery') scores low and the sentence naming the problem scores high.")]
    story += [P("A5.2 - Basic chatbot (2 marks)", H2)]
    story.append(code("""ALGORITHM Answer(question, database)
BEGIN
    q <- lower-case question
    IF q contains a greeting word THEN RETURN the help text with examples
    pollutant <- first keyword of q found in {pm2.5, pm10, no2, temperature}, default pm2.5
    today <- the newest day in the readings table
    IF q contains "polluted" or "highest" THEN
        row <- query: station with the highest average of pollutant on day today        // parameterised SQL (?)
        RETURN sentence with the station and the value
    station <- the first station name from the stations table that occurs in q
    IF no station found THEN RETURN "I could not find a station" + list of stations
    IF q contains "hour" and "worst" THEN RETURN the hour with the highest average at station
    row <- query: average, minimum, maximum of pollutant at station on day today        // parameterised SQL (?)
    IF row is empty THEN RETURN "no readings"
    RETURN sentence with the values (and the air-quality band for PM2.5)
END"""))
    story += bullets([
        "<b>Limitations:</b> it understands only the keywords and station names that were programmed ('Adyar's air for my asthma' returns the PM2.5 figure, not health advice; "
        "'Will it rain tomorrow?' is answered with the station list); spelling mistakes, other languages (Tamil), synonyms and follow-up questions ('and yesterday?') are not understood; "
        "it has no memory of the conversation; it answers only from the database (today means the newest day stored, not the clock); it cannot say why or predict; one wrong keyword "
        "gives a confident wrong answer (the pollutant defaults to PM2.5). A chatbot must therefore always say what it could not understand. The working program is A5/chatbot.py."])
    t = b4
    story += [P("Alternative concept and complexity analysis (A5)", H2),
              P("<b>A trained model instead of a word list.</b> A Naive Bayes classifier counts, from labelled complaints, how often each word occurs in positive, negative and neutral "
                "complaints and picks the class with the highest probability. It was implemented from scratch (B4/ai_tools.py) and trained on the 60 labelled complaints; a pre-trained "
                "language model would instead be downloaded with a library and run on each complaint.")]
    story += table([["Method", "Time per complaint", "Memory", "Accuracy on my 60 labels"],
                    ["Lexicon, assignment word list (v0)", f"{t['v0 scorer'] / 50000 * 1e6:.1f} µs", "14 words (under 1 KB)", f"{t['agree']['v0 assignment lexicon (one-word negation)']}/60 = 62%"],
                    ["Lexicon, larger list + better negation (v2)", f"{t['v2 scorer'] / 50000 * 1e6:.1f} µs", "64 words (about 2 KB)", f"{list(t['agree'].values())[2]}/60 = 92% (optimistic: the list was written after reading these complaints)"],
                    ["Naive Bayes, trained on 59 and tested on the 60th (leave-one-out)", f"{t['nb_time'] / 50000 * 1e6:.1f} µs", "about 43 KiB for a 336-word vocabulary; grows with the vocabulary", f"{t['nb_loo']}/60 = {t['nb_loo'] / 60 * 100:.0f}%"],
                    ["Pre-trained language model", "not measured here (needs a download; typically milliseconds to a second on a CPU)", "typically hundreds of MB", "typically the highest, also on sarcasm and mixed opinions, but not tested here"]],
                   [5 * cm, 3.2 * cm, 4 * cm, 4.4 * cm], font=7.2)
    story += [P("All word-based methods are O(words) per complaint; the lexicon is the cheapest and fully explainable. With only 60 labelled complaints Naive Bayes is no better "
                "than the plain word list (65% against 62%): a trained model needs many labelled examples (thousands) before it overtakes a good lexicon.")]


# ============================================================================= PART B
def part_b(story):
    b1alt, b2, b3, b4 = J("B1/alt_results.json"), J("B2/results.json"), J("B3/results.json"), J("B4/results.json")
    r1 = J("B1/results.json")
    a3 = J("A3/results.json")
    story += [P("PART B - IMPLEMENTATION AND EXPERIMENTAL INVESTIGATION (25 marks)", H1), P("Task B1 - Implement and validate the cleaning pipeline (K3 - Apply, 7 marks)", H2),
              P("B1.1 - Validate the implementation (2 marks)", H2),
              P("common/cleaning.py implements the rules of A2 with the csv module (functions <font name='DVM'>norm_station, norm_date, parse_number, min_max, z_score, clean_text</font>). "
                "B1/small_dirty.csv has 14 lines that contain every problem of A1.1: lowercase and padded names, NA, blank, negative, 9999 (twice, a duplicate), text, a dd/mm/yyyy date, an "
                "invalid date, hour 25, and a Fahrenheit station. <b>Before</b> and <b>after</b> cleaning:")]
    story.append(code(between("B1/output.txt", "=== B1.1 BEFORE", "=== Cleaning the 12 October station files ===")))
    story += [P("Every check in B1/pipeline.py passed (assert statements): 7 Adyar rows remain (the invalid date and hour 25 are rejected, the duplicate removed), PM2.5 gaps are filled "
                "with the previous value for at most 3 hours and flagged, the Manali temperatures are converted (80.6 °F → 27.0 °C), and min-max and z-score of the cleaned series are computed.")]
    story.append(code(funcs("common/cleaning.py", {"norm_station", "norm_date", "parse_number", "min_max", "z_score"})))
    story.append(code(funcs("common/cleaning.py", {"clean_text"}), 118))
    story += [P("B1.2 - Comparison with the design (1 mark)", H2)]
    story += table([["Design (Part A)", "Implementation", "Reason for the change"],
                    ["Fahrenheit stations known from stations.reports_fahrenheit", "Detected automatically: a station whose <b>median</b> 'temperature' is above 50 is converted; the flag is then stored in stations",
                     "A raw CSV file carries no station metadata. The detection found exactly Manali and Royapuram (asserted), the two real Fahrenheit stations."],
                    ["Impossible values → missing, then fill", "Same, but the counts are kept in a report (missing, impossible, filled)", "To show what the rules did (B1.1)."],
                    ["Dates: ISO", "Four input formats accepted; unparsable date or hour outside 0-23 → row rejected and counted", "The data contained dd/mm/yyyy; rejecting every such row would lose good data."],
                    ["No flag column for imputed values", "Column <font name='DVM'>pm25_imputed</font> added", "A filled value must stay distinguishable from a measured one."],
                    ["Plain open() of the file", "Bytes decoded with BOM/UTF-16/UTF-8/Windows-1252 detection and the delimiter detected", "Adversarial files of B2 (wrong encoding, semicolons)."],
                    ["Fill limit not specified", "Forward fill limited to 3 consecutive hours (FILL_LIMIT)", "Long outages must not be hidden."]], [4.6 * cm, 6.4 * cm, 5.6 * cm], font=7.2)
    story += [P("B1.3 - Store and query (2 marks)", H2),
              P("The 12 October files (8,974 raw lines) are cleaned and loaded with <font name='DVM'>executemany</font> (one call per table) into SQLite (common/store.py):")]
    story.append(code(read("common/store.py").split('SCHEMA = """')[1].split('"""')[0].strip() + "\n\n" + funcs("common/store.py", {"load_rows"})))
    story.append(code(between("B1/output.txt", "=== Cleaning the 12 October station files ===", "=== B1.3")))
    story.append(code(between("B1/output.txt", "Loaded ", "=== B1.4")))
    story += [P("The three SQL queries of A1.3 give the same answers as scanning the cleaned CSV (asserted): average PM2.5 of Adyar in October "
                f"{r1['answers']['q1']}, highest station {r1['answers']['q2'][0]} ({r1['answers']['q2'][1]}), worst hours {', '.join(str(h[0]) + ':00' for h in r1['answers']['q3'])}. "
                "The daily summary (A3.2) is produced by <font name='DVM'>GROUP BY</font> (A3/output.txt).")]
    story += [P("B1.4 - Visualise and interpret (2 marks)", H2)]
    charts = [("1_trend_line.png", "Fig. B1 - Trend of PM2.5 over October.",
               f"Daily mean PM2.5 rises steadily at all three stations through the month: Adyar from {r1['trend']['Adyar'][0]} to {r1['trend']['Adyar'][1]}, Guindy from {r1['trend']['Guindy'][0]} to "
               f"{r1['trend']['Guindy'][1]} and Manali from {r1['trend']['Manali'][0]} to {r1['trend']['Manali'][1]} µg/m³ (about +17). The three lines are roughly parallel, so the station ranking does "
               "not change: Manali is always the worst. (The rise is built into the synthetic data.)"),
              ("2_stations_bar.png", "Fig. B2 - Comparison of stations.",
               f"{r1['means'][0][0]} has the highest October mean ({r1['means'][0][1]}) and {r1['means'][-1][0]} the lowest ({r1['means'][-1][1]}). Eight of the twelve stations are above the 60 µg/m³ "
               "line and four below it. The line is the 24-hour standard, so comparing a monthly mean with it is only a rough yardstick."),
              ("3_stations_box.png", "Fig. B3 - Spread of hourly PM2.5 by station.",
               f"The boxes (middle 50% of hours) have a similar width at the cleanest and the dirtiest station (Manali {r1['spread']['Manali'][0]}-{r1['spread']['Manali'][1]}, "
               f"Adyar {r1['spread']['Adyar'][0]}-{r1['spread']['Adyar'][1]}): the stations differ in level, not in variability. Points above the whiskers are hours of unusually bad air."),
              ("4_temp_scatter.png", "Fig. B4 - Temperature and PM2.5 at Guindy.",
               f"The cloud slopes downward (r = {r1['corr']}, n = {r1['scatter_n']} hours): warmer hours tend to have less PM2.5. The relation is moderate - many points scatter widely - and it shows "
               "association, not cause: temperature and pollution both follow the time of day."),
              ("5_pm25_histogram.png", "Fig. B5 - Distribution of all valid PM2.5 readings.",
               f"The {r1['hist']['n']:,} readings have mean {r1['hist']['mean']} and median {r1['hist']['median']}, maximum {r1['hist']['max']}; the mean is slightly above the median because of a tail of bad hours. "
               "The cleaning worked: there are no negative or 9999 values."),
              ("6_hours_bar.png", "Fig. B6 - Hours with the worst air.",
               f"The worst hours are {r1['hours']['worst'][0][0]}:00 ({r1['hours']['worst'][0][1]}), {r1['hours']['worst'][1][0]}:00 ({r1['hours']['worst'][1][1]}) and {r1['hours']['worst'][2][0]}:00 ({r1['hours']['worst'][2][1]}) - "
               f"the evening and the morning rush hours; the best hour is {r1['hours']['best'][0]}:00 ({r1['hours']['best'][1]}), in the afternoon.")]
    for fn, cap, text in charts:
        story += img_B1(fn, cap) + [P("<b>Interpretation.</b> " + text)]
    story += [P("Complete the Code (B1/complete_the_code.py)", H2),
              P("TODO 1 reads the text with <font name='DVM'>csv.DictReader</font>, skips empty, 'NA' and negative readings and converts to float; TODO 2 scales with (v - min)/(max - min) rounded to 3 decimals "
                "(a constant series returns zeros instead of dividing by zero). The extra check skips values above 999 (the 5000 test row is skipped; 999 is kept). Output - the first two lines equal the expected output:"),
              code(funcs("B1/complete_the_code.py", {"load_clean", "min_max"})), code(read("B1/complete_output.txt"))]
    story += [P("Alternative concept and complexity analysis (B1)", H2),
              P("<b>pandas instead of csv and loops:</b> <font name='DVM'>read_csv</font>, <font name='DVM'>replace</font>/<font name='DVM'>to_numeric</font> for NA and text, boolean masks for impossible values, "
                "<font name='DVM'>drop_duplicates</font>, <font name='DVM'>groupby().ffill(limit=3)</font> and vectorised arithmetic for the Fahrenheit conversion (common/cleaning.py, clean_pandas). Both versions apply the same rules and "
                "give the same row count and mean PM2.5 (asserted).")]
    story += table([["Rows", "csv + loops: time", "pandas: time", "Speed-up", "loops: peak memory", "pandas: peak memory"]] +
                   [[f"{x['rows']:,}", ms(x['loops']), ms(x['pandas']), f"{x['loops'] / x['pandas']:.1f}×", f"{x['mem_loops'] / 1e6:.1f} MB", f"{x['mem_pandas'] / 1e6:.1f} MB"] for x in b1alt],
                   [2.6 * cm, 2.9 * cm, 2.6 * cm, 2.2 * cm, 3 * cm, 3.3 * cm], font=7.4)
    story += img("b1_alt.png", 13.5, "Fig. B7 - Cleaning with loops and with pandas (log-log).")
    story += [P(f"Both are O(n) in time (the curves are parallel straight lines), but pandas does the work in compiled code: about {b1alt[2]['loops'] / b1alt[2]['pandas']:.1f}× faster at a million rows and "
                f"about {b1alt[2]['mem_loops'] / b1alt[2]['mem_pandas']:.1f}× less memory (a Python float and tuple per value against 8 bytes in a numpy array). At 1,000 rows pandas is actually slower "
                "(fixed start-up cost). Memory is O(n) in both. The loop version is simpler to explain and has no dependency; pandas wins when the data are large.")]
    story.append(PageBreak())
    # ------------------------------------------------------------------ B2
    story += [P("Task B2 - Engineer adversarial data (K4 - Analyse, 5 marks)", H2), P("B2.1 - Awkward files", H2)]
    story.append(code(between("B2/output.txt", "=== B2.1", "=== B2.2")))
    story += [P("<b>What it reveals:</b> the program separates <i>recoverable</i> oddities (semicolon delimiter, Windows-1252, UTF-16, byte-order mark, capitals in the header - each handled and reported) from "
                "<i>unrecoverable</i> ones (empty file, missing required column, binary garbage - rejected with a message that names the problem, never a traceback and never a silently empty result). "
                "The first design assumed one encoding and one delimiter; the adversarial files forced explicit decoding and sniffing. A header-only file gives 0 rows without error, which the "
                "daily job should treat as suspicious.")]
    story += [P("B2.2 - A quote character in a station name", H2), code(between("B2/output.txt", "=== B2.2", "=== B2.3"))]
    story += [P("<b>Explanation.</b> With <font name='DVM'>+</font> the name becomes part of the SQL text: the apostrophe in <i>Besant Nagar's</i> ends the string early, so SQLite sees a syntax error "
                "(<font name='DVM'>OperationalError: near \"s\"</font>). The input <font name='DVM'>Adyar' OR '1'='1</font> changes the meaning of the query: "
                f"the condition is always true and the average of <i>all</i> rows ({b2['all_avg']:.2f}) is returned - data the user did not ask for (SQL injection). "
                "The stacked statement <font name='DVM'>; DROP TABLE</font> was refused only because sqlite3's execute() runs one statement. With a <font name='DVM'>?</font> placeholder the value "
                "travels separately from the SQL text and is always treated as data: the quote is just a character (the correct average 70.0 is found) and the injection string is simply a "
                "station name that does not exist (None).")]
    story += [P("B2.3 - Sentences that fool the sentiment scorer", H2), code(between("B2/output.txt", "=== B2.3", "=== Alternative"))]
    story += [P("<b>Failures and what they reveal:</b> <b>sarcasm</b> ('Oh great… just wonderful') - a word list reads the words, not the intention; the larger lexicon makes it worse (positive). "
                "<b>Double negatives</b> - the rule 'previous word is a negator' cannot compose two negations. <b>Mixed opinions</b> ('fast but rude') - positive and negative cancel to neutral; a person "
                "weighs the part after 'but'. <b>Negation at distance or in contractions</b> ('not very helpful', 'isn't') - fixed in v2 by skipping intensifiers and adding contractions, which shows that "
                "the failures are partly repairable. <b>Words absent from the list</b> ('cannot breathe', misspellings) give neutral. <b>Questions</b> are scored by their words. "
                "The scorer is a useful triage tool but not a judge of opinion: its design (bag of words, local negation) is exactly where each failure comes from.")]
    story += [P("Complete the Code (B2/complete_the_code.py)", H2), code(read("B2/complete_the_code.py").split("# TODO 1")[1].split("print(station_average")[0].strip()), code(read("B2/complete_output.txt")),
              P("<b>Why the injection attempt returns None:</b> the whole text <font name='DVM'>Adyar' OR '1'='1</font> is bound as <i>one value</i> for <font name='DVM'>station = ?</font>; no station has that name, "
                "so no row matches, and AVG over zero rows is NULL, which Python shows as None. The text is never parsed as SQL.")]
    ins = b2["insert_timing"]
    story += [P("Alternative concept and complexity analysis (B2)", H2),
              P("<b>f-string SQL.</b> <font name='DVM'>f\"SELECT … WHERE station = '{name}'\"</font> with <font name='DVM'>Adyar' OR '1'='1</font> becomes <font name='DVM'>WHERE station = 'Adyar' OR '1'='1'</font>: "
                "always true, so every row is returned/averaged (shown above: 66.25, the mean of all rows) - a leak - and a name with an apostrophe crashes the query. It is also re-parsed as new SQL text on every call. "
                "<b>executemany versus execute() in a loop:</b> both are O(n); executemany runs the loop inside the C library and prepares the statement once.")]
    story += table([["Rows", "executemany", "execute() loop", "Ratio"]] + [[f"{x['n']:,}", ms(x['many']), ms(x['loop']), f"{x['loop'] / x['many']:.2f}×"] for x in ins], [3 * cm, 3.4 * cm, 3.4 * cm, 2.4 * cm])
    story += [P(f"executemany is about {min(x['loop'] / x['many'] for x in ins):.1f}-{max(x['loop'] / x['many'] for x in ins):.1f}× faster (the gain shrinks as the per-row work of SQLite itself dominates). The costly mistake is committing after every row: on a file database, "
                f"{b2['commit']['n']:,} rows took {b2['commit']['each']:.2f} s with a commit per row against {b2['commit']['one'] * 1000:.1f} ms with one executemany and one commit "
                f"({b2['commit']['each'] / b2['commit']['one']:,.0f}×), because each commit forces the data to disk.")]
    story.append(PageBreak())
    # ------------------------------------------------------------------ B3
    story += [P("Task B3 - Loops vs libraries vs SQL (K4 - Analyse, 8 marks)", H2), P("B3.1 - Correctness on small data (2 marks)", H2),
              P("Daily mean PM2.5 per station by (1) csv + dictionary of lists + <font name='DVM'>statistics.mean</font>, (2) pandas <font name='DVM'>groupby</font>, (3) SQL <font name='DVM'>GROUP BY</font> "
                "(B3/loops_pandas_sql.py). On 3 stations × 5 days all three agree (and at every larger size, to 6 decimals):")]
    story.append(code(between("B3/output.txt", "=== B3.1", "=== B3.2")))
    story.append(code(funcs("B3/loops_pandas_sql.py", {"by_loops", "by_pandas", "by_sql", "load_sqlite"})))
    story += [P("B3.2 - Increase the data size (2 marks)", H2), code(between("B3/output.txt", "=== B3.2", "=== B3.3"))]
    story += img("b3_timing.png", 11, "Fig. B8 - Time to compute the daily means (log-log): all methods grow linearly with the number of readings.")
    tm = b3["timing"]
    story += [P("B3.3 - Profile the plain-Python version (2 marks)", H2), code(between("B3/output.txt", "=== B3.3", "=== Alternative")),
              P(f"<b>Result.</b> In <i>own time</i> the largest single entry is <font name='DVM'>by_loops</font> itself ({b3['profile_loop_tot']:.2f} s: the csv reading and grouping loop). But the function that takes "
                f"the most time <i>among the functions it calls</i> is <b>statistics.mean</b>: called 4,380 times it costs {b3['profile_mean_cum']:.2f} s cumulative, "
                f"{b3['profile_mean_cum'] / b3['profile_total'] * 100:.0f}% of the profiled run - because it converts every value to an exact fraction (<font name='DVM'>_exact_ratio</font>, "
                "<font name='DVM'>fractions</font>) to give a correctly rounded result. A running sum with a division (below) removes that cost.")]
    story += [P("B3.4 - Engineering trade-off (2 marks)", H2),
              P(f"<b>Observed:</b> at {tm[2]['rows']:,} readings pandas took {ms(tm[2]['pandas'])}, loops {ms(tm[2]['loops'])} ({tm[2]['loops'] / tm[2]['pandas']:.1f}× slower), the loop with a running sum "
                f"{ms(tm[2]['running'])}, SQL {ms(tm[2]['sql_query'])} for the query alone but {ms(tm[2]['sql_load'] + tm[2]['sql_query'])} including the one-off load. pandas and SQL "
                "run the loops in compiled code; the plain loop pays Python's cost per row, and statistics.mean adds a large constant. Differences between pandas and SQL are small; what matters is "
                "<i>where the data already are</i>: SQL's query is fast once the data are loaded, but loading is the larger cost.")]
    story += bullets(["<b>Quick one-time analysis:</b> pandas - a few lines (read_csv, groupby), fast enough, no database to design, easy to plot.",
                      "<b>Daily automated report:</b> SQL on the stored, validated, indexed table: the data are loaded once per day (not re-parsed for every report), the query is short, repeatable and can be "
                      "scheduled; a running-sum Python loop is the fallback when no database is available and memory is limited."])
    am = b3["alt_mem"]
    story += [P("Alternative concept and complexity analysis (B3)", H2),
              P("<b>One pass with a running sum and count per (station, day):</b> <font name='DVM'>acc[(station, day)] = [sum, count]</font>, mean = sum/count at the end (function "
                "<font name='DVM'>by_running_sum</font>). No reading is stored.")]
    story.append(code(funcs("B3/loops_pandas_sql.py", {"by_running_sum"})))
    story += [P(f"Time is O(n) in both. Space: the running-sum version keeps one [sum, count] pair per group, <b>O(stations × days)</b>; storing all readings first keeps <b>O(n)</b> values. Measured at "
                f"12 stations (105,120 readings, 4,380 groups): peak {list(am.values())[0] / 1e6:.1f} MB against {list(am.values())[1] / 1e6:.1f} MB, and the running sum was also "
                f"{tm[1]['loops'] / tm[1]['running']:.1f}× faster ({ms(tm[1]['running'])} against {ms(tm[1]['loops'])}). Results are identical (checked). The drawback: it can compute only "
                "what was planned (sum, count); a median or a second pass would need the readings.")]
    story.append(PageBreak())
    # ------------------------------------------------------------------ B4
    ix = J("B4/index_results.json")
    story += [P("Task B4 - Final engineering decision (K5 - Evaluate, 5 marks)", H2), P("B4.1 - Sentiment scorer and summariser on 60 complaints (2 marks)", H2),
              P("B4/complaints.csv holds 60 complaints (40 one-sentence, 20 three-sentence) with <b>my own reading</b> of each as positive, negative or neutral, and for the 20 long ones the word that names the "
                "real problem. B4/evaluate.py scores them (full output in the source-code PDF):")]
    story.append(code(between("B4/output.txt", "=== Sentiment", "=== Naive Bayes")))
    story += img("b4_agreement.png", 9.5, "Fig. B9 - Agreement with my own reading.")
    story += [P(f"<b>Agreement:</b> the scorer with the assignment's word list agrees with {b4['agree']['v0 assignment lexicon (one-word negation)']} of 60 labels (62%). Its mistakes are mostly "
                "<i>neutral instead of negative</i> ({b4['conf_v0']['negative->neutral']} of the 37 negative complaints), because words such as 'terrible', 'dust', 'horrible' are not in the list. The larger list and better "
                f"negation reach {list(b4['agree'].values())[2]} of 60, but that figure is optimistic - I wrote that list after reading these complaints; on new complaints it would be lower. Words absent from the lexicon, "
                "sarcasm and mixed opinions remain wrong.")]
    story.append(code(between("B4/output.txt", "=== Summariser:", "=== Summariser time")))
    story += [P(f"<b>Summariser:</b> the frequency-based summary keeps the key word of the complaint in {b4['hit_best']} of {b4['n_long']} three-sentence complaints, taking the first sentence only {b4['hit_first']} "
                f"of {b4['n_long']} (the first sentence is usually a greeting). Where it failed, the key word occurred only once in the whole set (a rare word such as 'foam' or 'filters' counts as unimportant). "
                f"For the whole set of complaints, three selected sentences cover {b4['cover_best']} of the 10 most frequent words against {b4['cover_first']} for the first three sentences.")]
    story += [P("B4.2 - Check the database: index on (station, day) (1 mark)", H2)]
    story.append(code(read("B4/index_output.txt")))
    story += img("b4_index.png", 11, "Fig. B10 - Query times on 1,051,200 rows without and with the index on (station, day).")
    q1 = "Q1 mean PM2.5 of Adyar in October"
    story += [P(f"<b>Effect.</b> The slowest query was <b>Q2</b> (station with the highest mean, a full-table aggregate, {ms(ix['before: no index']['Q2 station with the highest mean'])}). The (station, day) index "
                f"reduced it only to {ms(ix['after: index on (station, day)']['Q2 station with the highest mean'])} ({ix['before: no index']['Q2 station with the highest mean'] / ix['after: index on (station, day)']['Q2 station with the highest mean']:.1f}×), because it still has to read every row. The index transformed the queries "
                f"that look at <i>one station</i>: Q1 fell from {ms(ix['before: no index'][q1])} to {ms(ix['after: index on (station, day)'][q1])} "
                f"({ix['before: no index'][q1] / ix['after: index on (station, day)'][q1]:.0f}×; the plan changes from SCAN to SEARCH USING INDEX) and Q4 about {ix['before: no index']['Q4 daily min/max/mean/count, one station'] / ix['after: index on (station, day)']['Q4 daily min/max/mean/count, one station']:.0f}×. Q3 (group by hour) did not use the index; "
                f"a covering index on (hour, pm25) reduced it from {ms(ix['after: index on (station, day)']['Q3 three worst hours of the day'])} to "
                f"{ms(ix['after: plus covering index on (hour, pm25)']['Q3 three worst hours of the day'])}. The price: building the index took {ix['index_build']:.2f} s and the file grew from "
                f"{ix['size0'] / 1e6:.0f} to {ix['size1'] / 1e6:.0f} MB, and every later insert must also update it. (In the normalised design of B1.3 the primary key already provides this index.)")]
    story += [P("B4.3 - Production decision (2 marks)", H2)]
    rows_year = 112 * 96 * 365
    story += [P(f"<b>Scale.</b> 112 stations × 96 readings per day = 10,752 rows per day, about {rows_year / 1e6:.1f} million rows per year; 50,000 complaints per month.")]
    story += table([["Topic", "Decision", "Evidence from my measurements"],
                    ["Storage", "<b>SQLite</b> (one file) with the normalised tables of A1.2 and the (station, day) index; load each day's cleaned rows with <b>one executemany in one transaction</b>. "
                     "Move to a server database (PostgreSQL) only when several programs must write at the same time or the table reaches hundreds of millions of rows.",
                     f"Loading 1.05 million rows took {ms(tm[2]['sql_load'])}; the daily batch of 10,752 rows takes a few milliseconds. One commit instead of one per row is {b2['commit']['each'] / b2['commit']['one']:,.0f}× faster. "
                     f"A year of the new network is about 4 times the table I tested: index lookups stay under a millisecond ({ms(ix['after: index on (station, day)'][q1])})."],
                    ["Cleaning", "Keep the rules of A2; run them with <b>pandas</b> on each day's files (or chunks), keep the loop version as the readable reference for testing.",
                     f"pandas was {b1alt[2]['loops'] / b1alt[2]['pandas']:.1f}× faster and used {b1alt[2]['mem_loops'] / b1alt[2]['mem_pandas']:.1f}× less memory than loops at a million rows (loops: {ms(b1alt[2]['loops'])})."],
                    ["Analysis", "<b>SQL</b> GROUP BY for daily and monthly summaries, stored in a summary table; charts from the summary, not from the raw rows.",
                     f"Daily summary of 1.05 million rows in SQL: {ms(a3[1]['sql'])} against {ms(a3[1]['loops'])} for loops, with {a3[1]['mem_loops'] / a3[1]['mem_sql']:.0f}× less Python memory."],
                    ["Complaints (50,000 / month)", "Use the <b>lexicon scorer now</b> for triage and the frequency summariser for a daily digest; at the same time have staff label a few thousand complaints "
                     "and then <b>train a Naive Bayes / logistic-regression model</b>, tested on complaints it has not seen. A pre-trained language model only if that is still not accurate enough.",
                     f"Speed is not the problem: 50,000 complaints took {b4['v2 scorer']:.2f} s (lexicon), {b4['nb_time']:.2f} s (Naive Bayes). Accuracy is: the assignment lexicon agreed with my labels in only 62% of cases "
                     "and failed on sarcasm, double negatives and mixed opinions even after tuning; Naive Bayes with 60 examples reached only 65%, so it needs far more labelled data. A language model "
                     "would handle some of these cases but needs much more memory and time and was not measured here."]],
                   [2.6 * cm, 6.6 * cm, 7.4 * cm], font=7.2)
    story += [P("<b>Conclusion:</b> the simple methods are fast enough at the new scale; the weakness is the accuracy of the word-list sentiment, not the speed or the storage. A staged plan "
                "(lexicon now, labelled data collection, then a trained model) uses measurements at every step.")]
    story += [P("Complete the Code (B4/complete_the_code.py)", H2),
              P("TODO 1 gives each word its value (+1, -1 or 0) and flips it when the previous word is a negator. The output is identical to the expected output; the last two lines are complaints that "
                "are labelled wrongly."), code(funcs("B4/complete_the_code.py", {"score"})), code(read("B4/complete_output.txt")),
              P("<b>Wrongly labelled complaint:</b> <i>'The air isn't clean anymore, it smells of fumes.'</i> is labelled <b>positive</b> (score +1) although it is a complaint: 'isn't' is not in the "
                "negator set (only not, never, no), so 'clean' keeps its +1, and 'smells' and 'fumes' are not in the negative list. A second one: <i>'I am happy that the smoke from the garbage yard has "
                "stopped.'</i> is labelled <b>negative</b> because 'smoke' counts -1 and 'happy' is unknown - the scorer cannot see that the smoke is gone.")]
    story += [P("Alternative concept and complexity analysis (B4)", H2),
              P("<b>First k sentences instead of the sentences with the most frequent important words.</b> The summary of a complaint is simply its first k sentences "
                "(<font name='DVM'>summarise_first</font>, a split at the k-th sentence boundary).")]
    story.append(code(funcs("B4/ai_tools.py", {"summarise_first", "summarise_best", "sentence_score"})))
    story += table([["Method", "Quality on the 20 three-sentence complaints", "Time per complaint", "Space"],
                    ["First k sentences", f"key word kept in {b4['hit_first']}/{b4['n_long']}", f"{b4['sum_time_first'] * 1e6:.1f} µs - O(1) work if the split stops at k sentences (never reads the rest)", "O(1): no table"],
                    ["Most frequent important words", f"key word kept in {b4['hit_best']}/{b4['n_long']}", f"{b4['sum_time_frequency'] * 1e6:.1f} µs - O(words): every sentence is scored", "O(distinct words) for the frequency table (30 KiB for 274 words; built once in 0.35 s for 50,000 complaints)"]],
                   [3.4 * cm, 4.2 * cm, 5 * cm, 4 * cm], font=7.4)
    story += [P("Taking the first sentences is ten times cheaper but fails exactly where it matters, because citizens open with greetings and context; the frequency method pays O(words) per complaint and a "
                "shared table to find the sentence that names the problem.")]


def img_B1(name, cap):
    path = os.path.join(ROOT, "B1", "charts", name)
    w, h = PILImage.open(path).size
    return [KeepTogether([Image(path, width=11.5 * cm, height=11.5 * cm * h / w), P(cap, CAP)])]


def build(path, story, title):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.5 * cm, bottomMargin=1.7 * cm, title=title, author=args.name)
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)


def build_report(path):
    story = []
    cover(story)
    part_a(story)
    story.append(PageBreak())
    part_b(story)
    build(path, story, "Python Programming - Assignment 5 (CO5) - Report")


def excerpt(rel, n):
    lines = read(rel).split("\n")
    return "\n".join(lines[:n]) + (f"\n... ({len(lines) - n} more lines; full file in the repository)" if len(lines) > n else "")


def build_code(path):
    story = []
    cover(story, second=True)
    story += [P("How to run", H1), P("Folders: A1, A2, A3, A4, A5 (experiments for the Part A alternatives and chatbot), B1 … B4, common. From the repository root:"),
              code("pip install -r requirements.txt\npython run_all.py                       # runs every program and saves the outputs\n"
                   "python build_report.py --github <URL>   # builds the two PDFs\n\n# one program at a time, for example\ncd B2\npython complete_the_code.py\npython adversarial.py"),
              P("The large data files (up to 1,051,200 rows) are generated by common/bigdata.py into the temporary folder; the October station files in B1/data and the SQLite database "
                "B1/air.db are created by B1/make_october.py and B1/pipeline.py. Long data files are shown here as excerpts."), PageBreak()]
    sections = [
        ("Common modules", [("common/gen_data.py", 999), ("common/cleaning.py", 999), ("common/store.py", 999), ("common/bigdata.py", 999)]),
        ("B1 - cleaning pipeline", [("B1/make_october.py", 999), ("B1/small_dirty.csv", 999), ("B1/data/adyar.csv", 30), ("B1/pipeline.py", 999), ("B1/output.txt", 999),
                                    ("B1/cleaned_october.csv", 30), ("B1/complete_the_code.py", 999), ("B1/complete_output.txt", 99), ("B1/alt_pandas.py", 999), ("B1/alt_output.txt", 99)]),
        ("B2 - adversarial data", [("B2/complete_the_code.py", 999), ("B2/complete_output.txt", 99), ("B2/adversarial.py", 999), ("B2/output.txt", 999)]),
        ("B3 - loops vs libraries vs SQL", [("B3/loops_pandas_sql.py", 999), ("B3/output.txt", 999)]),
        ("B4 - final decision", [("B4/make_complaints.py", 999), ("B4/complaints.csv", 999), ("B4/ai_tools.py", 999), ("B4/evaluate.py", 999), ("B4/output.txt", 999),
                                 ("B4/index_test.py", 999), ("B4/index_output.txt", 999), ("B4/complete_the_code.py", 999), ("B4/complete_output.txt", 99)]),
        ("Part A experiments and chatbot", [("A1/csv_vs_sql.py", 999), ("A1/output.txt", 99), ("A2/missing_strategies.py", 999), ("A2/output.txt", 99), ("A3/daily_summary.py", 999),
                                            ("A3/output.txt", 99), ("A4/buggy_clean.py", 999), ("A4/debug_overhead.py", 999), ("A4/output.txt", 99), ("A5/chatbot.py", 999), ("A5/output.txt", 99)])]
    for heading, files in sections:
        story += [P(heading, H1)]
        for rel, n in files:
            story += [P(esc(rel), H2), code(excerpt(rel, n), 120)]
        story.append(PageBreak())
    build(path, story[:-1], "Python Programming - Assignment 5 (CO5) - Source code")


if __name__ == "__main__":
    make_figures.make_all()
    out = os.path.join(ROOT, "submission")
    os.makedirs(out, exist_ok=True)
    build_report(os.path.join(out, "File1_Report_PartA_PartB.pdf"))
    build_code(os.path.join(out, "File2_Source_Code_Data_Outputs.pdf"))
    for f in sorted(os.listdir(out)):
        print(f, round(os.path.getsize(os.path.join(out, f)) / 1024 / 1024, 2), "MB")
