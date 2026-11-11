"""CÁC THUẬT TOÁN BỔ SUNG — không trình bày trong báo cáo, giữ lại để tham khảo và so sánh.

Simon, Apostolico-Crochemore, Forward Dawg Matching, Ordered Alphabets, Apostolico-Giancarlo,
Reverse Colussi, Reverse Factor, Turbo Reverse Factor, Two Way, Colussi, Galil-Giancarlo,
Galil-Seiferas, và KMP theo sách Charras & Lecroq (bảng kmpNext biên chặt, kmpNext[0] = -1).
"""
from ._tables import mp_next, kmp_next, bm_bc, bm_gs, suffixes
from ._automata import SuffixAutomaton, with_sentinel
from .core import check_pattern, brute_force


def kmp_lecroq(x, y):
    """Knuth-Morris-Pratt (1977): như MP nhưng dùng biên chặt (kmpNext)."""
    check_pattern(x)
    m, n = len(x), len(y)
    nxt = kmp_next(x)
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


def _simon_lists(x):
    """L[q] = danh sách cạnh lùi 'có nghĩa' từ trạng thái q: (ký tự c, trạng thái t) với
    t = delta(q, c) > 0 và c khác x[q] (không phải cạnh tiến). Tổng kích thước <= 2m."""
    m = len(x)
    border = mp_next(x)
    L = [[] for _ in range(m + 1)]
    for q in range(1, m + 1):
        f = border[q]                         # trạng thái "biên" của q
        cand = list(L[f])
        if f < m:
            cand.append((x[f], f + 1))        # cạnh tiến của f
        seen = set()
        for c, t in cand:
            if c in seen or (q < m and c == x[q]):
                continue
            seen.add(c)
            L[q].append((c, t))
    return L


def simon(x, y):
    """Simon (1993): automat Σ*x tối giản bộ nhớ — chỉ lưu cạnh tiến và tối đa m cạnh lùi
    'có nghĩa'; các cạnh còn lại đều về trạng thái 0."""
    check_pattern(x)
    m, n = len(x), len(y)
    L = _simon_lists(x)
    res = []
    q = 0
    for j in range(n):
        c = y[j]
        if q < m and x[q] == c:
            q += 1
        else:
            nq = 0
            for a, t in L[q]:
                if a == c:
                    nq = t
                    break
            q = nq
        if q == m:
            res.append(j - m + 1)
    return res


def apostolico_crochemore(x, y):
    """Apostolico-Crochemore (1991): ell = độ dài khối ký tự đầu bằng x[0] (+1).
    So x[ell..m-1] từ trái sang phải trước, rồi x[0..ell-1]; dịch theo kmpNext.
    Tối đa 1,5n phép so sánh."""
    check_pattern(x)
    m, n = len(x), len(y)
    nxt = kmp_next(x)
    ell = 1
    while ell < m and x[ell - 1] == x[ell]:
        ell += 1
    if ell == m:
        ell = 0
    res = []
    i, j, k = ell, 0, 0
    while j <= n - m:
        while i < m and x[i] == y[i + j]:
            i += 1
        if i >= m:
            while k < ell and x[k] == y[j + k]:
                k += 1
            if k >= ell:
                res.append(j)
        j += i - nxt[i]
        if i == ell:
            k = max(0, k - 1)
        elif nxt[i] <= ell:
            k = max(0, nxt[i])
            i = ell
        else:
            k = ell
            i = nxt[i]
    return res


def forward_dawg_matching(x, y):
    """Forward Dawg Matching (Crochemore 1994): đọc văn bản trái→phải trên automat hậu tố của x,
    duy trì nhân tử dài nhất của x kết thúc tại j (độ dài ell); ell = m là một lần xuất hiện."""
    check_pattern(x)
    m, n = len(x), len(y)
    aut = SuffixAutomaton(x)
    res = []
    ell = 0
    state = 0
    for j in range(n):
        c = y[j]
        nxt = aut.trans[state].get(c)
        if nxt is not None:
            ell += 1
            state = nxt
        else:
            while state != 0 and c not in aut.trans[state]:
                state = aut.link[state]
            nxt = aut.trans[state].get(c)
            if nxt is not None:
                ell = aut.length[state] + 1
                state = nxt
            else:
                ell, state = 0, 0
        if ell == m:
            res.append(j - m + 1)
    return res


