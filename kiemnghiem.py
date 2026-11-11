"""Kiểm nghiệm thuật toán: sinh BẢNG CHẠY TỪNG BƯỚC (như slide bài giảng) cho 22 thuật toán.

    python kiemnghiem.py                         # cả 22 thuật toán, ví dụ của bài giảng
    python kiemnghiem.py -a KMP -a Horspool      # một vài thuật toán
    python kiemnghiem.py -x GCAGAGAG -y GCATCGCAGAGAGTATACAGTACG -a BM   # ví dụ khác

Ví dụ mặc định lấy từ bài giảng: X = "ABABCABAB" (m = 9), Y = "ABABDABACDABABCABAB" (n = 19).

Mỗi hàm trace_* chạy lại đúng logic của cài đặt trong algorithms/ nhưng ghi lại từng bước.
Hàm verify() đối chiếu: vị trí tìm thấy và SỐ LẦN ĐỌC KÝ TỰ VĂN BẢN của bản trace phải trùng
với bản cài đặt thật — bảo đảm bảng in ra đúng là những gì code làm.

Ký hiệu trong bảng: "x[i]=y[k]" là so khớp, "x[i]≠y[k] (a≠b)" là sai khớp,
"x[0..8]=y[10..18]" là một đoạn so khớp liên tiếp.
"""
import argparse
from collections import Counter

from algorithms import ALGORITHMS, CountingText, brute_force
from algorithms._tables import mp_next, kmp_next, bm_bc, bm_gs, qs_bc, suffixes
from algorithms.left_to_right import build_dfa
from algorithms.right_to_left import build_factor_oracle
from algorithms.specific_order import _adapted_gs

X_DEFAULT = "ABABCABAB"
Y_DEFAULT = "ABABDABACDABABCABAB"


# ------------------------------------------------------------------ tiện ích
class Table:
    def __init__(self, title, headers, rows, note=""):
        self.title, self.headers, self.rows, self.note = title, headers, rows, note

    def markdown(self):
        out = []
        if self.title:
            out.append(f"**{self.title}**\n")
        out.append("| " + " | ".join(str(h) for h in self.headers) + " |")
        out.append("| " + " | ".join("---" for _ in self.headers) + " |")
        for r in self.rows:
            out.append("| " + " | ".join(str(c) if str(c) != "" else " " for c in r) + " |")
        if self.note:
            out.append("\n" + self.note)
        return "\n".join(out)

    def text(self):
        widths = [max(len(str(h)), *(len(str(r[i])) for r in self.rows)) if self.rows else len(str(h))
                  for i, h in enumerate(self.headers)]
        line = lambda cells: "  ".join(str(c).ljust(w) for c, w in zip(cells, widths))
        out = [f"[{self.title}]"] if self.title else []
        out.append(line(self.headers))
        out.append("  ".join("-" * w for w in widths))
        out += [line(r) for r in self.rows]
        if self.note:
            out.append(self.note)
        return "\n".join(out)


class Cmp:
    """Ghi lại các phép so sánh x[i] với y[k] trong một lần thử, in gọn theo đoạn."""

    def __init__(self, x, y):
        self.x, self.y, self.log = x, y, []

    def eq(self, i, k):
        a, b = self.x[i], self.y[k]
        ok = a == b
        self.log.append((i, k, ok, a, b))
        return ok

    def reset(self):
        self.log = []

    def fmt(self):
        if not self.log:
            return "—"
        parts, run = [], []

        def flush():
            if not run:
                return
            if len(run) == 1:
                i, k = run[0][0], run[0][1]
                parts.append(f"x[{i}]=y[{k}]")
            else:
                i0, k0, i1, k1 = run[0][0], run[0][1], run[-1][0], run[-1][1]
                if i0 <= i1:
                    parts.append(f"x[{i0}..{i1}]=y[{k0}..{k1}]")
                else:
                    parts.append(f"x[{i0}..{i1}]=y[{k0}..{k1}] (←)")
            run.clear()

        for rec in self.log:
            i, k, ok, a, b = rec
            if ok:
                if run and abs(i - run[-1][0]) == 1 and i - run[-1][0] == k - run[-1][1] and \
                        (len(run) < 2 or i - run[-1][0] == run[-1][0] - run[-2][0]):
                    run.append(rec)
                else:
                    flush()
                    run.append(rec)
            else:
                flush()
                parts.append(f"x[{i}]≠y[{k}] ({a}≠{b})")
        flush()
        return ", ".join(parts)


def bits(v, m):
    return format(v, f"0{m}b")


def chtab(title, d, default, label="c"):
    keys = sorted(d)
    return Table(title, [label] + keys + ["khác"], [["giá trị"] + [d[k] for k in keys] + [default]])


