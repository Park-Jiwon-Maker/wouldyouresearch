"""직접 해보기 03 · 인산염의 지문 찾기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py           (결과 출력)
                               python3 analysis.py --check   (책의 예상 결과와 비교)
                               python3 analysis.py --window 2 --range 110 200   (조건 바꾸기)
자료: Klenner, Postberg, Sekine (2023) Zenodo 10.5281/zenodo.7703848 (CC BY 4.0) — 지상 LILBID 실험 스펙트럼.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
SOLUTIONS = {"mix": "Na₂HPO₄ + Na₃PO₄ 혼합액", "tri": "Na₃PO₄ 0.1M", "di": "Na₂HPO₄ 0.1M", "phosphite": "인산염 + 아인산염 혼합액"}
MARKS = (125, 165, 187)


def load(name):
    with open(HERE / "data" / f"{name}.csv") as f:
        r = csv.reader(f)
        next(r)
        return [(float(m), float(v)) for m, v in r]


def sha8(name):
    return hashlib.sha256((HERE / "data" / f"{name}.csv").read_bytes()).hexdigest()[:8]


def analyse(rows, window=1.0, lo=20.0, hi=210.0):
    """구간 [lo, hi] 안에서 가장 높은 신호를 1로 다시 맞추고, 각 명목 질량 ±window 안의 최고점을 찾는다."""
    sel = [(m, v) for m, v in rows if lo <= m <= hi]
    top_m, top_v = max(sel, key=lambda r: r[1])
    out = {"top_mz": round(top_m, 2), "peaks": {}}
    for c in MARKS:
        w = [(m, v / top_v) for m, v in sel if abs(m - c) <= window]
        if w:
            m, v = max(w, key=lambda r: r[1])
            out["peaks"][str(c)] = {"mz": round(m, 2), "height": round(v, 3)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=1.0)
    ap.add_argument("--range", type=float, nargs=2, default=(20.0, 210.0))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    res = {}
    for k, label in SOLUTIONS.items():
        r = analyse(load(k), a.window, *a.range)
        res[k] = r
        pk = "  ".join(f"{c}: {p['mz']:.2f} / {p['height']:.3f}" for c, p in r["peaks"].items())
        print(f"{label:<24} sha256 {sha8(k)}  최고점 m/z {r['top_mz']:.2f}  |  {pk}")
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        ok = True
        for k, v in exp["height_187"].items():
            mine = res[k]["peaks"]["187"]["height"]
            same = abs(mine - v) <= exp["tolerance"]
            ok &= same
            print(f"[{'같음' if same else '다름'}] {SOLUTIONS[k]} 187 높이: 당신 {mine:.3f} / 책 {v:.3f}")
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문(sha256)과 조건(--window, --range)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
