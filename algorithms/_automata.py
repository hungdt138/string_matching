"""Cấu trúc automat dùng chung: automat hậu tố (suffix automaton / DAWG).

Automat hậu tố của chuỗi p là automat đơn định nhỏ nhất nhận mọi hậu tố của p;
mọi nhân tử (factor) của p là một đường đi từ trạng thái đầu. Dựng trực tuyến O(|p|).
"""


class SuffixAutomaton:
    """trans[q]   : dict ký tự -> trạng thái
    link[q]    : liên kết hậu tố (suffix link)
    length[q]  : độ dài chuỗi dài nhất thuộc lớp trạng thái q
    firstpos[q]: vị trí kết thúc đầu tiên (từ 0) của các chuỗi thuộc q; firstpos[0] = -1
    terminal   : tập trạng thái kết thúc (ứng với các hậu tố của p)
    """

    def __init__(self, p):
        self.trans = [dict()]
        self.link = [-1]
        self.length = [0]
        self.firstpos = [-1]
        last = 0
        for pos, c in enumerate(p):
            cur = self._new(self.length[last] + 1, pos)
            q = last
            while q != -1 and c not in self.trans[q]:
                self.trans[q][c] = cur
                q = self.link[q]
            if q == -1:
                self.link[cur] = 0
            else:
                r = self.trans[q][c]
                if self.length[q] + 1 == self.length[r]:
                    self.link[cur] = r
                else:
                    clone = self._new(self.length[q] + 1, self.firstpos[r])
                    self.trans[clone] = dict(self.trans[r])
                    self.link[clone] = self.link[r]
                    while q != -1 and self.trans[q].get(c) == r:
                        self.trans[q][c] = clone
                        q = self.link[q]
                    self.link[r] = self.link[cur] = clone
            last = cur
        self.terminal = set()
        q = last
        while q > 0:
            self.terminal.add(q)
            q = self.link[q]
        self.terminal.add(0)

    def _new(self, length, firstpos):
        self.trans.append(dict())
        self.link.append(-1)
        self.length.append(length)
        self.firstpos.append(firstpos)
        return len(self.trans) - 1

    def shift(self, p, q):
        """Nhãn dịch của cạnh p -> q: tổng các nhãn trên đường đọc u = vị trí bắt đầu
        lần xuất hiện đầu tiên của u trong p (bằng 0 khi u là tiền tố của p)."""
        return self.firstpos[q] - self.firstpos[p] - 1


class Sentinel:
    """Ký tự canh đặt sau mẫu (tương đương '\\0' cuối chuỗi C): không bằng ký tự nào."""

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    __hash__ = object.__hash__


END = Sentinel()


def with_sentinel(x):
    return list(x) + [END]
