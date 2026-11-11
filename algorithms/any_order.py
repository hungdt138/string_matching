"""NHÓM 4 — TÌM KIẾM MẪU TỪ VỊ TRÍ BẤT KỲ (theo phân loại của bài giảng).

Boyer-Moore, Horspool, Tuned Boyer-Moore, Smith, Raita.
"""
from ._tables import bm_bc, bm_gs, qs_bc
from .core import check_pattern


def _eq_window(x, y, j, lo, hi):
    """So sánh x[lo..hi-1] với y[j+lo..j+hi-1] từ trái sang phải (tương đương memcmp)."""
    i = lo
    while i < hi and x[i] == y[j + i]:
        i += 1
    return i >= hi


def boyer_moore(x, y):
    """Boyer-Moore (1977): so sánh phải→trái, dịch = max(good-suffix, bad-character)."""
    check_pattern(x)
    m, n = len(x), len(y)
    gs = bm_gs(x)
    bc, bc_def = bm_bc(x)
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
            j += max(gs[i], bc.get(y[i + j], bc_def) - m + 1 + i)
    return res


def horspool(x, y):
    """Horspool (1980): chỉ dùng bad-character của ký tự CUỐI cửa sổ y[j+m-1]."""
    check_pattern(x)
    m, n = len(x), len(y)
    bc, bc_def = bm_bc(x)
    last = x[m - 1]
    res = []
    j = 0
    while j <= n - m:
        c = y[j + m - 1]
        if c == last and _eq_window(x, y, j, 0, m - 1):
            res.append(j)
        j += bc.get(c, bc_def)
    return res


def tuned_boyer_moore(x, y):
    """Tuned Boyer-Moore (Hume & Sunday 1991).

    Vòng lặp nhanh (ufast) 'trải' 3 bước dịch bad-character liên tiếp đến khi ký tự cuối
    cửa sổ bằng x[m-1] (bmBc[x[m-1]] được đặt = 0). Văn bản coi như được nối thêm m bản
    sao x[m-1] làm ký tự canh để vòng lặp luôn dừng.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    bc, bc_def = bm_bc(x)
    last = x[m - 1]
    shift = bc.get(last, bc_def)
    bc[last] = 0

    def at(k):                       # đọc văn bản kèm ký tự canh
        return y[k] if k < n else last

    res = []
    j = 0
    while j <= n - m:
        k = bc.get(at(j + m - 1), bc_def)
        while k != 0:
            j += k
            k = bc.get(at(j + m - 1), bc_def)
            j += k
            k = bc.get(at(j + m - 1), bc_def)
            j += k
            k = bc.get(at(j + m - 1), bc_def)
        if j <= n - m and _eq_window(x, y, j, 0, m - 1):
            res.append(j)
        j += shift
    return res


def smith(x, y):
    """Smith (1991): dịch = max(bad-character Horspool, bad-character Quick Search)."""
    check_pattern(x)
    m, n = len(x), len(y)
    bc, bc_def = bm_bc(x)
    qs, qs_def = qs_bc(x)
    res = []
    j = 0
    while j <= n - m:
        if _eq_window(x, y, j, 0, m):
            res.append(j)
        s1 = bc.get(y[j + m - 1], bc_def)
        s2 = qs.get(y[j + m], qs_def) if j + m < n else qs_def
        j += max(s1, s2)
    return res


def raita(x, y):
    """Raita (1992): so ký tự cuối, rồi ký tự giữa, rồi ký tự đầu, sau cùng phần còn lại."""
    check_pattern(x)
    m, n = len(x), len(y)
    bc, bc_def = bm_bc(x)
    first, mid, last = x[0], x[m // 2], x[m - 1]
    res = []
    j = 0
    while j <= n - m:
        c = y[j + m - 1]
        if (last == c and mid == y[j + m // 2] and first == y[j]
                and _eq_window(x, y, j, 1, m - 1)):
            res.append(j)
        j += bc.get(c, bc_def)
    return res
