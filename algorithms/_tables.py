"""Các bảng tiền xử lý dùng chung giữa nhiều thuật toán.

Bảng theo bảng chữ cái được cài bằng dict + giá trị mặc định, nên không phụ thuộc
kích thước sigma (chạy được cho cả DNA, ASCII lẫn Unicode tiếng Việt).
"""


# ---------------------------------------------------------------- Morris-Pratt / KMP
def mp_next(x):
    """mpNext[i] = độ dài biên (border) dài nhất của x[0..i-1]; mpNext[0] = -1."""
    m = len(x)
    nxt = [0] * (m + 1)
    nxt[0] = -1
    i, j = 0, -1
    while i < m:
        while j > -1 and x[i] != x[j]:
            j = nxt[j]
        i += 1
        j += 1
        nxt[i] = j
    return nxt


def kmp_next(x):
    """kmpNext: như mpNext nhưng loại các biên có ký tự kế tiếp trùng (biên chặt)."""
    m = len(x)
    nxt = [0] * (m + 1)
    nxt[0] = -1
    i, j = 0, -1
    while i < m:
        while j > -1 and x[i] != x[j]:
            j = nxt[j]
        i += 1
        j += 1
        if i < m and x[i] == x[j]:
            nxt[i] = nxt[j]
        else:
            nxt[i] = j
    return nxt


# ---------------------------------------------------------------- Boyer-Moore family
def bm_bc(x):
    """Bad-character: bmBc[c] = m-1-(vị trí xuất hiện cuối của c trong x[0..m-2]); mặc định m.
    Trả về (dict, default)."""
    m = len(x)
    table = {}
    for i in range(m - 1):
        table[x[i]] = m - i - 1
    return table, m


def suffixes(x):
    """suff[i] = độ dài hậu tố chung dài nhất của x[0..i] và x."""
    m = len(x)
    suff = [0] * m
    suff[m - 1] = m
    g = m - 1
    f = 0
    for i in range(m - 2, -1, -1):
        if i > g and suff[i + m - 1 - f] < i - g:
            suff[i] = suff[i + m - 1 - f]
        else:
            if i < g:
                g = i
            f = i
            while g >= 0 and x[g] == x[g + m - 1 - f]:
                g -= 1
            suff[i] = f - g
    return suff


def bm_gs(x):
    """Good-suffix: bmGs[i] = dịch chuyển khi sai khớp tại x[i] sau khi x[i+1..m-1] đã khớp."""
    m = len(x)
    suff = suffixes(x)
    gs = [m] * m
    j = 0
    for i in range(m - 1, -1, -1):
        if suff[i] == i + 1:
            while j < m - 1 - i:
                if gs[j] == m:
                    gs[j] = m - 1 - i
                j += 1
    for i in range(m - 1):
        gs[m - 1 - suff[i]] = m - 1 - i
    return gs


def qs_bc(x):
    """Quick Search bad-character: qsBc[c] = m - (vị trí xuất hiện cuối của c); mặc định m+1."""
    m = len(x)
    table = {}
    for i in range(m):
        table[x[i]] = m - i
    return table, m + 1
