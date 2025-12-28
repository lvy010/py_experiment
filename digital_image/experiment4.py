"""
数字图像处理实验四：
1) “train” 图像：Sobel 锐化，不同系数对比。
2) “lajiao” 图像：FFT 分解幅值谱、相位谱，用幅值+相位重构。
3) “xiaochou” 图像：自动陷波滤波器去除周期噪声。
生成结果和报告输出到 output/ 目录。
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, Tuple

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
  <title>数字图像处理实验四</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#f8fafc; color:#1f2937; padding:24px; }}
    h1 {{ margin-bottom:6px; }}
    h3 {{ margin:12px 0 6px 0; }}
  </style>
</head>
<body>
  <h1>数字图像处理实验四</h1>
  <p style="color:#6b7280;">Sobel 锐化、FFT 幅相重构、陷波滤波</p>
  {''.join(sections.values())}
</body>
</html>
"""
    (OUT_DIR / "report_exp4.html").write_text(html, encoding="utf-8")


# ========== 卷积与滤波 ==========
def convolve(gray: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    pad_y, pad_x = kernel.shape[0] // 2, kernel.shape[1] // 2
    padded = np.pad(gray, ((pad_y, pad_y), (pad_x, pad_x)), mode="reflect")
    windows = sliding_window_view(padded, kernel.shape)
    out = np.einsum("ij,xyij->xy", kernel, windows)
    return np.clip(out, 0, 255).astype(np.uint8)


def sobel_sharpen(gray: np.ndarray, alpha: float) -> np.ndarray:
    gx_k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    gy_k = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)
    gx = convolve(gray, gx_k)
    gy = convolve(gray, gy_k)
    mag = np.hypot(gx.astype(np.float32), gy.astype(np.float32))
    mag = mag / (mag.max() + 1e-6) * 255.0
    sharpened = np.clip(gray.astype(np.float32) + alpha * mag, 0, 255)
    return sharpened.astype(np.uint8)


# ========== FFT 幅相分解与重构 ==========
def fft_decompose(gray: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    mag = np.abs(fshift)
    phase = np.angle(fshift)
    mag_vis = (np.log1p(mag) / np.log1p(mag).max() * 255).astype(np.uint8)
    phase_vis = ((phase + np.pi) / (2 * np.pi) * 255).astype(np.uint8)
    return mag, phase, np.stack([mag_vis, phase_vis], axis=0)


def fft_reconstruct(mag: np.ndarray, phase: np.ndarray) -> np.ndarray:
    f = mag * np.exp(1j * phase)
    img = np.fft.ifft2(np.fft.ifftshift(f))
    img = np.clip(np.real(img), 0, 255)
    return img.astype(np.uint8)


# ========== 自动陷波滤波 ==========
def build_notch_mask(mag: np.ndarray, num_peaks: int = 4, radius: int = 5, exclude_r: int = 15) -> np.ndarray:
    h, w = mag.shape
    cy, cx = h // 2, w // 2
    mask = np.ones_like(mag, dtype=np.float32)
    mag_work = mag.copy()
    yy, xx = np.ogrid[:h, :w]
    center_mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= exclude_r ** 2
    mag_work[center_mask] = 0

    for _ in range(num_peaks):
        idx = np.argmax(mag_work)
        y, x = np.unravel_index(idx, mag_work.shape)
        if mag_work[y, x] == 0:
            break
        for (py, px) in [(y, x), (h - y, w - x)]:
            rr = (yy - py) ** 2 + (xx - px) ** 2
            mask[rr <= radius ** 2] = 0
            mag_work[rr <= radius ** 2] = 0
    return mask


def notch_filter(gray: np.ndarray, num_peaks: int = 4, radius: int = 5, exclude_r: int = 15) -> np.ndarray:
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    mag = np.abs(fshift)
    phase = np.angle(fshift)
    mask = build_notch_mask(mag, num_peaks=num_peaks, radius=radius, exclude_r=exclude_r)
    f_filtered = fshift * mask
    img = np.fft.ifft2(np.fft.ifftshift(f_filtered))
    img = np.clip(np.real(img), 0, 255)
    return img.astype(np.uint8), (mask * 255).astype(np.uint8)


# ========== 主流程 ==========
def main() -> None:
    sections: Dict[str, str] = {}

    # 1) train Sobel 锐化
    train = to_gray(IMG_DIR / "train.jpg")
    alphas = [0.4, 0.8, 1.2]
    sobel_imgs: Dict[str, Path] = {"原图": save_array(train, "train_orig.png")}
    for a in alphas:
        sobel_imgs[f"Sobel锐化 α={a}"] = save_array(sobel_sharpen(train, a), f"train_sobel_{a}.png")
    sections["sobel"] = add_section("train：Sobel 锐化参数对比", sobel_imgs)

    # 2) lajiao 幅值/相位分解与重构
    lajiao = to_gray(IMG_DIR / "lajiao.jpg")
    mag, phase, vis = fft_decompose(lajiao)
    mag_img = save_array(vis[0], "lajiao_mag.png")
    phase_img = save_array(vis[1], "lajiao_phase.png")
    recon_img = save_array(fft_reconstruct(mag, phase), "lajiao_recon.png")
    sections["fft"] = add_section("lajiao：FFT 幅值谱 / 相位谱 / 重构", {
        "原图": save_array(lajiao, "lajiao_orig.png"),
        "幅值谱(log)": mag_img,
        "相位谱": phase_img,
        "幅值+相位重构": recon_img,
    })

    # 3) xiaochou 自动陷波滤波
    xiaochou = to_gray(IMG_DIR / "xiaochou.jpg")
    notch_img, mask_vis = notch_filter(xiaochou, num_peaks=4, radius=6, exclude_r=12)
    notch_imgs = {
        "原图": save_array(xiaochou, "xiaochou_orig.png"),
        "陷波掩膜": save_array(mask_vis, "xiaochou_notch_mask.png"),
        "陷波滤波结果": save_array(notch_img, "xiaochou_notch.png"),
    }
    sections["notch"] = add_section("xiaochou：陷波滤波去除周期噪声", notch_imgs)

    build_report(sections)
    print(f"输出完成：{OUT_DIR / 'report_exp4.html'}")


if __name__ == "__main__":
    main()

