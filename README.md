# Các thuật toán đối sánh mẫu — mã nguồn báo cáo chuyên đề

22 thuật toán trình bày trong báo cáo (21 thuật toán của danh sách chuyên đề + Boyer-Moore),
xếp theo đúng phân loại của bài giảng; cài bằng Python thuần (3.9+).

## Cấu trúc

```
string_matching/
├── algorithms/
│   ├── left_to_right.py     # Chương 2 (6): Not So Naive, Karp-Rabin, Shift Or, Morris-Pratt,
│   │                        #   Knuth-Morris-Pratt (đúng mã giả bài giảng), Automat hữu hạn
│   ├── right_to_left.py     # Chương 3 (6): Turbo BM, Quick Search, Zhu-Takaoka, Berry-Ravindran,
│   │                        #   BNDM, Backward Oracle Matching
│   ├── specific_order.py    # Chương 4 (5): Optimal Mismatch, Maximal Shift, Skip Search,
│   │                        #   KMP Skip Search, Alpha Skip Search
│   ├── any_order.py         # Chương 5 (5): Boyer-Moore, Horspool, Tuned BM, Smith, Raita
│   ├── _tables.py           # bảng dùng chung: mpNext, kmpNext (Lecroq), bmBc, bmGs, suff, qsBc
│   ├── core.py              # CountingText (đếm số lần đọc ký tự), brute_force
│   ├── extra.py             # 12 thuật toán còn lại của danh sách + KMP biên chặt (không trình bày)
│   ├── _automata.py         # automat hậu tố (dùng trong extra.py)
│   └── __init__.py          # GROUPS (22, theo bài giảng), EXTRA, ALL_ALGORITHMS
├── kiemnghiem.py            # sinh bảng kiểm nghiệm từng bước + tự đối chiếu với cài đặt
├── tests/test_correctness.py   # đối chiếu với Brute-Force trên 5 017 bộ test (cả 35 cài đặt)
├── demo.py                  # bảng tổng hợp số lần đọc trên một ví dụ; --trace in vết đọc
├── benchmark.py             # thực nghiệm Chương 6
└── results/                 # CSV + PNG do benchmark.py sinh ra
```

## Chạy

```bash
python tests/test_correctness.py
python kiemnghiem.py                         # bảng kiểm nghiệm cả 22 thuật toán (ví dụ của bài giảng)
python kiemnghiem.py -a KMP -a Horspool      # chọn thuật toán (nhận tên tắt KMP, BM, BOM, QS, ...)
python kiemnghiem.py -x GCAGAGAG -y GCATCGCAGAGAGTATACAGTACG -a BM
python kiemnghiem.py --md                    # in dạng Markdown để dán vào báo cáo
python demo.py
pip install matplotlib && python benchmark.py
```

Ví dụ mặc định: X = "ABABCABAB", Y = "ABABDABACDABABCABAB" (bài giảng), kết quả: vị trí 10.

## Ghi chú

* Mọi hàm có dạng `ten_thuat_toan(x, y) -> list[int]`, trả về vị trí bắt đầu (từ 0).
* `kiemnghiem.py` chạy lại logic của từng thuật toán và ghi từng bước; hàm `verify()` kiểm tra
  vị trí tìm thấy và số lần đọc ký tự văn bản trùng với cài đặt thật.
* "Số lần đọc ký tự văn bản" tính cả lần đọc để tra bảng dịch, nên có thể lớn hơn số phép so
  sánh trong sách Charras & Lecroq.
* KMP theo mã giả bài giảng đọc Y[i] hai lần mỗi vòng (lệnh if và else if), nên khoảng 2 lần/ký tự.
* Karp-Rabin dùng hàm băm của sách (cơ số 2, mod 2^32) để tính tay được.
* Turbo BM: chỉ dùng turbo-shift và luật "dịch ≥ u+1" sau một lần sai khớp; thiếu điều kiện
  này sẽ bỏ sót kết quả (ví dụ x = accbcacc, y = xx) — ca này nằm trong bộ test.

## Tài liệu

C. Charras, T. Lecroq — *Handbook of Exact String Matching Algorithms*, 2004
(https://ligm.univ-eiffel.fr/~lecroq/string/index.html).