class _Window:
    """Đọc y[base + k]; vượt cuối văn bản trả về '' (nhỏ hơn mọi ký tự, như '\\0' trong C)."""

    __slots__ = ("y", "base", "n")

    def __init__(self, y, base):
        self.y, self.base, self.n = y, base, len(y)

    def __getitem__(self, k):
        p = self.base + k
        return self.y[p] if p < self.n else ""


def _next_maximal_suffix(w, m, st):
    """Tính tiếp hậu tố cực đại của w[0..m-1] (thứ tự từ điển). st = [i, j, k, p]."""
    i, j, k, p = st
    while j + k < m:
        a, b = w[i + k], w[j + k]
        if a == b:
            if k == p:
                j += p
                k = 1
            else:
                k += 1
        elif a > b:
            j += k
            k = 1
            p = j - i
        else:
            i = j
            j += 1
            k = p = 1
    st[:] = [i, j, k, p]


def ordered_alphabets(x, y):
    """String Matching on Ordered Alphabets (Crochemore 1992).

    Dùng thứ tự trên bảng chữ cái: song song với việc so khớp, duy trì hậu tố cực đại
    và chu kỳ của phần đã khớp để tính bước dịch. Không tiền xử lý mẫu, bộ nhớ O(1),
    thời gian O(n), tối đa 6n + 5 phép so sánh.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    res = []
    ip, jp, k, p = -1, 0, 1, 1
    i = j = 0
    while j <= n - m:
        while i + j < n and i < m and x[i] == y[i + j]:
            i += 1
        if i == 0:
            j += 1
            ip, jp, k, p = -1, 0, 1, 1
        else:
            if i >= m:
                res.append(j)
            st = [ip, jp, k, p]
            _next_maximal_suffix(_Window(y, j), i + 1, st)
            ip, jp, k, p = st
            periodic = ip < 0
            if not periodic and ip < p:
                t = 0
                while t <= ip and j + p + t < n and y[j + t] == y[j + p + t]:
                    t += 1
                periodic = t > ip
            if periodic:
                j += p
                i -= p
                if i < 0:
                    i = 0
                if jp - ip > p and ip + 1 < i:
                    jp -= p                       # giữ trạng thái hậu tố cực đại, dời theo chu kỳ
                else:
                    ip, jp, k, p = -1, 0, 1, 1    # trạng thái không còn hợp lệ: tính lại
            else:
                j += max(ip + 1, min(i - ip - 1, jp + 1)) + 1
                i = jp = 0
                ip = -1
                k = p = 1
    return res


def apostolico_giancarlo(x, y):
    """Apostolico-Giancarlo (1986): Boyer-Moore có nhớ.

    skip[i] = độ dài hậu tố của mẫu đã khớp với đoạn văn bản kết thúc tại vị trí j+i
    (ghi lại từ các lần thử trước); kết hợp suff[i] của mẫu để nhảy qua cả khối
    mà không so lại. Tối đa 1,5n phép so sánh.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    gs = bm_gs(x)
    suff = suffixes(x)
    bc, bc_def = bm_bc(x)
    skip = [0] * m
    res = []
    j = 0
    while j <= n - m:
        i = m - 1
        while i >= 0:
            k = skip[i]
            s = suff[i]
            if k > 0:
                if k > s:
                    i = -1 if i + 1 == s else i - s
                    break
                i -= k
                if k < s:
                    break
            elif x[i] == y[i + j]:
                i -= 1
            else:
                break
        if i < 0:
            res.append(j)
            skip[m - 1] = m
            shift = gs[0]
        else:
            skip[m - 1] = m - 1 - i
            shift = max(gs[i], bc.get(y[i + j], bc_def) - m + 1 + i)
        j += shift
        skip = skip[shift:] + [0] * shift
    return res


