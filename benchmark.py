"""Benchmark cho chương "Kiểm nghiệm tổng hợp".

    python benchmark.py                # mặc định n = 100 000, m = 2..64
    python benchmark.py --n 1000000    # văn bản dài hơn (chậm hơn)

Hai bộ dữ liệu:
  * DNA  : chuỗi ngẫu nhiên đều trên {A, C, G, T}           (sigma = 4)
  * Text : văn bản giả tiếng Anh theo tần suất chữ cái thật  (sigma = 27)
Mẫu lấy ngẫu nhiên từ chính văn bản (luôn có ít nhất một lần xuất hiện).

Hai thước đo:
  * inspections/n : số lần đọc ký tự văn bản chia cho n (độc lập ngôn ngữ, máy)
  * time_ms       : thời gian chạy trung bình (Python thuần — chỉ để so sánh tương đối)

Kết quả: results/benchmark.csv và các biểu đồ PNG trong results/.
"""
import argparse
import csv
import os
import random
import time

from algorithms import GROUPS, GROUP_OF, ALGORITHMS, CountingText, brute_force

ENGLISH_FREQ = {
    " ": 18.3, "e": 10.2, "t": 7.5, "a": 6.5, "o": 6.2, "n": 5.7, "i": 5.7, "s": 5.3, "r": 5.0,
    "h": 5.0, "l": 3.3, "d": 3.3, "u": 2.3, "c": 2.2, "m": 2.0, "f": 2.0, "w": 1.7, "g": 1.6,
    "y": 1.4, "p": 1.5, "b": 1.3, "v": 0.8, "k": 0.6, "x": 0.15, "j": 0.1, "q": 0.1, "z": 0.07,
}


def make_texts(n, seed):
    rng = random.Random(seed)
    dna = "".join(rng.choice("ACGT") for _ in range(n))
    letters, weights = zip(*ENGLISH_FREQ.items())
    eng = "".join(rng.choices(letters, weights=weights, k=n))
    return {"DNA": dna, "Text": eng}


def run(n, lengths, patterns_per_m, seed):
    rng = random.Random(seed + 1)
    rows = []
    for tname, y in make_texts(n, seed).items():
        for m in lengths:
            pats = []
            for _ in range(patterns_per_m):
                p = rng.randint(0, n - m)
                pats.append(y[p:p + m])
            expected = {x: brute_force(x, y) for x in pats[:1]}   # kiểm tra chéo 1 mẫu
            for name, fn in ALGORITHMS.items():
                insp = 0
                elapsed = 0.0
                for x in pats:
                    ct = CountingText(y)
                    out = fn(x, ct)
                    insp += ct.count
                    if x in expected:
                        assert sorted(out) == expected[x], (name, x)
                    t0 = time.perf_counter()
                    fn(x, y)
                    elapsed += time.perf_counter() - t0
                rows.append({
                    "text": tname, "m": m, "group": GROUP_OF[name], "algorithm": name,
                    "inspections_per_char": round(insp / (patterns_per_m * n), 4),
                    "time_ms": round(elapsed / patterns_per_m * 1000, 2),
                })
            print(f"  {tname} m={m:<3} xong")
    return rows


def save_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def plot(rows, metric, ylabel, path_prefix, lengths):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Không có matplotlib — bỏ qua vẽ biểu đồ.")
        return
    for tname in ("DNA", "Text"):
        fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
        for ax, (group, algs) in zip(axes.flat, GROUPS.items()):
            for name in algs:
                pts = [r for r in rows if r["text"] == tname and r["algorithm"] == name]
                ax.plot([r["m"] for r in pts], [r[metric] for r in pts], marker="o", label=name)
            ax.set_title(group)
            ax.set_xscale("log", base=2)
            ax.set_xticks(lengths)
            ax.set_xticklabels([str(v) for v in lengths])
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
        for ax in axes[1]:
            ax.set_xlabel("Độ dài mẫu m")
        for ax in axes[:, 0]:
            ax.set_ylabel(ylabel)
        fig.suptitle(f"{ylabel} — văn bản {tname}")
        fig.tight_layout()
        fig.savefig(f"{path_prefix}_{tname.lower()}.png", dpi=130)
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100_000)
    ap.add_argument("--patterns", type=int, default=10)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    lengths = [2, 4, 8, 16, 32, 64]

    os.makedirs("results", exist_ok=True)
    rows = run(args.n, lengths, args.patterns, args.seed)
    save_csv(rows, "results/benchmark.csv")
    plot(rows, "inspections_per_char", "Số lần đọc ký tự / n", "results/inspections", lengths)
    plot(rows, "time_ms", "Thời gian (ms)", "results/time", lengths)
    print("Đã ghi results/benchmark.csv và các biểu đồ results/*.png")


if __name__ == "__main__":
    main()