# ------------------------------------------------------------------ NHÓM 1: trái → phải
def trace_not_so_naive(x, y):
    m, n = len(x), len(y)
    k, ell = (2, 1) if x[0] == x[1] else (1, 2)
    pre = [Table("Tiền xử lý", ["x[0] = x[1]?", "k (sai tại x[1])", "ℓ (còn lại)"],
                 [["có" if x[0] == x[1] else "không", k, ell]])]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        if not c.eq(1, j + 1):
            s, kq = k, "sai tại x[1]"
        else:
            i = 2
            while i < m and c.eq(i, j + i):
                i += 1
            if i == m and c.eq(0, j):
                res.append(j)
                kq = "**khớp**"
            else:
                kq = f"sai tại x[{i if i < m else 0}]"
            s = ell
        rows.append([j, c.fmt(), kq, s])
        j += s
    return pre, Table("Các lần thử", ["j", "So sánh (x[1], x[2..m−1], rồi x[0])", "Kết quả", "Dịch"], rows), res


def trace_karp_rabin(x, y):
    m, n = len(x), len(y)
    mod, h = 2 ** 32, 2 ** (m - 1)
    hx = hy = 0
    for i in range(m):
        hx = (hx * 2 + ord(x[i])) % mod
        hy = (hy * 2 + ord(y[i])) % mod
    pre = [Table("Tiền xử lý", ["hash(x)", "2^(m−1)"], [[hx, h]],
                 "hash(w) = Σ ord(w[i])·2^(m−1−i); băm lại: hash' = (hash − ord(y[j])·2^(m−1))·2 + ord(y[j+m]).")]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while True:
        c.reset()
        if hx == hy:
            i = 0
            while i < m and c.eq(i, j + i):
                i += 1
            if i == m:
                res.append(j)
                kq = "**trùng băm, khớp**"
            else:
                kq = "trùng băm nhưng sai (xung đột)"
        else:
            kq = "khác"
        rows.append([j, hy, kq, c.fmt() if c.log else ""])
        if j >= n - m:
            break
        hy = ((hy - ord(y[j]) * h) * 2 + ord(y[j + m])) % mod
        j += 1
    return pre, Table("Các cửa sổ", ["j", "hash(y[j..j+m−1])", "So với hash(x)", "Kiểm tra từng ký tự"], rows), res


def trace_shift_or(x, y):
    m, n = len(x), len(y)
    full = (1 << m) - 1
    S = {}
    for i, ch in enumerate(x):
        S[ch] = S.get(ch, full) & ~(1 << i) & full
    pre = [Table("Mặt nạ S[c] (bit m−1 bên trái ↔ x[m−1], bit 0 bên phải ↔ x[0])", ["c", "S[c]"],
                 [[ch, bits(v, m)] for ch, v in sorted(S.items())] + [["khác", bits(full, m)]])]
    hi = 1 << (m - 1)
    D, rows, res = full, [], []
    for j in range(n):
        ch = y[j]
        D = ((D << 1) | S.get(ch, full)) & full
        hit = not D & hi
        if hit:
            res.append(j - m + 1)
        rows.append([j, ch, bits(S.get(ch, full), m), bits(D, m), f"**có, tại {j - m + 1}**" if hit else ""])
    return pre, Table("Từng ký tự (D ← (D ≪ 1) | S[y[j]], khởi đầu D = 1…1)",
                      ["j", "y[j]", "S[y[j]]", "D", "bit m−1 = 0?"], rows), res


def trace_morris_pratt(x, y):
    m, n = len(x), len(y)
    nxt = mp_next(x)
    pre = [Table("Bảng mpNext", ["i"] + list(range(m + 1)), [["x[i]"] + list(x) + [""], ["mpNext[i]"] + nxt])]
    rows, res = [], []
    i = 0
    for j in range(n):
        while i > -1:
            a = y[j]
            if x[i] == a:
                break
            rows.append([j, i, f"x[{i}]≠y[{j}] ({x[i]}≠{a})", f"i ← mpNext[{i}] = {nxt[i]}"])
            i = nxt[i]
        if i > -1:
            rows.append([j, i, f"x[{i}]=y[{j}]", f"i ← {i + 1}"])
        else:
            rows.append([j, i, "i = −1 (không so)", "i ← 0"])
        i += 1
        if i >= m:
            res.append(j - i + 1)
            rows.append([j, i, f"**khớp tại {j - i + 1}**", f"i ← mpNext[{i}] = {nxt[i]}"])
            i = nxt[i]
    return pre, Table("Từng phép so sánh (j: văn bản, i: mẫu)", ["j", "i", "So sánh", "Cập nhật"], rows), res


