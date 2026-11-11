"""Demo dùng cho mục "Kiểm nghiệm" và "Ví dụ chạy tay" của từng thuật toán.

    python demo.py                                  # bảng tổng hợp cho ví dụ của bài giảng
    python demo.py -x GCAGAGAG -y GCATCGCAGAGAGTATACAGTACG
    python demo.py --trace -a Horspool              # vết đọc văn bản để đối chiếu khi chạy tay
    python demo.py --trace -a KMP -a Boyer-Moore    # nhiều thuật toán

Chế độ --trace in văn bản kèm chỉ số, rồi mỗi dòng là một dãy lần đọc liền nhau
(cùng chiều, vị trí cách nhau 1). Thường mỗi dòng ứng với MỘT lần thử (một vị trí cửa sổ):
ký tự được đọc hiện ra, chỗ không đọc là dấu chấm, số bên phải là thứ tự các lần đọc.
"""
import argparse

from algorithms import ALGORITHMS, ALL_ALGORITHMS, GROUPS, CountingText, brute_force
from algorithms.core import TracingText
from algorithms._tables import mp_next, bm_bc, bm_gs, qs_bc
from algorithms.left_to_right import pre_kmp


def show_tables(x):
    m = len(x)
    print(f"Mẫu x = {x!r}  (m = {m})")
    print("  i        :", " ".join(f"{i:>3}" for i in range(m + 1)))
    print("  x[i]     :", " ".join(f"{c:>3}" for c in x))
    print("  mpNext   :", " ".join(f"{v:>3}" for v in mp_next(x)))
    print("  kmpNext  :", " ".join(f"{v:>3}" for v in pre_kmp(x)), "  (theo bài giảng)")
    print("  bmGs     :", " ".join(f"{v:>3}" for v in bm_gs(x)))
    bc, d = bm_bc(x)
    print("  bmBc     :", ", ".join(f"{c}={v}" for c, v in sorted(bc.items())), f"(khác: {d})")
    qs, d = qs_bc(x)
    print("  qsBc     :", ", ".join(f"{c}={v}" for c, v in sorted(qs.items())), f"(khác: {d})")
    print()


def split_runs(log):
    """Tách dãy vị trí đọc thành các đoạn liền nhau cùng chiều."""
    runs, cur, step = [], [], 0
    for k, pos in enumerate(log):
        if cur:
            d = pos - cur[-1][1]
            if abs(d) == 1 and (step == 0 or d == step):
                step = d
                cur.append((k + 1, pos))
                continue
            runs.append(cur)
        cur, step = [(k + 1, pos)], 0
    if cur:
        runs.append(cur)
    return runs


def show_trace(name, fn, x, y):
    t = TracingText(y)
    pos = sorted(fn(x, t))
    n = len(y)
    print(f"=== {name} — tìm thấy tại {pos}, {len(t.log)} lần đọc văn bản")
    print("      " + "".join(str(i // 10) if i >= 10 else " " for i in range(n)))
    print("      " + "".join(str(i % 10) for i in range(n)))
    print("  y = " + y)
    for r, run in enumerate(split_runs(t.log), 1):
        line = ["."] * n
        for _, p in run:
            line[p] = y[p]
        direction = "→" if len(run) > 1 and run[1][1] > run[0][1] else ("←" if len(run) > 1 else " ")
        order = ",".join(str(k) for k, _ in run)
        print(f"{r:>3}{direction} " + "".join(line) + f"   đọc #{order}")
    print()


ALIASES = {
    "kmp": "Knuth-Morris-Pratt", "mp": "Morris-Pratt", "bm": "Boyer-Moore", "tbm": "Turbo BM",
    "bom": "Backward Oracle Matching", "fdm": "Forward Dawg Matching", "rf": "Reverse Factor",
    "trf": "Turbo Reverse Factor", "ag": "Apostolico-Giancarlo", "ac": "Apostolico-Crochemore",
    "gg": "Galil-Giancarlo", "gs": "Galil-Seiferas", "qs": "Quick Search", "dfa": "Automat hữu hạn",
    "automat": "Automat hữu hạn", "kr": "Karp-Rabin", "zt": "Zhu-Takaoka", "br": "Berry-Ravindran",
}


def resolve(name):
    """Nhận tên đầy đủ, viết tắt (KMP, BM, BOM...) hoặc không phân biệt hoa/thường."""
    if name in ALL_ALGORITHMS:
        return name
    key = name.lower()
    if key in ALIASES:
        return ALIASES[key]
    for full in ALL_ALGORITHMS:
        if full.lower() == key:
            return full
    raise SystemExit(f"Không có thuật toán {name!r}. Tên hợp lệ: {', '.join(ALL_ALGORITHMS)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-x", "--pattern", default="ABABCABAB")
    ap.add_argument("-y", "--text", default="ABABDABACDABABCABAB")
    ap.add_argument("-a", "--algo", action="append", help="tên thuật toán (lặp lại được)")
    ap.add_argument("--trace", action="store_true", help="in vết đọc văn bản để đối chiếu chạy tay")
    args = ap.parse_args()
    x, y = args.pattern, args.text

    names = [resolve(a) for a in args.algo] if args.algo else list(ALGORITHMS)

    show_tables(x)
    print(f"Văn bản y = {y!r}  (n = {len(y)})")
    print(f"Kết quả chuẩn (vét cạn): {brute_force(x, y)}\n")

    if args.trace:
        for name in names:
            show_trace(name, ALL_ALGORITHMS[name], x, y)
        return

    print(f"{'Nhóm':<17}{'Thuật toán':<27}{'Vị trí':<16}{'Đọc ký tự':>10}{'/ n':>7}")
    print("-" * 77)
    for group, algs in GROUPS.items():
        for name, fn in algs.items():
            if name not in names:
                continue
            t = CountingText(y)
            pos = sorted(fn(x, t))
            ratio = t.count / len(y) if y else 0
            print(f"{group:<17}{name:<27}{str(pos):<16}{t.count:>10}{ratio:>7.2f}")


if __name__ == "__main__":
    main()
