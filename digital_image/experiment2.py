"""
数字图像处理实验二：
1) 对“lajiao”图像做 Gamma 变换，c=1.5，gamma ∈ {0.5, 0.75, 1.5, 2.0}，比较差异。
2) 对“lianhua”图像提取 0-7 位平面并展示。
3) 将“Lenna”RGB 转换为 HSI 与 YCrCb，并展示各分量含义。
生成图片与 HTML 报告存放在 output/ 目录。
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "jpg" / "素材"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def to_gray(path: Path) -> np.ndarray:
    """读取图像为灰度 uint8 ndarray。"""
    return np.array(Image.open(path).convert("L"), dtype=np.uint8)


def to_rgb(path: Path) -> np.ndarray:
    """读取图像为 RGB uint8 ndarray。"""
    return np.array(Image.open(path).convert("RGB"), dtype=np.uint8)


def save_array(arr: np.ndarray, filename: str) -> Path:
    dst = OUT_DIR / filename
    Image.fromarray(arr).save(dst)
    return dst


def image_to_base64(path: Path) -> str:
    data = path.read_bytes()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


# ========== 1) Gamma 变换 ==========
def gamma_transform(gray: np.ndarray, c: float, gamma: float) -> np.ndarray:
    norm = gray.astype(np.float32) / 255.0
    out = c * (norm ** gamma)
    out = np.clip(out * 255.0, 0, 255)
    return out.astype(np.uint8)


# ========== 2) 位平面提取 ==========
def bit_planes(gray: np.ndarray) -> Dict[int, np.ndarray]:
    planes: Dict[int, np.ndarray] = {}
    for b in range(8):
        planes[b] = ((gray >> b) & 1).astype(np.uint8) * 255
    return planes


# ========== 3) 颜色空间转换 ==========
def rgb_to_hsi(rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """返回 H, S, I，范围映射到 0-255。"""
    r, g, b = [rgb[:, :, i].astype(np.float32) / 255.0 for i in range(3)]
    eps = 1e-6
    num = 0.5 * ((r - g) + (r - b))
    den = np.sqrt((r - g) ** 2 + (r - b) * (g - b)) + eps
    theta = np.arccos(np.clip(num / den, -1, 1))  # [0, pi]
    h = np.where(b <= g, theta, 2 * np.pi - theta)  # [0, 2pi]
    h_norm = (h / (2 * np.pi) * 255).astype(np.uint8)

    i = (r + g + b) / 3.0
    i_norm = np.clip(i * 255, 0, 255).astype(np.uint8)

    min_rgb = np.minimum(np.minimum(r, g), b)
    s = np.where(i > eps, 1 - min_rgb / (i + eps), 0)
    s_norm = np.clip(s * 255, 0, 255).astype(np.uint8)

    return h_norm, s_norm, i_norm


def rgb_to_ycrcb(rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """BT.601 近似，输出 uint8。"""
    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)

    y = 0.299 * r + 0.587 * g + 0.114 * b
    cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
    cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b

    return (
        np.clip(y, 0, 255).astype(np.uint8),
        np.clip(cr, 0, 255).astype(np.uint8),
        np.clip(cb, 0, 255).astype(np.uint8),
    )


# ========== 报告生成 ==========
def add_section(title: str, images: Dict[str, Path]) -> str:
    blocks = []
    for name, path in images.items():
        img_b64 = image_to_base64(path)
        blocks.append(
            f"<div style='margin:6px 12px 6px 0;display:inline-block;text-align:center;'>"
            f"<div style='font-size:13px;color:#4b5563;margin-bottom:4px;'>{name}</div>"
            f"<img src='{img_b64}' style='max-width:240px;border:1px solid #d1d5db;'>"
            "</div>"
        )
    return f"<h3>{title}</h3><div style='margin-bottom:16px;'>{''.join(blocks)}</div>"


def build_report(sections: Dict[str, str]) -> None:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>数字图像处理实验二</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#f8fafc; color:#1f2937; padding:24px; }}
    h1 {{ margin-bottom:6px; }}
    h3 {{ margin:12px 0 6px 0; }}
  </style>
</head>
<body>
  <h1>数字图像处理实验二</h1>
  <p style="color:#6b7280;">Gamma 变换、位平面分解、RGB→HSI/YCrCb</p>
  {''.join(sections.values())}
</body>
</html>
"""
    (OUT_DIR / "report_exp2.html").write_text(html, encoding="utf-8")


def main() -> None:
    sections: Dict[str, str] = {}

    # 1) Gamma 变换
    lajiao = to_gray(IMG_DIR / "lajiao.jpg")
    gamma_values = [0.5, 0.75, 1.5, 2.0]
    gamma_imgs: Dict[str, Path] = {}
    for g in gamma_values:
        out = gamma_transform(lajiao, c=1.5, gamma=g)
        gamma_imgs[f"gamma={g}"] = save_array(out, f"lajiao_gamma_{g}.png")
    sections["gamma"] = add_section("辣椒图像 Gamma 变换 (c=1.5)", gamma_imgs)

    # 2) 位平面
    lotus = to_gray(IMG_DIR / "lianhua.jpg")
    planes = bit_planes(lotus)
    plane_imgs: Dict[str, Path] = {f"bit {b}": save_array(img, f"lianhua_bit{b}.png") for b, img in planes.items()}
    sections["bit"] = add_section("莲花 8 位平面", plane_imgs)

    # 3) 颜色空间
    lenna = to_rgb(IMG_DIR / "Lenna.jpg")
    h, s, i = rgb_to_hsi(lenna)
    y, cr, cb = rgb_to_ycrcb(lenna)
    color_imgs: Dict[str, Path] = {
        "HSI-H (色调)": save_array(h, "lenna_hsi_h.png"),
        "HSI-S (饱和度)": save_array(s, "lenna_hsi_s.png"),
        "HSI-I (亮度)": save_array(i, "lenna_hsi_i.png"),
        "Y (亮度)": save_array(y, "lenna_y.png"),
        "Cr (红色差分量)": save_array(cr, "lenna_cr.png"),
        "Cb (蓝色差分量)": save_array(cb, "lenna_cb.png"),
    }
    sections["color"] = add_section("Lenna RGB → HSI / YCrCb 分量", color_imgs)

    build_report(sections)
    print(f"输出完成：{OUT_DIR / 'report_exp2.html'}")


if __name__ == "__main__":
    main()