def trace_kmp(x, y):
    """Đúng mã giả bài giảng: i trên văn bản, j trên mẫu."""
    m, n = len(x), len(y)
    nxt = [0] * m
    prow = [["", "", "len = 0", "kmpNext[0] = 0"]]
    i, ln = 1, 0
    while i < m:
        if x[i] == x[ln]:
            prow.append([f"i={i}", f"('{x[i]}'=='{x[ln]}'): Yes", f"len = {ln + 1}", f"kmpNext[{i}] = {ln + 1}"])
            ln += 1
            nxt[i] = ln
            i += 1
        elif ln != 0:
            prow.append([f"i={i}", f"('{x[i]}'=='{x[ln]}'): No", f"len = kmpNext[{ln - 1}] = {nxt[ln - 1]}",
                         f"kmpNext[{i}] chưa xác định"])
            ln = nxt[ln - 1]
        else:
            prow.append([f"i={i}", f"('{x[i]}'=='{x[ln]}'): No", "len = 0", f"kmpNext[{i}] = 0"])
            nxt[i] = 0
            i += 1
    pre = [Table("Kiểm nghiệm PreKmp(X, m, kmpNext)", ["i", "(X[i]==X[len])?", "len", "kmpNext[i]"], prow,
                 f"Kết luận: kmpNext[] = {{{', '.join(map(str, nxt))}}}.")]
    rows, res = [], []
    i = j = 0
    while i < n:
        a = y[i]
        eq = x[j] == a
        if eq:
            row = [f"(X[{j}]==Y[{i}]): Yes", "No", "", ""]
            rows.append(row)
            i += 1
            j += 1
            row[2] = f"i={i}, j={j}"
        if j == m:
            res.append(i - j)
            rows[-1][1] = "Yes"
            rows[-1][3] = f"**tìm thấy tại {i - j}**; j ← kmpNext[{j - 1}] = {nxt[j - 1]}"
            j = nxt[j - 1]
            rows[-1][2] = f"i={i}, j={j}"
            continue
        if i < n:
            b = y[i]
            if x[j] != b:
                row = [f"(X[{j}]==Y[{i}]): No", "No"]
                if j != 0:
                    note = f"j ← kmpNext[{j - 1}] = {nxt[j - 1]}"
                    j = nxt[j - 1]
                else:
                    note = "j = 0 → i ← i + 1"
                    i += 1
                rows.append(row + [f"i={i}, j={j}", note])
    return pre, Table("Kiểm nghiệm Knuth-Morris-Pratt(X, m, Y, n)",
                      ["(X[j]==Y[i])?", f"(j=={m})?", "i, j sau bước", "Ghi chú"], rows), res


def trace_automaton(x, y):
    m, n = len(x), len(y)
    delta = build_dfa(x)
    alpha = sorted(set(x))
    pre = [Table("Bảng chuyển trạng thái δ (ký tự khác → 0)", ["q"] + alpha,
                 [[q] + [delta[q].get(c, 0) for c in alpha] for q in range(m + 1)])]
    rows, res, q = [], [], 0
    for j in range(n):
        c = y[j]
        q2 = delta[q].get(c, 0)
        hit = q2 == m
        if hit:
            res.append(j - m + 1)
        rows.append([j, c, f"δ({q}, {c}) = {q2}", f"**trạng thái {m}: xuất hiện tại {j - m + 1}**" if hit else ""])
        q = q2
    return pre, Table("Đọc từng ký tự", ["j", "y[j]", "Chuyển", "Ghi chú"], rows), res


# ------------------------------------------------------------------ NHÓM 2: phải → trái
def _pre_bm(x):
    m = len(x)
    bc, d = bm_bc(x)
    return [Table("Bảng bmGs (good-suffix) và suff", ["i"] + list(range(m)),
                  [["x[i]"] + list(x), ["suff[i]"] + suffixes(x), ["bmGs[i]"] + bm_gs(x)]),
            chtab("Bảng bmBc (bad-character)", bc, d)]


def trace_turbo_bm(x, y):
    m, n = len(x), len(y)
    gs = bm_gs(x)
    bc, bcd = bm_bc(x)
    rows, res, c = [], [], Cmp(x, y)
    j = u = 0
    shift = m
    after_match = False
    while j <= n - m:
        c.reset()
        jumped = ""
        i = m - 1
        while i >= 0 and c.eq(i, i + j):
            i -= 1
            if u != 0 and i == m - 1 - shift:
                jumped = f"nhảy qua y[{j + i - u + 1}..{j + i}]"
                i -= u
        if i < 0:
            res.append(j)
            shift = gs[0]
            u = m - shift
            after_match = True
            rows.append([j, c.fmt(), jumped, "**khớp**", "—", "—", f"bmGs[0] = {gs[0]}", shift, u])
        else:
            v = m - 1 - i
            ts = 0 if after_match else u - v
            a = y[i + j]
            bs = bc.get(a, bcd) - m + 1 + i
            shift = max(ts, bs, gs[i])
            note = ""
            if shift == gs[i]:
                u = min(m - shift, v)
            else:
                if ts < bs and not after_match:
                    if u + 1 > shift:
                        note = f" (≥ u+1 = {u + 1})"
                    shift = max(shift, u + 1)
                u = 0
            after_match = False
            rows.append([j, c.fmt(), jumped, f"sai tại i = {i}", ts, bs, gs[i], f"{shift}{note}", u])
        j += shift
    return _pre_bm(x), Table("Các lần thử (so từ phải sang trái)",
                             ["j", "So sánh", "Turbo (nhảy)", "Kết quả", "turboShift", "bcShift", "bmGs[i]",
                              "Dịch", "u mới"], rows), res