def _pre_reverse_colussi(x):
    """Tiền xử lý Reverse Colussi: thứ tự quét h, bảng dịch rcGs và hàm rcBc(c, s)."""
    m = len(x)
    # link[i+1] = vị trí xuất hiện trước đó của x[i] (trong x[0..m-2]); locc = xuất hiện cuối
    locc = {}
    link = [-1] * (m + 1)
    for i in range(m - 1):
        link[i + 1] = locc.get(x[i], -1)
        locc[x[i]] = i

    cache = {}

    def rc_bc(a, s):
        key = (a, s)
        if key in cache:
            return cache[key]
        i = locc.get(a, -1)
        j = link[m - s]
        while i - j != s and j >= 0:
            if i - j > s:
                i = link[i + 1]
            else:
                j = link[j + 1]
        while i - j > s:
            i = link[i + 1]
        cache[key] = m - i - 1
        return cache[key]

    hmin = [0] * (m + 2)
    k, i = 1, m - 1
    while k <= m:
        while i - k >= 0 and x[i - k] == x[i]:
            i -= 1
        hmin[k] = i
        q = k + 1
        while q <= m and hmin[q - k] - (q - k) > i:
            hmin[q] = hmin[q - k]
            q += 1
        i += q - k
        k = q
        if i == m:
            i = m - 1

    kmin = [0] * (m + 1)
    for k in range(m, 0, -1):
        kmin[hmin[k]] = k

    rmin = [0] * m
    r = m
    for i in range(m - 1, -1, -1):
        if hmin[i + 1] == i:
            r = i + 1
        rmin[i] = r

    h = [0] * (m + 1)
    gs = [0] * (m + 1)
    idx = 1
    for k in range(1, m + 1):
        if hmin[k] != m - 1 and kmin[hmin[k]] == k:
            h[idx] = hmin[k]
            gs[idx] = k
            idx += 1
    idx = m - 1
    for j in range(m - 2, -1, -1):
        if kmin[j] == 0:
            h[idx] = j
            gs[idx] = rmin[j]
            idx -= 1
    gs[m] = rmin[0]
    return h, gs, rc_bc


