"""Kiểm thử tính đúng: mọi thuật toán phải cho kết quả trùng thuật toán vét cạn.

Chạy:  python tests/test_correctness.py        (hoặc: pytest tests/)
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import ALL_ALGORITHMS as ALGORITHMS, CountingText, brute_force  # noqa: E402

# Các ca biên và ca kinh điển
FIXED_CASES = [
    ("GCAGAGAG", "GCATCGCAGAGAGTATACAGTACG"),   # ví dụ của Charras & Lecroq
    ("a", "aaaaa"),
    ("a", "bbbbb"),
    ("ab", "ab"),
    ("aa", "aaaaa"),
    ("aaab", "aaaaaaaaab"),
    ("abab", "abababababab"),
    ("abc", "ab"),                                # mẫu dài hơn văn bản
    ("x", ""),                                    # văn bản rỗng
    ("abcab", "abcabcabcab"),
    ("needle", "haystack with a needle and another needle"),
    ("tìm", "Thuật toán tìm kiếm mẫu — tìm mãi"),  # Unicode tiếng Việt
    ("aabaa", "aabaabaabaa"),
    ("baaa", "aaaabaaabaaa"),
    # các ca từng làm lộ lỗi khi phát triển (giữ lại để chống tái phát)
    ("accbcacc", "accbcaccaccbcacc"),   # Turbo BM: luật u+1 sau một lần khớp
    ("aaba", "aabaaabaa"),              # Ordered Alphabets: giữ trạng thái hậu tố cực đại
    ("b", "babb"),
]


def random_cases(seed=2026, rounds=3000):
    rng = random.Random(seed)
    for _ in range(rounds):
        sigma = rng.choice([1, 2, 3, 4, 26])
        alphabet = "abcdefghijklmnopqrstuvwxyz"[:sigma]
        m = rng.randint(1, 12)
        n = rng.randint(0, 80)
        x = "".join(rng.choice(alphabet) for _ in range(m))
        y = "".join(rng.choice(alphabet) for _ in range(n))
        if rng.random() < 0.3 and n >= m:          # cấy chắc chắn vài lần xuất hiện
            for _ in range(rng.randint(1, 3)):
                p = rng.randint(0, n - m)
                y = y[:p] + x + y[p + m:]
        yield x, y


def periodic_cases(seed=7, rounds=2000):
    """Mẫu tuần hoàn và văn bản lặp lại mẫu — loại dữ liệu dễ làm lộ lỗi bước dịch."""
    rng = random.Random(seed)
    for _ in range(rounds):
        alphabet = "abcd"[:rng.randint(1, 4)]
        m = rng.randint(1, 30)
        n = rng.randint(0, 300)
        x = "".join(rng.choice(alphabet) for _ in range(m))
        if rng.random() < 0.4:
            per = rng.randint(1, 4)
            x = (x[:per] * 30)[:m]
        y = "".join(rng.choice(alphabet) for _ in range(n))
        if rng.random() < 0.5:
            y = (x * 20)[:n]
        yield x, y


def run_all():
    failures = []
    cases = FIXED_CASES + list(random_cases()) + list(periodic_cases())
    for name, fn in ALGORITHMS.items():
        for x, y in cases:
            expected = brute_force(x, y)
            try:
                got_plain = fn(x, y)
                got_counted = fn(x, CountingText(y))
            except Exception as e:  # noqa: BLE001
                failures.append((name, x, y, f"lỗi {type(e).__name__}: {e}"))
                break
            if sorted(got_plain) != expected or sorted(got_counted) != expected:
                failures.append((name, x, y, f"mong đợi {expected}, nhận {sorted(got_plain)}"))
                break
    return len(cases), failures


def test_all_algorithms_match_brute_force():
    _, failures = run_all()
    assert not failures, failures


if __name__ == "__main__":
    total, failures = run_all()
    print(f"{len(ALGORITHMS)} thuật toán × {total} bộ test")
    if failures:
        for f in failures:
            print("SAI:", f)
        sys.exit(1)
    print("Tất cả thuật toán cho kết quả trùng với thuật toán vét cạn.")