def trace_quick_search(x, y):
    m, n = len(x), len(y)
    qs, d = qs_bc(x)
    pre = [chtab("Bảng qsBc (dịch theo ký tự ngay sau cửa sổ)", qs, d)]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        i = 0
        while i < m and c.eq(i, j + i):
            i += 1
        kq = "**khớp**" if i >= m else f"sai tại x[{i}]"
        if i >= m:
            res.append(j)
        if j + m >= n:
            rows.append([j, c.fmt(), kq, "hết văn bản", "dừng"])
            break
        a = y[j + m]
        s = qs.get(a, d)
        rows.append([j, c.fmt(), kq, f"y[{j + m}] = {a}", s])
        j += s
    return pre, Table("Các lần thử", ["j", "So sánh (trái → phải)", "Kết quả", "Ký tự sau cửa sổ", "Dịch qsBc"],
                      rows), res


def trace_zhu_takaoka(x, y):
    m, n = len(x), len(y)
    gs = bm_gs(x)
    pair = {}
    for i in range(1, m - 1):
        pair[(x[i - 1], x[i])] = m - 1 - i

    def zt(a, b):
        v = pair.get((a, b))
        return v if v is not None else (m - 1 if b == x[0] else m)

    pre = _pre_bm(x)[:1] + [Table("Bảng ztBc theo cặp (a, b)", ["cặp", "ztBc"],
                                  [[a + b, v] for (a, b), v in sorted(pair.items())] +
                                  [[f"(*, {x[0]}) khác", m - 1], ["còn lại", m]])]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        i = m - 1
        while i >= 0 and c.eq(i, i + j):
            i -= 1
        if i < 0:
            res.append(j)
            rows.append([j, c.fmt(), "**khớp**", "—", "—", f"bmGs[0] = {gs[0]}"])
            j += gs[0]
        else:
            a, b = y[j + m - 2], y[j + m - 1]
            z = zt(a, b)
            s = max(gs[i], z)
            rows.append([j, c.fmt(), f"sai tại i = {i}", f"{a}{b} → {z}", gs[i], s])
            j += s
    return pre, Table("Các lần thử", ["j", "So sánh (←)", "Kết quả", "(y[j+m−2], y[j+m−1]) → ztBc", "bmGs[i]",
                                      "Dịch"], rows), res


def trace_berry_ravindran(x, y):
    m, n = len(x), len(y)
    pair = {}
    for i in range(m - 1):
        pair[(x[i], x[i + 1])] = m - i
    last, first = x[m - 1], x[0]

    def br(a, b):
        if a == last:
            return 1
        v = pair.get((a, b))
        if v is not None:
            return v
        return m + 1 if b == first else m + 2

    pre = [Table("Bảng brBc(a, b), a = y[j+m], b = y[j+m+1]", ["Trường hợp", "brBc"],
                 [[f"a = x[m−1] = {last}", 1]] +
                 [[f"cặp {a}{b} có trong x", v] for (a, b), v in sorted(pair.items()) if a != last] +
                 [[f"b = x[0] = {first}", m + 1], ["còn lại", m + 2]])]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        i = m - 1
        while i >= 0 and c.eq(i, j + i):
            i -= 1
        kq = "**khớp**" if i < 0 else f"sai tại i = {i}"
        if i < 0:
            res.append(j)
        a = y[j + m] if j + m < n else None
        b = y[j + m + 1] if j + m + 1 < n else None
        s = br(a, b)
        rows.append([j, c.fmt(), kq, f"({a or '∅'}, {b or '∅'})", s])
        j += s
    return pre, Table("Các lần thử", ["j", "So sánh (←)", "Kết quả", "(y[j+m], y[j+m+1])", "Dịch"], rows), res


def trace_bndm(x, y):
    m, n = len(x), len(y)
    full = (1 << m) - 1
    B = {}
    s = 1
    for i in range(m):
        ch = x[m - i - 1]
        B[ch] = B.get(ch, 0) | s
        s <<= 1
    pre = [Table("Mặt nạ B[c]: bit i bật khi x[m−1−i] = c (bit m−1 bên trái)", ["c", "B[c]"],
                 [[ch, bits(v, m)] for ch, v in sorted(B.items())] + [["khác", bits(0, m)]])]
    hi = 1 << (m - 1)
    rows, res = [], []
    j = 0
    while j <= n - m:
        i, last, d = m - 1, m, full
        steps = []
        while i >= 0 and d != 0:
            ch = y[j + i]
            d &= B.get(ch, 0)
            pos = i
            i -= 1
            mark = ""
            if d & hi:
                if i >= 0:
                    last = i + 1
                    mark = f" tiền tố → last={last}"
                else:
                    res.append(j)
                    mark = " **khớp**"
            steps.append(f"y[{j + pos}]={ch}: D={bits(d, m)}{mark}")
            d = (d << 1) & full
        rows.append([j, "; ".join(steps), last])
        j += last
    return pre, Table("Các lần thử (đọc từ phải sang trái; D ← D & B[c], rồi D ≪ 1)",
                      ["j", "Đọc và D sau phép AND", "Dịch (last)"], rows), res


