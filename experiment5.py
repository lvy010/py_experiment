from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import Dict, List, Tuple


def extract_phones(text: str) -> Tuple[List[str], List[str]]:
    mobile_pat = re.compile(r"\b1\d{10}\b")
    landline_pat = re.compile(r"\b\d{2,5}-\d{5,12}\b")

    mobiles = mobile_pat.findall(text)
    landlines = landline_pat.findall(text)
    return mobiles, landlines


def extract_idcards(text: str) -> List[Dict[str, str]]:

    pat = re.compile(r"(\d{6})(\d{4})(\d{2})(\d{2})(\d{3}[0-9Xx])")
    results: List[Dict[str, str]] = []
    for m in pat.finditer(text):
        number = m.group(0)
        results.append(
            {
                "id": number,
                "birth_year": m.group(2),
                "birth_month": m.group(3),
                "birth_day": m.group(4),
            }
        )
    return results


def fetch_book_titles(url: str) -> List[str]:
    """
    爬取书名，格式：《XXX》。
    若页面需要登录/验证，返回空并提示。
    """

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"[提示] 页面无法直接访问，可能需要验证码/登录：{e}")
        return []

    return re.findall(r"《([^》]+)》", html)


def main() -> None:
    print("题目1：提取电话号码")
    phone_text = "我的电话号码是13725894678、15885885901、155254747，固定电话为010-8574564,0278-54887341,265-25882255188,26525-22551，感谢您的惠存。"
    mobiles, landlines = extract_phones(phone_text)
    print("手机号:", mobiles)
    print("座机号:", landlines)

    print("\n题目2：提取身份证与出生年月日")
    id_text = "张三的身份证号：429006200512012587，李四的身份证号：12900620050812045X，王五的身份证号：12547820000915035X。"
    id_info = extract_idcards(id_text)
    for item in id_info:
        print(f"证件: {item['id']} 出生: {item['birth_year']}-{item['birth_month']}-{item['birth_day']}")

    print("\n题目3：爬取书名《…》")
    url = "https://mp.weixin.qq.com/s/D5_ZfhnQGe51sffEA4YVOw"
    titles = fetch_book_titles(url)
    if titles:
        print(f"共提取 {len(titles)} 个书名，示例前 10 个：", titles[:10])
    else:
        print("未能获取书名，可能页面需要人工验证；可浏览器打开后将页面 HTML 另存再解析。")


if __name__ == "__main__":
    main()

