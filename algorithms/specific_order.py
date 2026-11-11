"""NHÓM 3 — TÌM KIẾM MẪU TỪ VỊ TRÍ XÁC ĐỊNH (theo phân loại của bài giảng).

Thứ tự so sánh các ký tự của mẫu được quyết định trong pha tiền xử lý.
Optimal Mismatch, Maximal Shift, Skip Search, KMP Skip Search, Alpha Skip Search.
"""
from collections import Counter

from ._tables import mp_next, kmp_next, qs_bc
from .core import check_pattern, raw_text


def _match_shift(x, m, ploc, lshift, pat):
    """Dịch trái nhỏ nhất >= lshift sao cho ploc phần tử đầu của mẫu đã sắp vẫn khớp."""
    while lshift < m:
        i = ploc - 1
        while i >= 0:
            loc, c = pat[i]
            jj = loc - lshift
            if jj >= 0 and c != x[jj]:
                break
            i -= 1
        if i < 0:
            break
        lshift += 1
    return lshift


def _adapted_gs(x, pat):
    """Bảng good-suffix thích nghi với thứ tự quét pat (độ phức tạp O(m^2))."""
    m = len(x)
    gs = [0] * (m + 1)
    gs[0] = lshift = 1
    for ploc in range(1, m + 1):
        lshift = _match_shift(x, m, ploc, lshift, pat)
        gs[ploc] = lshift
    for ploc in range(m + 1):
        lshift = gs[ploc]
        while lshift < m:
            loc, c = pat[ploc]
            i = loc - lshift
            if i < 0 or c != x[i]:
                break
            lshift += 1
            lshift = _match_shift(x, m, ploc, lshift, pat)
        gs[ploc] = lshift
    return gs


def _ordered_search(x, y, pat):
    """Pha tìm kiếm chung của Optimal Mismatch và Maximal Shift."""
    m, n = len(x), len(y)
    qs, qs_def = qs_bc(x)
    gs = _adapted_gs(x, pat)
    res = []
    j = 0
    while j <= n - m:
        i = 0
        while i < m and pat[i][1] == y[j + pat[i][0]]:
            i += 1
        if i >= m:
            res.append(j)
        nxt = qs.get(y[j + m], qs_def) if j + m < n else qs_def
        j += max(gs[i], nxt)
    return res


def optimal_mismatch(x, y, freq=None):
    """Optimal Mismatch (Sunday 1990): so ký tự HIẾM NHẤT trước (để sớm gặp sai khớp).

    freq: tần suất ký tự trong ngôn ngữ/văn bản (thông tin tiên nghiệm).
    Mặc định ước lượng từ chính văn bản (không tính vào số phép so sánh).
    """
    check_pattern(x)
    m = len(x)
    if freq is None:
        freq = Counter(raw_text(y))
    order = sorted(range(m), key=lambda loc: (freq.get(x[loc], 0), -loc))
    pat = [(loc, x[loc]) for loc in order] + [(m, None)]
    return _ordered_search(x, y, pat)


def maximal_shift(x, y):
    """Maximal Shift (Sunday 1990): so trước ký tự có khoảng dịch tối thiểu minShift LỚN NHẤT."""
    check_pattern(x)
    m = len(x)
    min_shift = []
    for i in range(m):
        j = i - 1
        while j >= 0 and x[i] != x[j]:
            j -= 1
        min_shift.append(i - j)
    order = sorted(range(m), key=lambda loc: (-min_shift[loc], -loc))
    pat = [(loc, x[loc]) for loc in order] + [(m, None)]
    return _ordered_search(x, y, pat)


def skip_search(x, y):
    """Skip Search (Charras, Lecroq, Pehoushek 1998).

    Chỉ xét các ký tự y[j] với j = m-1, 2m-1, ... ; với mỗi vị trí k mà x[k] = y[j]
    (danh sách 'xô' z[y[j]]) thử khớp mẫu tại j-k.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    z = {}
    for i in range(m):
        z.setdefault(x[i], []).insert(0, i)      # thứ tự giảm dần như danh sách liên kết gốc
    res = []
    for j in range(m - 1, n, m):
        for k in z.get(y[j], ()):
            s = j - k
            if s < 0 or s + m > n:
                continue
            i = 0
            while i < m and x[i] == y[s + i]:
                i += 1
            if i == m:
                res.append(s)
    return res


def kmp_skip_search(x, y):
    """KMP Skip Search (Charras, Lecroq, Pehoushek 1998).

    Kết hợp Skip Search với bảng MP/KMP: dùng 'wall' (biên phải đoạn văn bản đã kiểm tra)
    để không so sánh lại ký tự, đạt thời gian O(n).
    """
    check_pattern(x)
    m, n = len(x), len(y)
    mp = mp_next(x)
    kmpn = kmp_next(x)
    z = {x[0]: 0}
    lst = [-1] * m
    for i in range(1, m):
        lst[i] = z.get(x[i], -1)
        z[x[i]] = i
    per = m - kmpn[m]
    res = []

    def next_bucket(j):
        while True:
            j += m
            if j >= n:
                return j, -1
            i = z.get(y[j], -1)
            if i >= 0:
                return j, i

    def attempt(start, wall):
        k = wall - start
        while k < m and x[k] == y[k + start]:
            k += 1
        return k

    wall = 0
    j, i = next_bucket(-1)
    if j >= n:
        return res
    start = j - i
    while start <= n - m:
        if start > wall:
            wall = start
        k = attempt(start, wall)
        wall = start + k
        if k == m:
            res.append(start)
            i -= per
        else:
            i = lst[i]
        if i < 0:
            j, i = next_bucket(j)
            if j >= n:
                return res
        kmp_start = start + k - kmpn[k]
        k = kmpn[k]
        start = j - i
        while start < kmp_start or (kmp_start < start < wall):
            if start < kmp_start:
                i = lst[i]
                if i < 0:
                    j, i = next_bucket(j)
                    if j >= n:
                        return res
                start = j - i
            else:
                kmp_start += k - mp[k]
                k = mp[k]
    return res


def alpha_skip_search(x, y, sigma=None):
    """Alpha Skip Search (Charras, Lecroq, Pehoushek 1998).

    Tổng quát Skip Search: xô theo NHÂN TỬ độ dài L = log_σ m (lưu trong trie) thay vì
    theo một ký tự. Chỉ đọc L ký tự văn bản ở các vị trí cách nhau m - L + 1.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    if sigma is None:
        sigma = max(2, len(set(x)))
    L, t = 0, m                      # L = floor(log_sigma m), tính bằng số nguyên
    while t >= sigma:
        t //= sigma
        L += 1
    L = max(1, min(L, m))
    # trie các nhân tử độ dài L của x; lá giữ danh sách vị trí bắt đầu
    trie = {}
    for pos in range(m - L + 1):
        node = trie
        for c in x[pos:pos + L]:
            node = node.setdefault(c, {})
        node.setdefault(None, []).append(pos)
    shift = m - L + 1
    res = []
    j = m - L
    while j <= n - L:
        node = trie
        k = 0
        while node is not None and k < L:
            node = node.get(y[j + k])
            k += 1
        if node is not None:
            for pos in node[None]:
                b = j - pos
                if b < 0 or b > n - m:
                    continue
                t = 0
                while t < m and x[t] == y[b + t]:
                    t += 1
                if t == m:
                    res.append(b)
        j += shift
    return sorted(res)