def trace_bom(x, y):
    m, n = len(x), len(y)
    trans = build_factor_oracle(x[::-1])
    pre = [Table(f"Factor oracle của mẫu đảo ngược {x[::-1]}", ["trạng thái", "chuyển"],
                 [[q, ", ".join(f"{a}→{t}" for a, t in sorted(tr.items())) or "—"] for q, tr in enumerate(trans)])]
    rows, res = [], []
    j = 0
    while j <= n - m:
        q, i, steps = 0, m - 1, []
        while i >= 0:
            ch = y[j + i]
            nq = trans[q].get(ch)
            if nq is None:
                steps.append(f"y[{j + i}]={ch}: không có cạnh")
                break
            steps.append(f"y[{j + i}]={ch}: {q}→{nq}")
            q = nq
            i -= 1
        if i < 0:
            res.append(j)
            rows.append([j, "; ".join(steps), "**khớp**", 1])
            j += 1
        else:
            rows.append([j, "; ".join(steps), f"dừng tại i = {i}", i + 1])
            j += i + 1
    return pre, Table("Các lần thử (đọc từ phải sang trái trên oracle)", ["j", "Đọc", "Kết quả", "Dịch"], rows), res


# ------------------------------------------------------------------ NHÓM 3: vị trí xác định
def _ordered(x, y, order, title_order):
    m, n = len(x), len(y)
    qs, d = qs_bc(x)
    pat = [(loc, x[loc]) for loc in order] + [(m, None)]
    gs = _adapted_gs(x, pat)
    pre_rows = [["thứ tự quét"] + [f"x[{loc}]={x[loc]}" for loc in order],
                ["gs thích nghi (sau k vị trí khớp)"] + gs[:m]]
    pre = [Table(title_order, ["k"] + list(range(m)), pre_rows, f"gs[{m}] (khớp hết) = {gs[m]}"),
           chtab("Bảng qsBc", qs, d)]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        i = 0
        while i < m and c.eq(pat[i][0], j + pat[i][0]):
            i += 1
        if i >= m:
            res.append(j)
        a = y[j + m] if j + m < n else None
        nx = qs.get(a, d) if a is not None else d
        s = max(gs[i], nx)
        rows.append([j, c.fmt(), "**khớp**" if i >= m else f"khớp {i} vị trí", gs[i],
                     f"{a} → {nx}" if a is not None else f"∅ → {d}", s])
        j += s
    return pre, Table("Các lần thử (so theo thứ tự quét)",
                      ["j", "So sánh", "Kết quả", "gs[k]", "qsBc[y[j+m]]", "Dịch"], rows), res


def trace_optimal_mismatch(x, y):
    m = len(x)
    freq = Counter(y.raw if isinstance(y, CountingText) else y)
    order = sorted(range(m), key=lambda loc: (freq.get(x[loc], 0), -loc))
    fq = ", ".join(f"{k} = {v}" for k, v in sorted(freq.items()))
    pre, tab, res = _ordered(x, y, order, f"Thứ tự quét theo tần suất tăng dần trong y ({fq})")
    return pre, tab, res


def trace_maximal_shift(x, y):
    m = len(x)
    ms = []
    for i in range(m):
        j = i - 1
        while j >= 0 and x[i] != x[j]:
            j -= 1
        ms.append(i - j)
    order = sorted(range(m), key=lambda loc: (-ms[loc], -loc))
    pre, tab, res = _ordered(x, y, order, "Thứ tự quét theo minShift giảm dần")
    pre.insert(0, Table("Bảng minShift", ["i"] + list(range(m)), [["x[i]"] + list(x), ["minShift[i]"] + ms]))
    return pre, tab, res


def trace_skip_search(x, y):
    m, n = len(x), len(y)
    z = {}
    for i in range(m):
        z.setdefault(x[i], []).insert(0, i)
    pre = [Table("Xô z[c] (vị trí của c trong x, giảm dần)", ["c", "z[c]"],
                 [[ch, "{" + ", ".join(map(str, v)) + "}"] for ch, v in sorted(z.items())] + [["khác", "∅"]])]
    rows, res, c = [], [], Cmp(x, y)
    for j in range(m - 1, n, m):
        ch = y[j]
        tries = []
        for k in z.get(ch, ()):
            s = j - k
            if s < 0 or s + m > n:
                tries.append(f"j={s}: ngoài văn bản")
                continue
            c.reset()
            i = 0
            while i < m and c.eq(i, s + i):
                i += 1
            if i == m:
                res.append(s)
                tries.append(f"j={s}: {c.fmt()} **khớp**")
            else:
                tries.append(f"j={s}: {c.fmt()}")
        rows.append([j, ch, "{" + ", ".join(map(str, z.get(ch, []))) + "}" if ch in z else "∅",
                     "; ".join(tries) or "—"])
    return pre, Table("Đọc y tại các vị trí m−1, 2m−1, …", ["vị trí", "y[vị trí]", "xô", "Các cửa sổ thử"],
                      rows), res


