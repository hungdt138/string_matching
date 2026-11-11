"""NHÓM 2 — TÌM KIẾM MẪU TỪ PHẢI SANG TRÁI (theo phân loại của bài giảng).

Turbo BM, Quick Search (Sunday), Zhu-Takaoka, Berry-Ravindran, BNDM, Backward Oracle Matching.
"""
from ._tables import bm_bc, bm_gs, qs_bc
from .core import check_pattern, brute_force


def turbo_bm(x, y):
    """Turbo Boyer-Moore (Crochemore et al. 1992): nhớ đoạn đã khớp ở lần thử trước
    để nhảy qua nó (jump) và dịch thêm turbo-shift; bảo đảm tối đa 2n phép so sánh.

    Ghi chú cài đặt: turbo-shift và luật 'dịch ít nhất u+1' chỉ đúng khi đoạn nhớ u
    đứng sau một lần SAI KHỚP. Sau một lần khớp trọn vẹn, đoạn nhớ chỉ dùng để nhảy.
    (Phiên bản đầu viết theo mã C trong sách thiếu điều kiện này và bỏ sót kết quả,
    ví dụ x = accbcacc, y = xx; bộ test của báo cáo phát hiện lỗi đó.)
    """
    check_pattern(x)
    m, n = len(x), len(y)
    gs = bm_gs(x)
    bc, bc_def = bm_bc(x)
    res = []
    j = u = 0
    shift = m
    after_match = False
    while j <= n - m:
        i = m - 1
        while i >= 0 and x[i] == y[i + j]:
            i -= 1
            if u != 0 and i == m - 1 - shift:
                i -= u                      # nhảy qua đoạn đã biết là khớp
        if i < 0:
            res.append(j)
            shift = gs[0]
            u = m - shift
            after_match = True
        else:
            v = m - 1 - i
            turbo_shift = 0 if after_match else u - v
            bc_shift = bc.get(y[i + j], bc_def) - m + 1 + i
            shift = max(turbo_shift, bc_shift, gs[i])
            if shift == gs[i]:
                u = min(m - shift, v)
            else:
                if turbo_shift < bc_shift and not after_match:
                    shift = max(shift, u + 1)
                u = 0
            after_match = False
        j += shift
    return res


def quick_search(x, y):
    """Quick Search (Sunday 1990): dịch theo ký tự NGAY SAU cửa sổ y[j+m]."""
    check_pattern(x)
    m, n = len(x), len(y)
    qs, qs_def = qs_bc(x)
    res = []
    j = 0
    while j <= n - m:
        if _match_ltr(x, y, j):
            res.append(j)
        if j + m >= n:
            break
        j += qs.get(y[j + m], qs_def)
    return res


def _match_ltr(x, y, j):
    """So x[0..m-1] với y[j..j+m-1] từ trái sang phải."""
    i, m = 0, len(x)
    while i < m and x[i] == y[j + i]:
        i += 1
    return i >= m


def zhu_takaoka(x, y):
    """Zhu-Takaoka (1987): bad-character theo CẶP hai ký tự cuối cửa sổ y[j+m-2], y[j+m-1]."""
    check_pattern(x)
    m, n = len(x), len(y)
    if m < 2:
        return brute_force(x, y)
    gs = bm_gs(x)
    pair = {}
    for i in range(1, m - 1):
        pair[(x[i - 1], x[i])] = m - 1 - i

    def zt_bc(a, b):
        v = pair.get((a, b))
        if v is not None:
            return v
        return m - 1 if b == x[0] else m

    res = []
    j = 0
    while j <= n - m:
        i = m - 1
        while i >= 0 and x[i] == y[i + j]:
            i -= 1
        if i < 0:
            res.append(j)
            j += gs[0]
        else:
            j += max(gs[i], zt_bc(y[j + m - 2], y[j + m - 1]))
    return res


def berry_ravindran(x, y):
    """Berry-Ravindran (1999): dịch theo cặp ký tự NGAY SAU cửa sổ y[j+m], y[j+m+1].

    Lần thử so sánh từ phải sang trái. Hai vị trí vượt quá văn bản đọc ra ký tự canh (None).
    """
    check_pattern(x)
    m, n = len(x), len(y)
    pair = {}
    for i in range(m - 1):
        pair[(x[i], x[i + 1])] = m - i
    last, first = x[m - 1], x[0]

    def br_bc(a, b):
        if a == last:
            return 1
        v = pair.get((a, b))
        if v is not None:
            return v
        return m + 1 if b == first else m + 2

    res = []
    j = 0
    while j <= n - m:
        i = m - 1
        while i >= 0 and x[i] == y[j + i]:
            i -= 1
        if i < 0:
            res.append(j)
        a = y[j + m] if j + m < n else None
        b = y[j + m + 1] if j + m + 1 < n else None
        j += br_bc(a, b)
    return res


def bndm(x, y):
    """Backward Nondeterministic Dawg Matching (Navarro & Raffinot 1998).

    Mô phỏng bằng bit automat hậu tố KHÔNG đơn định của mẫu đảo ngược;
    đọc cửa sổ từ phải sang trái, ghi nhớ vị trí tiền tố dài nhất (last) để dịch.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    full = (1 << m) - 1
    B = {}
    s = 1
    for i in range(m):
        c = x[m - i - 1]
        B[c] = B.get(c, 0) | s
        s <<= 1
    hi = 1 << (m - 1)                     # bit cao nhất bật <=> đoạn đã đọc là TIỀN TỐ của x
    res = []
    j = 0
    while j <= n - m:
        i = m - 1
        last = m
        d = full
        while i >= 0 and d != 0:
            d &= B.get(y[j + i], 0)
            i -= 1
            if d & hi:
                if i >= 0:
                    last = i + 1                  # ghi nhớ tiền tố dài nhất gặp được
                else:
                    res.append(j)
            d = (d << 1) & full
        j += last
    return res


def build_factor_oracle(p):
    """Factor oracle của chuỗi p (Allauzen, Crochemore, Raffinot 1999), dựng trực tuyến O(|p|)."""
    m = len(p)
    trans = [dict() for _ in range(m + 1)]
    supply = [-1] * (m + 1)
    for i in range(m):
        c = p[i]
        trans[i][c] = i + 1
        k = supply[i]
        while k > -1 and c not in trans[k]:
            trans[k][c] = i + 1
            k = supply[k]
        supply[i + 1] = 0 if k == -1 else trans[k][c]
    return trans


def backward_oracle_matching(x, y):
    """Backward Oracle Matching (Allauzen, Crochemore, Raffinot 1999).

    Đọc cửa sổ từ phải sang trái trên factor oracle của mẫu đảo ngược.
    Không đi tiếp được tại y[j+i] => y[j+i..j+m-1] không là nhân tử của x => dịch i+1.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    trans = build_factor_oracle(x[::-1])
    res = []
    j = 0
    while j <= n - m:
        q = 0
        i = m - 1
        while i >= 0:
            nq = trans[q].get(y[j + i])
            if nq is None:
                break
            q = nq
            i -= 1
        if i < 0:
            res.append(j)
            j += 1
        else:
            j += i + 1
    return res
