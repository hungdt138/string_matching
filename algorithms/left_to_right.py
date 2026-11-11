"""NHÓM 1 — TÌM KIẾM MẪU TỪ TRÁI SANG PHẢI (theo phân loại của bài giảng).

Not So Naive, Karp-Rabin, Shift Or, Morris-Pratt, Knuth-Morris-Pratt, Automat hữu hạn.
"""
from ._tables import mp_next
from .core import check_pattern, brute_force


def not_so_naive(x, y):
    """Not So Naive (Hancart 1992).

    Tiền xử lý O(1): xét x[0] có bằng x[1] hay không để có hai bước nhảy k, ell.
    So sánh x[1] trước, sau đó x[2..m-1], cuối cùng x[0].
    """
    check_pattern(x)
    m, n = len(x), len(y)
    if m < 2:
        return brute_force(x, y)
    if x[0] == x[1]:
        k, ell = 2, 1
    else:
        k, ell = 1, 2
    res = []
    j = 0
    while j <= n - m:
        if x[1] != y[j + 1]:
            j += k
        else:
            i = 2
            while i < m and x[i] == y[j + i]:
                i += 1
            if i == m and x[0] == y[j]:
                res.append(j)
            j += ell
    return res


def karp_rabin(x, y, base=2, mod=2 ** 32):
    """Karp-Rabin (1987): so sánh giá trị băm lăn (rolling hash), khớp băm thì kiểm tra lại từng ký tự.

    Mặc định dùng hàm băm của Charras & Lecroq: hash(w) = sum(ord(w[i]) * 2^(m-1-i)) mod 2^32,
    băm lại: hash' = (hash - ord(y[j]) * 2^(m-1)) * 2 + ord(y[j+m]). Nhờ vậy tính tay được.
    Muốn ít xung đột hơn có thể truyền base=256, mod=1_000_000_007.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    res = []
    if m > n:
        return res
    h = pow(base, m - 1, mod)          # trọng số của ký tự rời cửa sổ
    hx = hy = 0
    for i in range(m):
        hx = (hx * base + ord(x[i])) % mod
        hy = (hy * base + ord(y[i])) % mod
    j = 0
    while True:
        if hx == hy:
            i = 0
            while i < m and x[i] == y[j + i]:
                i += 1
            if i == m:
                res.append(j)
        if j >= n - m:
            break
        hy = ((hy - ord(y[j]) * h) * base + ord(y[j + m])) % mod
        j += 1
    return res


def shift_or(x, y):
    """Shift Or (Baeza-Yates & Gonnet 1992) — song song hóa bit.

    Bit i của trạng thái D bằng 0 khi x[0..i] khớp với y[j-i..j].
    Python dùng số nguyên không giới hạn nên chạy được với m > độ dài từ máy.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    full = (1 << m) - 1
    S = {}
    for i, c in enumerate(x):
        S[c] = S.get(c, full) & ~(1 << i) & full
    hi = 1 << (m - 1)
    D = full
    res = []
    for j in range(n):
        D = ((D << 1) | S.get(y[j], full)) & full
        if not D & hi:
            res.append(j - m + 1)
    return res


def morris_pratt(x, y):
    """Morris-Pratt (1970): dịch chuyển theo biên dài nhất của phần đã khớp."""
    check_pattern(x)
    m, n = len(x), len(y)
    nxt = mp_next(x)
    res = []
    i = 0
    for j in range(n):
        while i > -1 and x[i] != y[j]:
            i = nxt[i]
        i += 1
        if i >= m:
            res.append(j - i + 1)
            i = nxt[i]
    return res


def pre_kmp(x):
    """Tiền xử lý KMP theo bài giảng: kmpNext[i] = độ dài biên dài nhất của x[0..i]
    (hàm tiền tố). kmpNext[0] luôn bằng 0."""
    m = len(x)
    nxt = [0] * m
    i, length = 1, 0
    while i < m:
        if x[i] == x[length]:
            length += 1
            nxt[i] = length
            i += 1
        elif length != 0:
            length = nxt[length - 1]
        else:
            nxt[i] = 0
            i += 1
    return nxt


def knuth_morris_pratt(x, y):
    """Knuth-Morris-Pratt (1977) theo đúng mã giả bài giảng.

    i chạy trên văn bản, j chạy trên mẫu. Khớp thì tăng cả hai; sai khớp thì
    lùi j về kmpNext[j-1] (không lùi i); j = 0 mà vẫn sai thì tăng i.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    nxt = pre_kmp(x)
    res = []
    i = j = 0
    while i < n:
        if x[j] == y[i]:
            i += 1
            j += 1
        if j == m:
            res.append(i - j)
            j = nxt[j - 1]
        elif i < n and x[j] != y[i]:
            if j != 0:
                j = nxt[j - 1]
            else:
                i += 1
    return res


def build_dfa(x):
    """Automat đơn định nhận ngôn ngữ Σ*x. delta[q][c] -> trạng thái kế; ký tự ngoài x về 0."""
    m = len(x)
    alphabet = set(x)
    delta = [dict() for _ in range(m + 1)]
    for c in alphabet:
        delta[0][c] = 0
    delta[0][x[0]] = 1
    restart = 0                       # trạng thái sau khi đọc x[1..q-1]
    for q in range(1, m + 1):
        delta[q].update(delta[restart])
        if q < m:
            delta[q][x[q]] = q + 1
            restart = delta[restart][x[q]]
    return delta


def automaton(x, y):
    """Automat hữu hạn: mỗi ký tự văn bản được đọc đúng một lần."""
    check_pattern(x)
    m, n = len(x), len(y)
    delta = build_dfa(x)
    res = []
    q = 0
    for j in range(n):
        q = delta[q].get(y[j], 0)
        if q == m:
            res.append(j - m + 1)
    return res
