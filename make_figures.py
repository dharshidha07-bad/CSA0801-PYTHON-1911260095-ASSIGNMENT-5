"""Diagrams and graphs for the report (numbers come from the results.json files written by the programs)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)


def load(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)


def box(ax, x, y, w, h, text, fc="#e8f1fb", ec="#2c5d8f", fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q, style="-|>", color="#444"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=10, color=color, lw=1.1))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=150)
    plt.close(fig)


def make_all():
    # ER diagram
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis("off")
    box(ax, 0.2, 0.5, 4.3, 4.0, "stations\n\nstation_id  INTEGER  PRIMARY KEY\nname  TEXT  NOT NULL  UNIQUE\nreports_fahrenheit  INTEGER  (0/1)", fc="#fff3cd", ec="#a07800", fs=8)
    box(ax, 6.2, 0.2, 5.6, 4.6, "readings\n\nstation_id  INTEGER  NOT NULL  (FK -> stations)\nday  TEXT  'YYYY-MM-DD'\nhour  INTEGER  0..23\npm25  REAL\npm10  REAL\nno2  REAL\ntemp_c  REAL\npm25_imputed  INTEGER  (0/1)\nPRIMARY KEY (station_id, day, hour)", fc="#e8f1fb", fs=8)
    arrow(ax, (4.5, 2.5), (6.2, 2.5), style="<|-|>")
    ax.text(5.35, 2.8, "1 : many", ha="center", fontsize=8)
    save(fig, "er.png")
    # workflow
    fig, ax = plt.subplots(figsize=(10, 2.4))
    ax.set_xlim(0, 20); ax.set_ylim(0, 4); ax.axis("off")
    steps = ["Acquire\nCSV files", "Inspect\nheader, rows", "Clean\nrules A2.1", "Normalise\nmin-max / z", "Store\nSQLite", "Query\nSQL", "Visualise\ncharts", "Profile\ncProfile", "Interpret"]
    for i, s in enumerate(steps):
        box(ax, 0.1 + i * 2.2, 1.0, 1.9, 2.0, s, fs=7.5, fc="#e3f6e3" if i in (2, 4) else "#e8f1fb")
        if i:
            arrow(ax, (0.1 + i * 2.2 - 0.3, 2.0), (0.1 + i * 2.2, 2.0))
    save(fig, "workflow.png")
    # B3 timing
    r = load("B3/results.json")["timing"]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    n = [x["rows"] for x in r]
    for key, lab in (("loops", "loops + statistics.mean"), ("running", "loops, running sum"), ("pandas", "pandas groupby")):
        ax.plot(n, [x[key] for x in r], "o-", label=lab)
    ax.plot(n, [x["sql_load"] + x["sql_query"] for x in r], "o-", label="SQL (load + query)")
    ax.plot(n, [x["sql_query"] for x in r], "s--", label="SQL query only")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("readings (1, 12, 120 stations x 8,760)"); ax.set_ylabel("seconds")
    ax.set_title("B3: daily mean per station", fontsize=10); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=7)
    save(fig, "b3_timing.png")
    # B1 alternative
    r = load("B1/alt_results.json")
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.2))
    n = [x["rows"] for x in r]
    axes[0].plot(n, [x["loops"] for x in r], "o-", label="csv + loops"); axes[0].plot(n, [x["pandas"] for x in r], "o-", label="pandas")
    axes[0].set_xscale("log"); axes[0].set_yscale("log"); axes[0].set_xlabel("rows"); axes[0].set_ylabel("seconds"); axes[0].set_title("time", fontsize=10)
    axes[0].grid(True, which="both", alpha=0.3); axes[0].legend(fontsize=8)
    axes[1].plot(n, [x["mem_loops"] / 1e6 for x in r], "o-", label="csv + loops"); axes[1].plot(n, [x["mem_pandas"] / 1e6 for x in r], "o-", label="pandas")
    axes[1].set_xscale("log"); axes[1].set_yscale("log"); axes[1].set_xlabel("rows"); axes[1].set_ylabel("peak MB (tracemalloc)"); axes[1].set_title("memory", fontsize=10)
    axes[1].grid(True, which="both", alpha=0.3); axes[1].legend(fontsize=8)
    save(fig, "b1_alt.png")
    # B4 index
    r = load("B4/index_results.json")
    b, a = r["before: no index"], r["after: index on (station, day)"]
    qs = list(b)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    xs = range(len(qs))
    ax.bar([x - 0.2 for x in xs], [b[q] * 1000 for q in qs], 0.4, label="no index")
    ax.bar([x + 0.2 for x in xs], [a[q] * 1000 for q in qs], 0.4, label="index (station, day)")
    ax.set_yscale("log"); ax.set_xticks(list(xs)); ax.set_xticklabels([q.split(" ")[0] for q in qs]); ax.set_ylabel("milliseconds (log scale)")
    ax.set_title("B4.2: effect of the index on 1,051,200 rows", fontsize=10); ax.legend(fontsize=8); ax.grid(True, axis="y", alpha=0.3)
    save(fig, "b4_index.png")
    # B4 agreement
    r = load("B4/results.json")
    labs = ["v0\nassignment\nlexicon", "v1\nlarger\nlexicon", "v2 + better\nnegation", "Naive Bayes\n(leave-one-out)"]
    vals = list(r["agree"].values()) + [r["nb_loo"]]
    fig, ax = plt.subplots(figsize=(6, 3.3))
    ax.bar(labs, [v / 60 * 100 for v in vals], color=["#2c5d8f", "#6a9ac4", "#6a9ac4", "#e08a1e"])
    for i, v in enumerate(vals):
        ax.text(i, v / 60 * 100 + 1, f"{v}/60", ha="center", fontsize=8)
    ax.set_ylim(0, 105); ax.set_ylabel("agreement with my reading (%)"); ax.set_title("B4.1: sentiment on 60 complaints", fontsize=10)
    save(fig, "b4_agreement.png")


if __name__ == "__main__":
    make_all()
    print("figures written to", FIG)
