"""Các thuật toán tìm kiếm mẫu chính xác.

GROUPS  : 22 thuật toán trình bày trong báo cáo, xếp theo phân loại của bài giảng.
EXTRA   : 13 cài đặt bổ sung (không trình bày), dùng để tham khảo / so sánh.
"""
from .core import CountingText, brute_force
from . import left_to_right as _l, right_to_left as _r, specific_order as _s, any_order as _a
from . import extra as _x

GROUPS = {
    "Trái → phải": {
        "Not So Naive": _l.not_so_naive,
        "Karp-Rabin": _l.karp_rabin,
        "Shift Or": _l.shift_or,
        "Morris-Pratt": _l.morris_pratt,
        "Knuth-Morris-Pratt": _l.knuth_morris_pratt,
        "Automat hữu hạn": _l.automaton,
    },
    "Phải → trái": {
        "Turbo BM": _r.turbo_bm,
        "Quick Search": _r.quick_search,
        "Zhu-Takaoka": _r.zhu_takaoka,
        "Berry-Ravindran": _r.berry_ravindran,
        "BNDM": _r.bndm,
        "Backward Oracle Matching": _r.backward_oracle_matching,
    },
    "Vị trí xác định": {
        "Optimal Mismatch": _s.optimal_mismatch,
        "Maximal Shift": _s.maximal_shift,
        "Skip Search": _s.skip_search,
        "KMP Skip Search": _s.kmp_skip_search,
        "Alpha Skip Search": _s.alpha_skip_search,
    },
    "Vị trí bất kỳ": {
        "Boyer-Moore": _a.boyer_moore,
        "Horspool": _a.horspool,
        "Tuned Boyer-Moore": _a.tuned_boyer_moore,
        "Smith": _a.smith,
        "Raita": _a.raita,
    },
}

EXTRA = {
    "KMP (Lecroq, biên chặt)": _x.kmp_lecroq,
    "Simon": _x.simon,
    "Apostolico-Crochemore": _x.apostolico_crochemore,
    "Forward Dawg Matching": _x.forward_dawg_matching,
    "Ordered Alphabets": _x.ordered_alphabets,
    "Apostolico-Giancarlo": _x.apostolico_giancarlo,
    "Reverse Colussi": _x.reverse_colussi,
    "Reverse Factor": _x.reverse_factor,
    "Turbo Reverse Factor": _x.turbo_reverse_factor,
    "Two Way": _x.two_way,
    "Colussi": _x.colussi,
    "Galil-Giancarlo": _x.galil_giancarlo,
    "Galil-Seiferas": _x.galil_seiferas,
}

ALGORITHMS = {name: fn for g in GROUPS.values() for name, fn in g.items()}
GROUP_OF = {name: g for g, algs in GROUPS.items() for name in algs}
ALL_ALGORITHMS = {**ALGORITHMS, **EXTRA}

__all__ = ["GROUPS", "EXTRA", "ALGORITHMS", "ALL_ALGORITHMS", "GROUP_OF", "CountingText", "brute_force"]
