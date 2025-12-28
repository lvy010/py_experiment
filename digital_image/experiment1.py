"""
数字图像处理实验一：
- 安装并使用 Python + Pillow + Matplotlib。
- 读取“Lenna”并另存为 PNG。
- 对“莲花”灰度值统计并绘制灰度直方图。
- 对“Lenna”进行变暗、变亮、降低对比度、直方图均衡化，并绘制对应灰度直方图。
生成的图像与报告页面输出在 output/ 目录。
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "jpg" / "素材"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_gray(path: Path) -> np.ndarray:
    """读取图像并转为灰度 ndarray (uint8)。"""
    img = Image.open(path).convert("L")
    return np.array(img, dtype=np.uint8)


def save_image(arr: np.ndarray, filename: str) -> Path:
    """保存 ndarray 灰度图到 output 目录，返回路径。"""
    dst = OUT_DIR / filename
    Image.fromarray(arr).save(dst)
    return dst


def plot_hist(arr: np.ndarray, title: str, filename: str) -> Path:
    """绘制灰度直方图并保存。"""
    fig, ax = plt.subplots(figsize=(4, 3), dpi=150)
    ax.hist(arr.flatten(), bins=256, range=(0, 255), color="steelblue", edgecolor="black")
    ax.set_title(title)
    ax.set_xlabel("Gray Level")
    ax.set_ylabel("Pixel Count")
    ax.grid(alpha=0.3, linestyle="--")
    dst = OUT_DIR / filename
    fig.tight_layout()
    fig.savefig(dst)
    plt.close(fig)
    return dst


def adjust_brightness(arr: np.ndarray, factor: float) -> np.ndarray:
    """按比例调节亮度并裁剪到 0-255。"""
    out = np.clip(arr.astype(np.float32) * factor, 0, 255)
    return out.astype(np.uint8)


def adjust_contrast(arr: np.ndarray, alpha: float, center: float = 128.0) -> np.ndarray:
    """围绕中心灰度调整对比度。alpha<1 降低，alpha>1 提升。"""
    out = (arr.astype(np.float32) - center) * alpha + center
    out = np.clip(out, 0, 255)
    return out.astype(np.uint8)


def hist_equalize(arr: np.ndarray) -> np.ndarray:
    """直方图均衡化。"""
    hist = np.bincount(arr.flatten(), minlength=256)
    cdf = hist.cumsum()
    cdf_min = cdf[np.nonzero(cdf)].min()
    scale = 255 / (cdf[-1] - cdf_min)
    lut = np.floor((cdf - cdf_min) * scale).clip(0, 255).astype(np.uint8)
    return lut[arr]


def save_png_copy(src_path: Path, filename: str) -> Path:
    """将源图像另存为 PNG。"""
    img = Image.open(src_path)
    dst = OUT_DIR / filename
    img.save(dst, format="PNG")
    return dst


def image_to_base64(path: Path) -> str:
    """将图像文件转为 base64，便于 HTML 内嵌。"""
    data = path.read_bytes()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


@dataclass
class ResultItem:
    title: str
    image_path: Path
    hist_path: Path | None = None


def build_report(items: Dict[str, ResultItem], output_html: Path) -> None:
    """生成实验结果 HTML。"""
    sections = []
    for key, item in items.items():
        img_b64 = image_to_base64(item.image_path)
        hist_img = f'<img src="{img_b64}" alt="{item.title}" style="max-width:320px; border:1px solid #ccc;">'
        hist_block = ""
        if item.hist_path:
            hist_b64 = image_to_base64(item.hist_path)
            hist_block = (
                f'<div style="margin-top:8px;">'
                f'<img src="{hist_b64}" alt="{item.title} histogram" style="max-width:320px; border:1px solid #ccc;">'
                f"</div>"
            )
        sections.append(
            f"<div style='margin-bottom:20px;'><h3>{item.title}</h3>{hist_img}{hist_block}</div>"
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>数字图像处理实验一</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#f9fafb; color:#1f2933; padding:24px; }}
    h1 {{ margin-bottom:4px; }}
    .subtitle {{ color:#52616b; margin-top:0; }}
  </style>
</head>
<body>
  <h1>数字图像处理实验一</h1>
  <p class="subtitle">自动生成报告，包含灰度变换与直方图分析。</p>
  {''.join(sections)}
</body>
</html>
"""
    output_html.write_text(html, encoding="utf-8")


def main() -> None:
    lenna_path = IMG_DIR / "Lenna.jpg"
    lotus_path = IMG_DIR / "lianhua.jpg"

    # 1) 读取 Lenna 并另存为 PNG
    lenna_png = save_png_copy(lenna_path, "lenna.png")

    # 2) 莲花灰度与直方图
    lotus_gray = load_gray(lotus_path)
    lotus_img = save_image(lotus_gray, "lianhua_gray.png")
    lotus_hist = plot_hist(lotus_gray, "莲花灰度直方图", "lianhua_hist.png")

    # 3) Lenna 灰度变换
    lenna_gray = load_gray(lenna_path)
    dark = adjust_brightness(lenna_gray, 0.5)
    bright = adjust_brightness(lenna_gray, 1.5)
    low_contrast = adjust_contrast(lenna_gray, 0.6)
    equalized = hist_equalize(lenna_gray)

    # 保存变换结果与直方图
    results: Dict[str, ResultItem] = {
        "lenna_png": ResultItem("Lenna 另存为 PNG", lenna_png),
        "lotus": ResultItem("莲花灰度图与直方图", lotus_img, lotus_hist),
        "dark": ResultItem(
            "Lenna 变暗 (×0.5)", save_image(dark, "lenna_dark.png"), plot_hist(dark, "变暗直方图", "lenna_dark_hist.png")
        ),
        "bright": ResultItem(
            "Lenna 变亮 (×1.5)", save_image(bright, "lenna_bright.png"), plot_hist(bright, "变亮直方图", "lenna_bright_hist.png")
        ),
        "low_contrast": ResultItem(
            "Lenna 降低对比度 (α=0.6)",
            save_image(low_contrast, "lenna_low_contrast.png"),
            plot_hist(low_contrast, "降低对比度直方图", "lenna_low_contrast_hist.png"),
        ),
        "equalized": ResultItem(
            "Lenna 直方图均衡化",
            save_image(equalized, "lenna_equalized.png"),
            plot_hist(equalized, "均衡化直方图", "lenna_equalized_hist.png"),
        ),
    }

    # 生成 HTML 报告
    report_path = OUT_DIR / "report.html"
    build_report(results, report_path)
    print(f"输出完成：{report_path}")


if __name__ == "__main__":
    main()