def trace_kmp_skip_search(x, y):
    m, n = len(x), len(y)
    mp = mp_next(x)
    kmpn = kmp_next(x)
    z = {x[0]: 0}
    lst = [-1] * m
    for i in range(1, m):
        lst[i] = z.get(x[i], -1)
        z[x[i]] = i
    per = m - kmpn[m]
    pre = [Table("Bảng z (vị trí cuối của c trong x) và list (vị trí trước đó cùng ký tự)",
                 ["i"] + list(range(m)), [["x[i]"] + list(x), ["list[i]"] + lst, ["mpNext[i]"] + mp[:m],
                                          ["kmpNext[i]"] + kmpn[:m]],
                 "z: " + ", ".join(f"z[{k}] = {v}" for k, v in sorted(z.items())) + f"; chu kỳ per = {per}")]
    rows, res, c = [], [], Cmp(x, y)
    log_bucket = []

    def next_bucket(j):
        while True:
            j += m
            if j >= n:
                return j, -1
            ch = y[j]
            i = z.get(ch, -1)
            log_bucket.append(f"đọc y[{j}]={ch}" + (f" → z = {i}" if i >= 0 else " → không có"))
            if i >= 0:
                return j, i

    def attempt(start, wall):
        k = wall - start
        c.reset()
        while k < m and c.eq(k, k + start):
            k += 1
        return k

    wall = 0
    j, i = next_bucket(-1)
    if j < n:
        start = j - i
        while start <= n - m:
            if start > wall:
                wall = start
            wall0 = wall
            k = attempt(start, wall)
            wall = start + k
            buckets = "; ".join(log_bucket)
            log_bucket.clear()
            if k == m:
                res.append(start)
                kq = "**khớp**"
                i -= per
            else:
                kq = f"khớp {k} ký tự"
                i = lst[i]
            rows.append([start, wall0, c.fmt(), kq, buckets])
            if i < 0:
                j, i = next_bucket(j)
                if j >= n:
                    break
            kmp_start = start + k - kmpn[k]
            k = kmpn[k]
            start = j - i
            stop = False
            while start < kmp_start or (kmp_start < start < wall):
                if start < kmp_start:
                    i = lst[i]
                    if i < 0:
                        j, i = next_bucket(j)
                        if j >= n:
                            stop = True
                            break
                    start = j - i
                else:
                    kmp_start += k - mp[k]
                    k = mp[k]
            if stop:
                break
    if log_bucket:
        rows.append(["—", "—", "—", "hết văn bản", "; ".join(log_bucket)])
    return pre, Table("Các lần thử (bắt đầu so từ wall, không so lại phần đã kiểm tra)",
                      ["cửa sổ", "wall", "So sánh", "Kết quả", "Đọc xô trước đó"], rows), res


def trace_alpha_skip_search(x, y):
    m, n = len(x), len(y)
    sigma = max(2, len(set(x)))
    L, t = 0, m                      # L = floor(log_sigma m), tính bằng số nguyên
    while t >= sigma:
        t //= sigma
        L += 1
    L = max(1, min(L, m))
    fac = {}
    for pos in range(m - L + 1):
        fac.setdefault(x[pos:pos + L], []).append(pos)
    trie = {}
    for pos in range(m - L + 1):
        node = trie
        for ch in x[pos:pos + L]:
            node = node.setdefault(ch, {})
        node.setdefault(None, []).append(pos)
    pre = [Table(f"Trie các nhân tử độ dài L = ⌊log_{sigma} {m}⌋ = {L} của x", ["nhân tử", "vị trí trong x"],
                 [[f, "{" + ", ".join(map(str, v)) + "}"] for f, v in sorted(fac.items())],
                 f"Bước nhảy giữa các lần đọc: m − L + 1 = {m - L + 1}")]
    rows, c = [], Cmp(x, y)
    shift = m - L + 1
    found = []
    j = m - L
    while j <= n - L:
        node, k, read = trie, 0, ""
        while node is not None and k < L:
            ch = y[j + k]
            read += ch
            node = node.get(ch)
            k += 1
        tries = []
        if node is not None:
            for pos in node[None]:
                b = j - pos
                if b < 0 or b > n - m:
                    tries.append(f"j={b}: ngoài văn bản")
                    continue
                c.reset()
                t = 0
                while t < m and c.eq(t, b + t):
                    t += 1
                if t == m:
                    found.append(b)
                    tries.append(f"j={b}: {c.fmt()} **khớp**")
                else:
                    tries.append(f"j={b}: {c.fmt()}")
        rows.append([j, read, "có" if node is not None else "không", "; ".join(tries) or "—"])
        j += shift
    return pre, Table(f"Đọc nhân tử y[j..j+{L - 1}] tại j = m−L, bước {shift}",
                      ["j", "Nhân tử đọc", "Trong trie?", "Các cửa sổ thử"], rows), sorted(found)


