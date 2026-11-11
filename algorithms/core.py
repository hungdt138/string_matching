"""
Thành phần dùng chung cho mọi thuật toán tìm kiếm mẫu.

Quy ước (theo Charras & Lecroq):
    x : mẫu (pattern), độ dài m
    y : văn bản (text), độ dài n
    sigma : kích thước bảng chữ cái
Mọi hàm tìm kiếm có dạng  search(x, y) -> list[int]
trả về danh sách vị trí bắt đầu (đánh số từ 0) của các lần xuất hiện x trong y.

Đo số phép so sánh: thay vì chèn biến đếm vào từng thuật toán (dễ sai, làm rối code),
ta bọc văn bản trong CountingText. Mỗi lần thuật toán đọc một ký tự của văn bản
(y[i]) bộ đếm tăng 1. Đây là thước đo "số lần truy cập ký tự văn bản" (text character
inspections) — thống nhất cho cả nhóm so sánh ký tự lẫn nhóm dùng bảng/bit/hash.
"""


class CountingText:
    """Bọc một chuỗi; đếm số lần đọc ký tự qua chỉ số y[i]."""

    __slots__ = ("raw", "count")

    def __init__(self, s: str):
        self.raw = s
        self.count = 0

    def __getitem__(self, i):
        if isinstance(i, slice):
            raise TypeError("Thuật toán không được cắt (slice) văn bản; hãy đọc từng ký tự")
        self.count += 1
        return self.raw[i]

    def __len__(self):
        return len(self.raw)


class TracingText(CountingText):
    """Như CountingText nhưng ghi lại thứ tự các vị trí được đọc (dùng cho ví dụ chạy tay)."""

    __slots__ = ("log",)

    def __init__(self, s: str):
        super().__init__(s)
        self.log = []

    def __getitem__(self, i):
        ch = super().__getitem__(i)
        self.log.append(i if i >= 0 else len(self.raw) + i)
        return ch


def raw_text(y):
    """Lấy chuỗi gốc (không đếm) — chỉ dùng cho thống kê tiên nghiệm, ví dụ tần suất ký tự."""
    return y.raw if isinstance(y, CountingText) else y


def brute_force(x, y):
    """Thuật toán vét cạn — dùng làm chuẩn đối chiếu trong kiểm thử."""
    m, n = len(x), len(y)
    res = []
    for j in range(n - m + 1):
        i = 0
        while i < m and x[i] == y[i + j]:
            i += 1
        if i == m:
            res.append(j)
    return res


def check_pattern(x):
    if len(x) == 0:
        raise ValueError("Mẫu rỗng")
