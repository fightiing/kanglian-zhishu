from __future__ import annotations
from typing import List, Dict, Any
import math


def _enrich_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """丰富 block 信息"""
    out = []
    for b in blocks:
        x1, y1, x2, y2 = b["bbox"]
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        w = x2 - x1
        h = y2 - y1
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        b2 = dict(b)
        b2.update({"bbox": [x1, y1, x2, y2], "cx": cx, "cy": cy, "w": w, "h": h})
        out.append(b2)
    return out


def _kmeans_1d(xs: List[float], k: int, iters: int = 30) -> tuple[List[int], List[float]]:
    """1维 KMeans 聚类"""
    n = len(xs)
    xs_sorted = sorted(xs)
    centers = []
    for i in range(k):
        q = (i + 0.5) / k
        idx = int(q * (n - 1))
        centers.append(xs_sorted[idx])

    labels = [0] * n
    for _ in range(iters):
        changed = False
        for i, x in enumerate(xs):
            best = 0
            best_d = abs(x - centers[0])
            for j in range(1, k):
                d = abs(x - centers[j])
                if d < best_d:
                    best_d = d
                    best = j
            if labels[i] != best:
                labels[i] = best
                changed = True

        new_centers = [0.0] * k
        counts = [0] * k
        for lab, x in zip(labels, xs):
            new_centers[lab] += x
            counts[lab] += 1
        for j in range(k):
            if counts[j] > 0:
                new_centers[j] /= counts[j]
            else:
                new_centers[j] = xs_sorted[int((j + 0.5) / k * (n - 1))]
        centers = new_centers
        if not changed:
            break

    return labels, centers


def _score_clustering(xs: List[float], labels: List[int], centers: List[float]) -> float:
    """聚类质量评分"""
    n = len(xs)
    k = len(centers)
    if n == 0:
        return -1e9
    mean = sum(xs) / n
    within = 0.0
    counts = [0] * k
    for x, lab in zip(xs, labels):
        within += (x - centers[lab]) ** 2
        counts[lab] += 1
    between = 0.0
    for j in range(k):
        if counts[j] > 0:
            between += counts[j] * (centers[j] - mean) ** 2
    penalty = 1.0 + 0.35 * (k - 1)
    return (between / (within + 1e-6)) / penalty


def _choose_k(xs: List[float], max_k: int = 4, min_pts_per_col: int = 2) -> tuple[int, List[int], List[float]]:
    """自动选择最佳列数"""
    n = len(xs)
    if n < min_pts_per_col * 2:
        labs, c = _kmeans_1d(xs, 1)
        return 1, labs, c

    best = (1, None, None, -1e9)
    for k in range(1, max_k + 1):
        labs, centers = _kmeans_1d(xs, k)
        counts = [0] * k
        for lab in labs:
            counts[lab] += 1
        if k > 1 and min(counts) < min_pts_per_col:
            continue
        if k > 1:
            cs = sorted(centers)
            min_gap = min(abs(cs[i + 1] - cs[i]) for i in range(len(cs) - 1))
            if min_gap < 0.10 * (max(xs) - min(xs) + 1e-6):
                continue

        sc = _score_clustering(xs, labs, centers)
        if sc > best[3]:
            best = (k, labs, centers, sc)

    if best[1] is None:
        labs, c = _kmeans_1d(xs, 1)
        return 1, labs, c
    return best[0], best[1], best[2]


def sort_blocks_reading_order(
    blocks: List[Dict[str, Any]],
    img_w: int | None = None,
    img_h: int | None = None,
    max_cols: int = 4,
) -> List[Dict[str, Any]]:
    """
    YOLO blocks 排序（鲁棒）
    - 自动判断列数：1..max_cols
    - 1列：按 y->x
    - 多列：左列读完 -> 右列
    """
    if not blocks:
        return []

    blocks = _enrich_blocks(blocks)

    # 推断 img_w（如果没传）
    if img_w is None:
        img_w = int(max(b["bbox"][2] for b in blocks) + 1)

    # 过滤 abandon / 极小块
    clean = []
    for b in blocks:
        if str(b.get("type", "")).lower() in ("abandon", "ignored", "ignore"):
            continue
        x1, y1, x2, y2 = b["bbox"]
        if (x2 - x1) < 20 or (y2 - y1) < 18:
            continue
        clean.append(b)
    blocks = clean
    if not blocks:
        return []

    # title / header 先单独拉出来
    top_types = {"title", "header"}
    top_blocks = [b for b in blocks if str(b.get("type", "")).lower() in top_types]
    main_blocks = [b for b in blocks if b not in top_blocks]

    top_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))

    if not main_blocks:
        return top_blocks

    # 使用y坐标作为主要排序依据，确保从上到下的顺序
    # 先按行分组
    row_gap = img_h * 0.02 if img_h else 40
    rows = []
    
    for block in main_blocks:
        placed = False
        for row in rows:
            # 如果block的y中心与行平均y接近，加入该行
            row_mean_y = sum(b["cy"] for b in row) / len(row)
            if abs(block["cy"] - row_mean_y) < row_gap:
                row.append(block)
                placed = True
                break
        if not placed:
            rows.append([block])
    
    # 对每行按x排序
    for row in rows:
        row.sort(key=lambda b: b["cx"])
    
    # 按行的y坐标排序
    rows.sort(key=lambda r: sum(b["cy"] for b in r) / len(r))
    
    # 合并所有blocks
    ordered = []
    ordered.extend(top_blocks)
    for row in rows:
        ordered.extend(row)
    
    return ordered