# ------------------------------------------------------------------ NHÓM 4: vị trí bất kỳ
def trace_boyer_moore(x, y):
    m, n = len(x), len(y)
    gs = bm_gs(x)
    bc, bcd = bm_bc(x)
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        i = m - 1
        while i >= 0 and c.eq(i, i + j):
            i -= 1
        if i < 0:
            res.append(j)
            rows.append([j, c.fmt(), "**khớp**", f"bmGs[0] = {gs[0]}", "—", gs[0]])
            j += gs[0]
        else:
            a = y[i + j]
            b = bc.get(a, bcd) - m + 1 + i
            s = max(gs[i], b)
            rows.append([j, c.fmt(), f"sai tại i = {i}", gs[i], f"bmBc[{a}] − m + 1 + i = {b}", s])
            j += s
    return _pre_bm(x), Table("Các lần thử (so từ phải sang trái)",
                             ["j", "So sánh", "Kết quả", "bmGs[i]", "Bad-character", "Dịch"], rows), res


def trace_horspool(x, y):
    m, n = len(x), len(y)
    bc, d = bm_bc(x)
    last = x[m - 1]
    pre = [chtab("Bảng bmBc", bc, d)]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        ch = y[j + m - 1]
        if ch == last:
            i = 0
            while i < m - 1 and c.eq(i, j + i):
                i += 1
            ok = i >= m - 1
            kq = "**khớp**" if ok else f"sai tại x[{i}]"
            if ok:
                res.append(j)
        else:
            kq = f"{ch} ≠ x[m−1] = {last}"
        s = bc.get(ch, d)
        rows.append([j, f"y[{j + m - 1}] = {ch}", c.fmt(), kq, s])
        j += s
    return pre, Table("Các lần thử", ["j", "Ký tự cuối cửa sổ", "So x[0..m−2]", "Kết quả", "Dịch bmBc"], rows), res


def trace_tuned_bm(x, y):
    m, n = len(x), len(y)
    bc, d = bm_bc(x)
    last = x[m - 1]
    shift = bc.get(last, d)
    bc[last] = 0
    pre = [chtab(f"Bảng bmBc đã chỉnh (bmBc[{last}] = 0; shift = {shift})", bc, d)]

    def at(k):
        return y[k] if k < n else last

    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        path = [j]
        k = bc.get(at(j + m - 1), d)
        while k != 0:
            j += k
            k = bc.get(at(j + m - 1), d)
            j += k
            k = bc.get(at(j + m - 1), d)
            j += k
            k = bc.get(at(j + m - 1), d)
            path.append(j)
        c.reset()
        if j <= n - m:
            i = 0
            while i < m - 1 and c.eq(i, j + i):
                i += 1
            ok = i >= m - 1
            if ok:
                res.append(j)
            kq = "**khớp**" if ok else f"sai tại x[{i}]"
        else:
            kq = "vượt cuối, dừng"
        rows.append([" → ".join(map(str, path)), j, c.fmt(), kq, shift])
        j += shift
    return pre, Table("Vòng nhanh + kiểm tra", ["Vòng nhanh (các j)", "j kiểm tra", "So x[0..m−2]", "Kết quả",
                                                "Dịch"], rows), res


def trace_smith(x, y):
    m, n = len(x), len(y)
    bc, bd = bm_bc(x)
    qs, qd = qs_bc(x)
    pre = [chtab("Bảng bmBc", bc, bd), chtab("Bảng qsBc", qs, qd)]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        i = 0
        while i < m and c.eq(i, j + i):
            i += 1
        if i >= m:
            res.append(j)
        a = y[j + m - 1]
        s1 = bc.get(a, bd)
        if j + m < n:
            b = y[j + m]
            s2 = qs.get(b, qd)
        else:
            b, s2 = "∅", qd
        s = max(s1, s2)
        rows.append([j, c.fmt(), "**khớp**" if i >= m else f"sai tại x[{i}]", f"{a} → {s1}", f"{b} → {s2}", s])
        j += s
    return pre, Table("Các lần thử", ["j", "So sánh (→)", "Kết quả", "bmBc[y[j+m−1]]", "qsBc[y[j+m]]", "Dịch"],
                      rows), res


