"""직접 해보기 06 · 두 관측소의 떨림 겹쳐 보기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:
  python3 analysis.py                         # 논문 조건(H를 6.9 ms 앞당기고 부호 반전)과 네 가지 비교
  python3 analysis.py --check                 # 책의 예상 결과와 비교
  python3 analysis.py --shift 7.4 --start 0.30 --end 0.45    # 조건 바꾸기
  python3 analysis.py --no-flip               # 부호를 뒤집지 않기
  python3 analysis.py --component 1           # NANOGrav 열 고르기(0 monopole · 1 dipole · 2 HD)
자료: GWOSC GW150914 그림 1 파형(Abbott et al. 2016, PRL 116, 061102) · NANOGrav 15년 교육용 요약(MIT 저장소).
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
FILES = ["fig1-observed-H.txt", "fig1-observed-L.txt", "pta_summary_ratios.csv"]
COMPONENTS = ["monopole", "dipole", "HD"]


def sha8(name):
    return hashlib.sha256((DATA / name).read_bytes()).hexdigest()[:8]


def wave(name):
    rows = []
    for ln in open(DATA / f"fig1-observed-{name}.txt"):
        if ln.startswith("#") or not ln.strip():
            continue
        t, v = ln.split()
        rows.append((float(t), float(v)))
    return rows


def interp(rows, t):
    """선형 보간. 파일 범위 밖은 끝값을 그대로 쓴다(책의 그림 계산과 같다)."""
    lo, hi = 0, len(rows) - 1
    if t <= rows[0][0]:
        return rows[0][1]
    if t >= rows[-1][0]:
        return rows[-1][1]
    while hi - lo > 1:
        m = (lo + hi) // 2
        if rows[m][0] <= t:
            lo = m
        else:
            hi = m
    (ta, va), (tb, vb) = rows[lo], rows[hi]
    return va + (vb - va) * (t - ta) / (tb - ta)


def corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return sab / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def pearson(H, L, shift_ms=6.9, flip=True, start=0.30, end=0.45):
    """L의 각 시각 t에서 H(t + shift)를 (부호를 곱해) 비교한다. shift>0이면 H를 앞당긴 것."""
    sel = [(t, v) for t, v in L if start <= t <= end]
    sign = -1.0 if flip else 1.0
    h = [sign * interp(H, t + shift_ms / 1000.0) for t, _ in sel]
    return corr(h, [v for _, v in sel]), len(sel)


def best_shift(H, L, flip=True, start=0.30, end=0.45, lo=-15.0, hi=15.0, step=0.2):
    n = round((hi - lo) / step)
    best = max(((pearson(H, L, lo + i * step, flip, start, end)[0], lo + i * step) for i in range(n + 1)))
    return best[1], best[0]


def pta():
    with open(DATA / "pta_summary_ratios.csv", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        next(r)
        return [[float(c) for c in row[1:4]] for row in r]


def quantile(vals, p):
    """NumPy 기본(선형) 백분위와 같다."""
    s = sorted(vals)
    x = (len(s) - 1) * p
    i = int(math.floor(x))
    return s[i] + (x - i) * (s[min(i + 1, len(s) - 1)] - s[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shift", type=float, default=6.9, help="H를 앞당기는 양(ms)")
    ap.add_argument("--no-flip", action="store_true", help="H의 부호를 뒤집지 않는다")
    ap.add_argument("--start", type=float, default=0.30)
    ap.add_argument("--end", type=float, default=0.45)
    ap.add_argument("--component", type=int, default=2, choices=(0, 1, 2))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    H, L = wave("H"), wave("L")
    print("파일 지문:", " · ".join(f"{n} {sha8(n)}" for n in FILES))
    print(f"H {len(H):,}행 · L {len(L):,}행 · 시각 {L[0][0]:.4f}–{L[-1][0]:.4f} s")
    r, n = pearson(H, L, a.shift, not a.no_flip, a.start, a.end)
    print(f"조건: H {a.shift:.1f} ms 앞당김 · 부호 {'유지' if a.no_flip else '반전'} · 구간 {a.start:.2f}–{a.end:.2f} s ({n:,}행) → r = {r:+.3f}")
    bs, br = best_shift(H, L, not a.no_flip, a.start, a.end)
    print(f"이 구간·부호에서 0.2 ms 간격으로 훑은 최고 상관: 이동 {bs:.1f} ms · r = {br:+.3f}")
    ratios = pta()
    col = [r_[a.component] for r_ in ratios]
    q = [quantile(col, p) for p in (.16, .5, .84)]
    print(f"NANOGrav {COMPONENTS[a.component]} 열 {len(col):,}행: 중앙값 {q[1]:.2f} · 16–84 백분위 {q[0]:.2f}–{q[2]:.2f}")

    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        ok = True
        tol = exp["tolerance"]
        paper = pearson(H, L, 6.9, True)[0]
        flip_only = pearson(H, L, 0, True)[0]
        nothing = pearson(H, L, 0, False)[0]
        wide = pearson(H, L, 6.9, True, 0.25, 0.46)[0]
        bsh, _ = best_shift(H, L)
        hd = [x[2] for x in ratios]
        hq = [quantile(hd, p) for p in (.16, .5, .84)]
        rows = [
            ("논문 조건 r", paper, exp["r_paper"], tol, 3),
            ("부호만 반전 r", flip_only, exp["r_flip_only"], exp["tolerance_2digit"], 2),
            ("이동·반전 없음 r", nothing, exp["r_nothing"], exp["tolerance_2digit"], 2),
            ("구간 0.25–0.46 s로 넓힘 r", wide, exp["r_wide"], tol, 3),
            ("상관이 가장 큰 이동량 (ms)", bsh, exp["best_shift_ms"], 0.05, 1),
            ("NANOGrav HD 중앙값", hq[1], exp["pta_hd"]["median"], 0.005, 2),
            ("NANOGrav HD 16 백분위", hq[0], exp["pta_hd"]["p16"], 0.005, 2),
            ("NANOGrav HD 84 백분위", hq[2], exp["pta_hd"]["p84"], 0.005, 2),
        ]
        for label, mine, book, t, d in rows:
            same = abs(mine - book) <= t
            ok &= same
            print(f"[{'같음' if same else '다름'}] {label}: 당신 {mine:.{d}f} / 책 {book:.{d}f}")
        for k, v in exp["sha256_8"].items():
            same = sha8(k) == v
            ok &= same
            print(f"[{'같음' if same else '다름'}] 파일 지문 {k}: {sha8(k)} / {v}")
        print("모두 같다." if ok else "다른 값이 있다. H를 앞당겼는지(+), 파일 첫 줄 설명을 건너뛰었는지, 지문을 먼저 확인하자.")


if __name__ == "__main__":
    main()
