"""직접 해보기 02 · 달의 두 얼굴, 지각 두께로 비교하기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py                    (결과 출력)
                               python3 analysis.py --check            (책의 예상 결과와 비교)
                               python3 analysis.py --lat 30           (위도 ±30°만)
                               python3 analysis.py --no-weight        (넓이 가중치 없이 단순 평균)
자료: Wieczorek 외 (2013) GRAIL 지각 두께 모형, Zenodo 10.5281/zenodo.997347 — 계산으로 얻은 모형이며 직접 관측값이 아니다.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
FILE = HERE / "data" / "lunar_crust_2deg.csv"


def load():
    with open(FILE) as f:
        r = csv.reader(f)
        next(r)
        return [(float(a), float(b), float(c), float(d)) for a, b, c, d in r]


def sha8():
    return hashlib.sha256(FILE.read_bytes()).hexdigest()[:8]


def is_near(lon, edge=90.0):
    """경도 -edge ~ +edge(양끝 포함)를 앞면으로 둔다. 이 격자의 경도는 홀수라 경계에 걸리는 칸이 없다."""
    return -edge <= lon <= edge


def hemisphere_means(rows, model=1, lat=90.0, weight=True, edge=90.0):
    """위도 |φ| ≤ lat 인 칸만 모아 앞면·뒷면의 (넓이 가중) 평균 두께와 차이를 구한다."""
    acc = {"near": [0.0, 0.0, 0], "far": [0.0, 0.0, 0]}
    col = 2 if model == 1 else 3
    for row in rows:
        la, lo = row[0], row[1]
        if abs(la) > lat:
            continue
        w = math.cos(math.radians(la)) if weight else 1.0
        a = acc["near" if is_near(lo, edge) else "far"]
        a[0] += w * row[col]
        a[1] += w
        a[2] += 1
    near, far = acc["near"][0] / acc["near"][1], acc["far"][0] / acc["far"][1]
    return {"near": near, "far": far, "diff": far - near, "cells": [acc["near"][2], acc["far"][2]]}


def thin_far_share(rows, model=1, edge=90.0):
    """뒷면 넓이 중 두께가 앞면 평균보다 얇은 칸이 차지하는 비율(전 위도, 넓이 가중)."""
    near = hemisphere_means(rows, model, 90, True, edge)["near"]
    col = 2 if model == 1 else 3
    tot = thin = 0.0
    for row in rows:
        if is_near(row[1], edge):
            continue
        w = math.cos(math.radians(row[0]))
        tot += w
        if row[col] < near:
            thin += w
    return thin / tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, default=90.0, help="이 위도 이내(±)의 칸만 쓴다 (기본 90)")
    ap.add_argument("--no-weight", action="store_true", help="cos(위도) 가중치를 쓰지 않고 칸마다 같은 무게로 평균")
    ap.add_argument("--edge", type=float, default=90.0, help="앞면 경계 경도(±, 기본 90)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows = load()
    print(f"lunar_crust_2deg.csv  sha256 {sha8()}  {len(rows):,}행  | 위도 ±{a.lat:g}° · {'단순 평균' if a.no_weight else 'cos 위도 가중'} · 앞면 경도 ±{a.edge:g}°")
    res = {}
    for m in (1, 3):
        r = hemisphere_means(rows, m, a.lat, not a.no_weight, a.edge)
        res[m] = r
        print(f"모형 {m}: 앞 {r['near']:.2f} · 뒤 {r['far']:.2f} · 차 {r['diff']:.2f} km   (칸 수 앞 {r['cells'][0]:,} / 뒤 {r['cells'][1]:,})")
    print(f"모형 1에서 앞면 평균보다 얇은 뒷면 넓이: {thin_far_share(rows, 1, a.edge) * 100:.1f}%")
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        tol = exp["tolerance_km"]
        ok = sha8() == exp["sha256_8"]
        print(f"[{'같음' if ok else '다름'}] 파일 지문: 당신 {sha8()} / 기대 {exp['sha256_8']}")
        for key, val in exp["all_lat"].items():
            m, k = int(key[1]), key[3:]
            mine = hemisphere_means(rows, m, 90)[k]
            same = abs(mine - val) <= tol
            ok &= same
            print(f"[{'같음' if same else '다름'}] 전 위도 모형 {m} {k}: 당신 {mine:.2f} / 책 {val:.2f} km")
        for key, val in exp["lat30_diff"].items():
            m = int(key[1])
            mine = hemisphere_means(rows, m, 30)["diff"]
            same = abs(mine - val) <= tol
            ok &= same
            print(f"[{'같음' if same else '다름'}] 위도 ±30° 모형 {m} 차이: 당신 {mine:.2f} / 책 {val:.2f} km")
        mine = thin_far_share(rows, 1)
        same = abs(mine - exp["thin_far_share_m1"]) <= exp["tolerance_share"]
        ok &= same
        print(f"[{'같음' if same else '다름'}] 모형 1, 앞면 평균보다 얇은 뒷면 넓이: 당신 {mine:.3f} / 책 약 {exp['thin_far_share_m1']:.2f}")
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문(sha256)과 조건(--lat, --no-weight, --edge)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
