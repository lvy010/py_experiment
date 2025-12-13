from __future__ import annotations

from typing import List, Tuple


def solve_chicken_rabbit(heads: int, legs: int) -> Tuple[int, int]:
    if heads < 0 or legs < 0 or legs % 2 != 0:
        raise ValueError("error input")

    rabbits = (legs - 2 * heads) // 2
    chickens = heads - rabbits

    if rabbits < 0 or chickens < 0 or 2 * chickens + 4 * rabbits != legs:
        raise ValueError("no solution")

    return chickens, rabbits


def selection_sort(data: List[int]) -> List[int]:
    arr = data.copy()
    n = len(arr)
    for i in range(n - 1):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr


def bubble_sort_desc(data: List[int]) -> List[int]:
    arr = data.copy()
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] < arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr


def run_chicken_rabbit_prompt() -> None:
    """交互式计算鸡兔同笼。"""
    raw = input("请输入鸡兔总数和腿总数，用空格分隔：").strip()
    if not raw:
        raise ValueError("未输入数据")
    try:
        heads_str, legs_str = raw.split()
        heads, legs = int(heads_str), int(legs_str)
        chickens, rabbits = solve_chicken_rabbit(heads, legs)
        print(f"鸡：{chickens} 只, 兔：{rabbits} 只")
    except ValueError as exc:
        raise ValueError("数据不正确，无解或格式错误") from exc


if __name__ == "__main__":
    # 题目2：例题4-2 鸡兔同笼
    try:
        run_chicken_rabbit_prompt()
    except ValueError as err:
        print(err)

    numbers = [196, 78, 89, 10, 67, 25, 34, 56, 82, 524]

    # 题目3：选择排序（升序）
    asc_sorted = selection_sort(numbers)
    print("选择排序（升序）：", asc_sorted)

    # 题目4：冒泡排序（降序）
    desc_sorted = bubble_sort_desc(numbers)
    print("冒泡排序（降序）：", desc_sorted)