def reverse_colussi(x, y):
    """Reverse Colussi (Colussi 1994): cải tiến Boyer-Moore.

    Chia các vị trí của mẫu thành hai tập; so x[m-1] trước, rồi các vị trí theo thứ tự h.
    Bước dịch rcBc phụ thuộc cả ký tự văn bản lẫn bước dịch trước đó. Tối đa 2n phép so sánh.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    h, gs, rc_bc = _pre_reverse_colussi(x)
    res = []
    j = 0
    s = m
    while j <= n - m:
        while j <= n - m:
            c = y[j + m - 1]
            if x[m - 1] == c:
                break
            s = rc_bc(c, s)
            j += s
        if j > n - m:
            break
        i = 1
        while i < m and x[h[i]] == y[j + h[i]]:
            i += 1
        if i >= m:
            res.append(j)
        s = gs[i]
        j += s
    return res


def reverse_factor(x, y):
    """Reverse Factor (Lecroq 1992): đọc cửa sổ từ phải sang trái trên automat hậu tố của
    mẫu đảo ngược. Đọc được đoạn dài nhất là nhân tử; trạng thái kết thúc = tiền tố của x."""
    check_pattern(x)
    m, n = len(x), len(y)
    aut = SuffixAutomaton(x[::-1])
    period = m
    res = []
    j = 0
    while j <= n - m:
        i = m - 1
        state = 0
        shift = m
        while i >= 0:
            nxt = aut.trans[state].get(y[i + j])
            if nxt is None:
                break
            state = nxt
            if state in aut.terminal:
                period = shift
                shift = i
            i -= 1
        if i < 0:
            res.append(j)
            shift = period
        j += shift
    return res


def turbo_reverse_factor(x, y):
    """Turbo Reverse Factor (Crochemore et al. 1994): Reverse Factor + nhớ tiền tố đã khớp
    ở lần thử trước (độ dài m - shift) để không đọc lại; thời gian O(n), tối đa 2n phép so sánh."""
    check_pattern(x)
    m, n = len(x), len(y)
    aut = SuffixAutomaton(x[::-1])
    mp = mp_next(x)
    period = m - mp[m]
    res = []
    if n < m:
        return res
    t = 0
    while t < m and x[t] == y[t]:
        t += 1
    if t == m:
        res.append(0)
    shift = m
    j = 1
    while j <= n - m:
        i = m - 1
        state = 0
        u = m - 1 - shift
        period_u = (m - shift - mp[m - shift]) if shift != m else 0
        shift = m
        disp = 0

        def scan(i, state, disp, shift, lo):
            while i > lo:
                nxt = aut.trans[state].get(y[i + j])
                if nxt is None:
                    break
                disp += aut.shift(state, nxt)
                state = nxt
                if state in aut.terminal:
                    shift = i
                i -= 1
            return i, state, disp, shift

        i, state, disp, shift = scan(i, state, disp, shift, u)
        if i <= u:
            if disp == 0:
                res.append(j)
                shift = period
            else:
                mu = (u + 1) // 2
                if period_u <= mu:
                    u -= period_u
                    i, state, disp, shift = scan(i, state, disp, shift, u)
                    if i <= u:
                        shift = disp
                else:
                    u = u - mu - 1
                    i, state, disp, shift = scan(i, state, disp, shift, u)
        j += shift
    return res


def _max_suf(x, tilde=False):
    """Hậu tố cực đại của x theo thứ tự từ điển (tilde=True: thứ tự đảo).
    Trả về (vị trí bắt đầu - 1, chu kỳ)."""
    m = len(x)
    ms, j, k, p = -1, 0, 1, 1
    while j + k < m:
        a, b = x[j + k], x[ms + k]
        less = (a > b) if tilde else (a < b)
        if a == b:
            if k != p:
                k += 1
            else:
                j += p
                k = 1
        elif less:
            j += k
            k = 1
            p = j - ms
        else:
            ms = j
            j = ms + 1
            k = p = 1
    return ms, p


def two_way(x, y):
    """Two Way (Crochemore & Perrin 1991).

    Phân rã tới hạn x = x_l · x_r (vị trí ell). Mỗi lần thử: so x_r từ trái sang phải,
    nếu khớp hết thì so x_l từ phải sang trái. Bộ nhớ phụ O(1), thời gian O(n).
    """
    check_pattern(x)
    m, n = len(x), len(y)
    i1, p = _max_suf(x)
    i2, q = _max_suf(x, tilde=True)
    if i1 > i2:
        ell, per = i1, p
    else:
        ell, per = i2, q
    res = []
    # x[0..ell] có phải là hậu tố của x[0..per+ell] không (mẫu tuần hoàn với chu kỳ per)?
    periodic = all(k + per < m and x[k] == x[k + per] for k in range(ell + 1))
    if periodic:
        j = 0
        memory = -1
        while j <= n - m:
            i = max(ell, memory) + 1
            while i < m and x[i] == y[i + j]:
                i += 1
            if i >= m:
                i = ell
                while i > memory and x[i] == y[i + j]:
                    i -= 1
                if i <= memory:
                    res.append(j)
                j += per
                memory = m - per - 1
            else:
                j += i - ell
                memory = -1
    else:
        per = max(ell + 1, m - ell - 1) + 1
        j = 0
        while j <= n - m:
            i = ell + 1
            while i < m and x[i] == y[i + j]:
                i += 1
            if i >= m:
                i = ell
                while i >= 0 and x[i] == y[i + j]:
                    i -= 1
                if i < 0:
                    res.append(j)
                j += per
            else:
                j += i - ell
    return res


def _pre_colussi(x):
    """Tiền xử lý Colussi. Vị trí 'nohole' (kmin > 0) quét trái→phải trước, sau đó các
    vị trí 'hole' quét phải→trái. Trả về (h, next, shift, nd) với nd = chỉ số nohole cuối."""
    m = len(x)
    X = with_sentinel(x)
    hmax = [0] * (m + 2)
    i = k = 1
    while True:
        while X[i] == X[i - k]:
            i += 1
        hmax[k] = i
        q = k + 1
        while hmax[q - k] + k < i:
            hmax[q] = hmax[q - k] + k
            q += 1
        k = q
        if k == i + 1:
            i = k
        if k > m:
            break

    kmin = [0] * (m + 1)
    for i in range(m, 0, -1):
        if hmax[i] < m:
            kmin[hmax[i]] = i

    rmin = [0] * m
    r = 0
    for i in range(m - 1, -1, -1):
        if hmax[i + 1] == m:
            r = i + 1
        rmin[i] = r if kmin[i] == 0 else 0

    h = [0] * m
    s, r = -1, m
    for i in range(m):
        if kmin[i] == 0:
            r -= 1
            h[r] = i
        else:
            s += 1
            h[s] = i
    nd = s

    shift = [0] * (m + 1)
    for i in range(nd + 1):
        shift[i] = kmin[h[i]]
    for i in range(nd + 1, m):
        shift[i] = rmin[h[i]]
    shift[m] = rmin[0]

    nhd0 = [0] * (m + 1)
    s = 0
    for i in range(m):
        nhd0[i] = s
        if kmin[i] > 0:
            s += 1
    nhd0[m] = s

    nxt = [0] * (m + 1)
    for i in range(nd + 1):
        nxt[i] = nhd0[h[i] - kmin[h[i]]]
    for i in range(nd + 1, m):
        nxt[i] = nhd0[m - rmin[h[i]]]
    nxt[m] = nhd0[m - rmin[h[m - 1]]]
    return h, nxt, shift, nd


def colussi(x, y):
    """Colussi (1991): tinh chỉnh KMP với thứ tự so sánh hai pha (nohole → hole).
    Tiền xử lý O(m), tìm kiếm O(n), tối đa 1,5n phép so sánh."""
    check_pattern(x)
    m, n = len(x), len(y)
    if m == 1:
        return brute_force(x, y)
    h, nxt, shift, nd = _pre_colussi(x)
    res = []
    i = j = 0
    last = -1
    while j <= n - m:
        while i < m and last < j + h[i] and x[h[i]] == y[j + h[i]]:
            i += 1
        if i >= m or last >= j + h[i]:
            res.append(j)
            i = m
        if i > nd:
            last = j + m - 1
        j += shift[i]
        i = nxt[i]
    return res


def galil_giancarlo(x, y):
    """Galil-Giancarlo (1992): Colussi + xử lý riêng khối x[0]^ell ở đầu mẫu
    ('heavy'). Tối đa 4/3·n phép so sánh."""
    check_pattern(x)
    m, n = len(x), len(y)
    ell = 0
    while ell < m - 1 and x[ell] == x[ell + 1]:
        ell += 1
    res = []
    if ell == m - 1:                       # mẫu là lũy thừa của một ký tự
        run = 0
        for j in range(n):
            if x[0] == y[j]:
                run += 1
                if run >= m:
                    res.append(j - m + 1)
            else:
                run = 0
        return res
    h, nxt, shift, nd = _pre_colussi(x)
    i = j = 0
    heavy = False
    last = -1
    while j <= n - m:
        if heavy and i == 0:
            k = last - j + 1
            while j + k < n and x[0] == y[j + k]:
                k += 1
            if k <= ell or j + k >= n or x[ell + 1] != y[j + k]:
                i = 0
                j += k + 1
                last = j - 1
            else:
                i = 1
                last = j + k
                j = last - (ell + 1)
            heavy = False
        else:
            while i < m and last < j + h[i] and x[h[i]] == y[j + h[i]]:
                i += 1
            if i >= m or last >= j + h[i]:
                res.append(j)
                i = m
            if i > nd:
                last = j + m - 1
            j += shift[i]
            i = nxt[i]
        heavy = j <= last
    return res


def galil_seiferas(x, y, k=4):
    """Galil-Seiferas (1983): bộ nhớ phụ hằng (chỉ vài biến nguyên).

    Tiền xử lý tìm phân tích x = u·v trong đó v có ít 'tiền tố k-lũy thừa' (perfect
    factorization); tìm kiếm so v từ trái sang phải rồi u. Tối đa 5n phép so sánh.
    """
    check_pattern(x)
    m, n = len(x), len(y)
    X = with_sentinel(x)
    p = q = s = q1 = p2 = q2 = 0
    p1 = 1
    state = "newP1"
    while state != "search":
        if state == "newP1":
            while X[s + q1] == X[s + p1 + q1]:
                q1 += 1
            if p1 + q1 >= k * p1:
                p2, q2 = q1, 0
                state = "newP2"
            elif s + p1 + q1 == m:
                state = "search"
            else:
                p1 += q1 // k + 1
                q1 = 0
        elif state == "newP2":
            while X[s + q2] == X[s + p2 + q2] and p2 + q2 < k * p2:
                q2 += 1
            if p2 + q2 == k * p2:
                state = "parse"
            elif s + p2 + q2 == m:
                state = "search"
            elif q2 == p1 + q1:
                p2 += p1
                q2 -= p1
            else:
                p2 += q2 // k + 1
                q2 = 0
        else:  # parse
            while True:
                while X[s + q1] == X[s + p1 + q1]:
                    q1 += 1
                while p1 + q1 >= k * p1:
                    s += p1
                    q1 -= p1
                p1 += q1 // k + 1
                q1 = 0
                if p1 >= p2:
                    break
            state = "newP1"

    res = []
    while p <= n - m:
        while p + s + q < n and X[s + q] == y[p + s + q]:
            q += 1
        if q == m - s:
            t = 0
            while t <= s and x[t] == y[p + t]:
                t += 1
            if t > s:
                res.append(p)
        if q == p1 + q1:
            p += p1
            q -= p1
        else:
            p += q // k + 1
            q = 0
    return res
