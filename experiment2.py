from __future__ import annotations

import math
from datetime import datetime
from typing import List, Tuple
from random import randint, seed


def grade_letter(score: int) -> str:
    if score < 0 or score > 100:
        raise ValueError("invalid score")
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def diamond(n: int) -> List[str]:
    if n <= 0:
        raise ValueError("n must be positive")
    lines: List[str] = []
    for i in range(1, n + 1):
        lines.append(("*" * (2 * i - 1)).center(2 * n - 1))
    for i in range(n - 1, 0, -1):
        lines.append(("*" * (2 * i - 1)).center(2 * n - 1))
    return lines


def factors(num: int) -> List[int]:
    if num <= 1:
        return [num]
    facs: List[int] = []
    n = num
    i = 2
    while i * i <= n:
        while n % i == 0:
            facs.append(i)
            n //= i
        i += 1
    if n > 1:
        facs.append(n)
    return facs


def cylinder_volume_area(r: float, h: float) -> Tuple[float, float]:
    v = math.pi * r * r * h
    a = 2 * math.pi * r * (r + h)
    return v, a


def cone_volume_area(r: float, h: float) -> Tuple[float, float]:
    v = math.pi * r * r * h / 3
    a = math.pi * r * (r + math.sqrt(h * h + r * r))
    return v, a


def pascal_triangle(n: int) -> List[List[int]]:
    if n <= 0:
        return []
    tri = [[1]]
    for _ in range(1, n):
        prev = tri[-1]
        row = [1]
        for i in range(1, len(prev)):
            row.append(prev[i - 1] + prev[i])
        row.append(1)
        tri.append(row)
    return tri


def elapsed_2025() -> Tuple[int, int, int, int]:
    target = datetime(2025, 10, 11, 14, 34, 47)
    start = datetime(2025, 1, 1, 0, 0, 0)
    delta = target - start
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return days, hours, minutes, secs


def newton_root(x0: float, tol: float = 1e-8, max_iter: int = 50) -> Tuple[float, int]:
    def f(x: float) -> float:
        return 2 * x ** 3 - 4 * x ** 2 + 3 * x - 6

    def df(x: float) -> float:
        return 6 * x ** 2 - 8 * x + 3

    x = x0
    for k in range(1, max_iter + 1):
        fx = f(x)
        dfx = df(x)
        if dfx == 0:
            raise ZeroDivisionError("derivative zero")
        x_new = x - fx / dfx
        if abs(x_new - x) < tol:
            return x_new, k
        x = x_new
    return x, max_iter


def show_pascal(tri: List[List[int]]) -> List[str]:
    if not tri:
        return []
    width = len("   ".join(map(str, tri[-1])))
    return ["   ".join(map(str, row)).center(width) for row in tri]


if __name__ == "__main__":
    score = 77
    letter = grade_letter(score)
    print(f"4.3 score={score} -> {letter}")

    n = 6
    dia = diamond(n)
    print("4.10 diamond:")
    for line in dia:
        print(line)

    seed(0)
    num = randint(2, 10 ** 8)
    facs = factors(num)
    result = "*".join(map(str, facs))
    print(f"5.2 n={num} => {result}")

    r, h = 3.0, 5.0
    cyl_v, cyl_a = cylinder_volume_area(r, h)
    cone_v, cone_a = cone_volume_area(r, h)
    print(f"cylinder r={r}, h={h} volume={cyl_v:.4f}, area={cyl_a:.4f}")
    print(f"cone r={r}, h={h} volume={cone_v:.4f}, area={cone_a:.4f}")

    tri = pascal_triangle(6)
    print("Pascal triangle (6 rows):")
    for line in show_pascal(tri):
        print(line)

    days, hours, minutes, secs = elapsed_2025()
    print(f"2025 elapsed: {days} days {hours} hours {minutes} minutes {secs} seconds")

    root, steps = newton_root(1.5)
    print(f"Newton root near 1.5: {root:.10f} in {steps} steps")

