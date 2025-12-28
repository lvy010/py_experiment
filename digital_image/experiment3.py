"""
数字图像处理实验三：
1) “jizhu” 添加高斯噪声，再用不同 sigma 的高斯滤波去噪。
2) “train” 添加椒盐噪声，再用 3/7/11/15 的中值滤波比较效果。
3) “lianhua” 添加椒盐噪声，再用 11/15 的均值滤波比较效果。
4) “Lenna” 使用 Sobel 算子锐化，比较不同锐化系数。
生成图像与 HTML 报告输出到 output/ 目录。
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image


ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "jpg" / "素材"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ========== 基础工具 ==========
def to_gray(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("L"), dtype=np.uint8)


def save_array(arr: np.ndarray, filename: str) -> Path:
    dst = OUT_DIR / filename
    Image.fromarray(arr).save(dst)
    return dst


def image_to_base64(path: Path) -> str:
    data = path.read_bytes()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


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
  <title>数字图像处理实验三</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#f8fafc; color:#1f2937; padding:24px; }}
    h1 {{ margin-bottom:6px; }}
    h3 {{ margin:12px 0 6px 0; }}
  </style>
</head>
<body>
  <h1>数字图像处理实验三</h1>
  <p style="color:#6b7280;">噪声抑制与锐化实验</p>
  {''.join(sections.values())}
</body>
</html>
"""
    (OUT_DIR / "report_exp3.html").write_text(html, encoding="utf-8")


# ========== 噪声与滤波 ==========
def add_gaussian_noise(gray: np.ndarray, mean: float = 0.0, std: float = 15.0) -> np.ndarray:
    noise = np.random.normal(mean, std, gray.shape).astype(np.float32)
    out = np.clip(gray.astype(np.float32) + noise, 0, 255)
    return out.astype(np.uint8)


def gaussian_kernel(sigma: float) -> np.ndarray:
    size = int(6 * sigma + 1)
    size = size if size % 2 == 1 else size + 1
    k = size // 2
    x = np.arange(-k, k + 1)
    y = x[:, None]
    kernel = np.exp(-(x ** 2 + y ** 2) / (2 * sigma ** 2))
    kernel /= kernel.sum()
    return kernel.astype(np.float32)


def convolve(gray: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    pad_y, pad_x = kernel.shape[0] // 2, kernel.shape[1] // 2
    padded = np.pad(gray, ((pad_y, pad_y), (pad_x, pad_x)), mode="reflect")
    windows = sliding_window_view(padded, kernel.shape)
    out = np.einsum("ij,xyij->xy", kernel, windows)
    return np.clip(out, 0, 255).astype(np.uint8)


def median_filter(gray: np.ndarray, ksize: int) -> np.ndarray:
    pad = ksize // 2
    padded = np.pad(gray, pad, mode="reflect")
    windows = sliding_window_view(padded, (ksize, ksize))
    out = np.median(windows, axis=(2, 3))
    return out.astype(np.uint8)


def mean_filter(gray: np.ndarray, ksize: int) -> np.ndarray:
    kernel = np.ones((ksize, ksize), dtype=np.float32) / (ksize * ksize)
    return convolve(gray, kernel)


# ========== Sobel 锐化 ==========
def sobel_sharpen(gray: np.ndarray, alpha: float) -> np.ndarray:
    gx_k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    gy_k = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)
    gx = convolve(gray, gx_k)
    gy = convolve(gray, gy_k)
    mag = np.hypot(gx.astype(np.float32), gy.astype(np.float32))
    mag = mag / (mag.max() + 1e-6) * 255.0
    sharpened = np.clip(gray.astype(np.float32) + alpha * mag, 0, 255)
    return sharpened.astype(np.uint8)


def main() -> None:
    sections: Dict[str, str] = {}

    # 1) jizhu 高斯噪声 + 高斯滤波
    jizhu = to_gray(IMG_DIR / "jizhu.jpg")
    jizhu_noisy = add_gaussian_noise(jizhu, mean=0, std=15)
    sigmas = [0.8, 1.2, 1.8]
    gauss_imgs: Dict[str, Path] = {"原图": save_array(jizhu, "jizhu_orig.png"), "加高斯噪声": save_array(jizhu_noisy, "jizhu_gauss_noise.png")}
    for s in sigmas:
        kernel = gaussian_kernel(s)
        gauss_imgs[f"高斯滤波 σ={s}"] = save_array(convolve(jizhu_noisy, kernel), f"jizhu_gauss_sigma{s}.png")
    sections["gauss"] = add_section("jizhu：高斯噪声与不同 σ 高斯滤波", gauss_imgs)

    # 2) train 椒盐噪声 + 中值滤波
    train = to_gray(IMG_DIR / "train.jpg")
    def add_salt_pepper(img: np.ndarray, amount: float = 0.02, salt_vs_pepper: float = 0.5) -> np.ndarray:
        out = img.copy()
        num = int(amount * img.size)
        num_salt = int(num * salt_vs_pepper)
        num_pepper = num - num_salt
        coords_s = (np.random.randint(0, img.shape[0], num_salt), np.random.randint(0, img.shape[1], num_salt))
        coords_p = (np.random.randint(0, img.shape[0], num_pepper), np.random.randint(0, img.shape[1], num_pepper))
        out[coords_s] = 255
        out[coords_p] = 0
        return out

    train_sp = add_salt_pepper(train, amount=0.03)
    sizes = [3, 7, 11, 15]
    median_imgs: Dict[str, Path] = {"原图": save_array(train, "train_orig.png"), "椒盐噪声": save_array(train_sp, "train_sp.png")}
    for k in sizes:
        median_imgs[f"中值 {k}x{k}"] = save_array(median_filter(train_sp, k), f"train_median_{k}.png")
    sections["median"] = add_section("train：椒盐噪声与不同模板中值滤波", median_imgs)

    # 3) lianhua 椒盐噪声 + 均值滤波
    lotus = to_gray(IMG_DIR / "lianhua.jpg")
    lotus_sp = add_salt_pepper(lotus, amount=0.03)
    mean_sizes = [11, 15]
    mean_imgs: Dict[str, Path] = {"原图": save_array(lotus, "lianhua_orig.png"), "椒盐噪声": save_array(lotus_sp, "lianhua_sp.png")}
    for k in mean_sizes:
        mean_imgs[f"均值 {k}x{k}"] = save_array(mean_filter(lotus_sp, k), f"lianhua_mean_{k}.png")
    sections["mean"] = add_section("莲花：椒盐噪声与不同模板均值滤波", mean_imgs)

    # 4) Lenna Sobel 锐化
    lenna = to_gray(IMG_DIR / "Lenna.jpg")
    alphas = [0.3, 0.6, 1.0]
    sharpen_imgs: Dict[str, Path] = {"原图": save_array(lenna, "lenna_orig.png")}
    for a in alphas:
        sharpen_imgs[f"Sobel锐化 α={a}"] = save_array(sobel_sharpen(lenna, a), f"lenna_sobel_{a}.png")
    sections["sobel"] = add_section("Lenna：Sobel 锐化系数对比", sharpen_imgs)

    build_report(sections)
    print(f"输出完成：{OUT_DIR / 'report_exp3.html'}")


if __name__ == "__main__":
    main()

