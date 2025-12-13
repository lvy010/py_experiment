from __future__ import annotations

import math
from random import random, randint, seed
from typing import List, Tuple


def estimate_pi(times: int) -> float:
    hits = 0
    for _ in range(times):
        x = random() * 2 - 1
        y = random() * 2 - 1
        if x * x + y * y <= 1:
            hits += 1
    return 4.0 * hits / times


def charity_simulation() -> Tuple[int, float, int]:
    seed(42)
    total = 0
    donors = 0
    for _ in range(50):
        donation = randint(50, 500)
        total += donation
        donors += 1
        if total >= 10000:
            break
    avg = total / donors
    return donors, avg, total


def list_slices(a: List[int]) -> Tuple[List[int], List[int], List[int], List[int], List[int], List[int]]:
    s1 = a[1:2:3]
    s2 = a[1:9:]
    s3 = a[-1:5:-1]
    s4 = a[:-2:-1]
    s5 = a[2::1]
    b = a.copy()
    b.append(9)
    b.append(12)
    return s1, s2, s3, s4, s5, b


def pattern(rows: int) -> List[str]:
    lines: List[str] = []
    width = len("* " * rows)
    for i in range(1, rows + 1):
        line = ("* " * i).strip()
        lines.append(line.center(width))
    for i in range(rows - 1, 0, -1):
        line = ("* " * i).strip()
        lines.append(line.center(width))
    return lines


def black_hole(n: int, start: int, max_iter: int = 100) -> Tuple[int, int, List[int]]:
    def format_num(x: int) -> str:
        return str(x).zfill(n)

    seen = []
    current = start
    for step in range(max_iter):
        seen.append(current)
        s = format_num(current)
        big = int("".join(sorted(s, reverse=True)))
        little = int("".join(sorted(s)))
        current = big - little
        if current in seen:
            return current, step + 1, seen
    return current, max_iter, seen


if __name__ == "__main__":
    seed(0)
    for t in (10_000, 100_000, 1_000_000, 10_000_000):
        print(f"pi estimate {t}: {estimate_pi(t):.6f}")

    donors, avg, total = charity_simulation()
    print(f"charity donors={donors}, avg={avg:.2f}, total={total}")

    base = [12, 15, 1, 21, 4, 5, 6, 45, 44, 4, 7, 5, 10, 21, 52]
    s1, s2, s3, s4, s5, b = list_slices(base)
    print("slice a[1:2:3]:", s1)
    print("slice a[1:9:]:", s2)
    print("slice a[-1:5:-1]:", s3)
    print("slice a[:-2:-1]:", s4)
    print("slice a[2::1]:", s5)
    print("list with extra:", b)

    pat = pattern(6)
    print("pattern:")
    for line in pat:
        print(line)

    n = 4
    start_val = 3524
    result, steps, seq = black_hole(n, start_val)
    print(f"black hole n={n}, start={start_val} -> {result} in {steps} steps")
    print("seq:", seq)