def trace_raita(x, y):
    m, n = len(x), len(y)
    bc, d = bm_bc(x)
    first, mid, last = x[0], x[m // 2], x[m - 1]
    pre = [chtab("Bảng bmBc", bc, d),
           Table("Thứ tự so", ["cuối", "giữa", "đầu", "còn lại"],
                 [[f"x[{m - 1}] = {last}", f"x[{m // 2}] = {mid}", f"x[0] = {first}", f"x[1..{m - 2}]"]])]
    rows, res, c = [], [], Cmp(x, y)
    j = 0
    while j <= n - m:
        c.reset()
        ch = y[j + m - 1]
        steps = [f"cuối y[{j + m - 1}]={ch}" + ("" if last == ch else " ≠")]
        ok = False
        if last == ch:
            b = y[j + m // 2]
            steps.append(f"giữa y[{j + m // 2}]={b}" + ("" if mid == b else " ≠"))
            if mid == b:
                a = y[j]
                steps.append(f"đầu y[{j}]={a}" + ("" if first == a else " ≠"))
                if first == a:
                    i = 1
                    while i < m - 1 and c.eq(i, j + i):
                        i += 1
                    ok = i >= m - 1
                    steps.append(c.fmt())
        if ok:
            res.append(j)
        s = bc.get(ch, d)
        rows.append([j, "; ".join(steps), "**khớp**" if ok else "sai", s])
        j += s
    return pre, Table("Các lần thử", ["j", "So sánh (cuối, giữa, đầu, còn lại)", "Kết quả", "Dịch bmBc"], rows), res


TRACERS = {
    "Not So Naive": trace_not_so_naive,
    "Karp-Rabin": trace_karp_rabin,
    "Shift Or": trace_shift_or,
    "Morris-Pratt": trace_morris_pratt,
    "Knuth-Morris-Pratt": trace_kmp,
    "Automat hữu hạn": trace_automaton,
    "Turbo BM": trace_turbo_bm,
    "Quick Search": trace_quick_search,
    "Zhu-Takaoka": trace_zhu_takaoka,
    "Berry-Ravindran": trace_berry_ravindran,
    "BNDM": trace_bndm,
    "Backward Oracle Matching": trace_bom,
    "Optimal Mismatch": trace_optimal_mismatch,
    "Maximal Shift": trace_maximal_shift,
    "Skip Search": trace_skip_search,
    "KMP Skip Search": trace_kmp_skip_search,
    "Alpha Skip Search": trace_alpha_skip_search,
    "Boyer-Moore": trace_boyer_moore,
    "Horspool": trace_horspool,
    "Tuned Boyer-Moore": trace_tuned_bm,
    "Smith": trace_smith,
    "Raita": trace_raita,
}

ALIASES = {"kmp": "Knuth-Morris-Pratt", "mp": "Morris-Pratt", "bm": "Boyer-Moore", "tbm": "Turbo BM",
           "bom": "Backward Oracle Matching", "qs": "Quick Search", "kr": "Karp-Rabin", "zt": "Zhu-Takaoka",
           "br": "Berry-Ravindran", "automat": "Automat hữu hạn", "dfa": "Automat hữu hạn",
           "nsn": "Not So Naive", "om": "Optimal Mismatch", "ms": "Maximal Shift", "skip": "Skip Search"}


def resolve(name):
    if name in TRACERS:
        return name
    key = name.lower()
    if key in ALIASES:
        return ALIASES[key]
    for full in TRACERS:
        if full.lower() == key:
            return full
    raise SystemExit(f"Không có {name!r}. Tên hợp lệ: {', '.join(TRACERS)}")


def run(name, x, y):
    """Chạy trace và đối chiếu với cài đặt thật. Trả về (pre, table, positions, reads)."""
    ty = CountingText(y)
    pre, tab, res = TRACERS[name](x, ty)
    real = CountingText(y)
    expect = sorted(ALGORITHMS[name](x, real))
    assert sorted(res) == expect == brute_force(x, y), (name, res, expect)
    assert ty.count == real.count, (name, "số lần đọc", ty.count, real.count)
    return pre, tab, sorted(res), real.count


def verify(x=X_DEFAULT, y=Y_DEFAULT):
    for name in TRACERS:
        run(name, x, y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-x", default=X_DEFAULT)
    ap.add_argument("-y", default=Y_DEFAULT)
    ap.add_argument("-a", "--algo", action="append")
    ap.add_argument("--md", action="store_true", help="in bảng dạng Markdown (để dán vào báo cáo)")
    args = ap.parse_args()
    names = [resolve(a) for a in args.algo] if args.algo else list(TRACERS)
    print(f"X = {args.x!r} (m = {len(args.x)}), Y = {args.y!r} (n = {len(args.y)})\n")
    for name in names:
        pre, tab, res, reads = run(name, args.x, args.y)
        print(f"{'#' * 3 if args.md else '==='} {name}\n")
        for t in pre + [tab]:
            print(t.markdown() if args.md else t.text())
            print()
        print(f"Kết quả: xuất hiện tại {res}; {reads} lần đọc ký tự văn bản "
              f"(bản trace đã đối chiếu khớp với cài đặt).\n")


if __name__ == "__main__":
    main()
