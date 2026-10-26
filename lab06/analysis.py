"""직접 해보기 04 · 이산화탄소의 봉우리 재기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py                         (네 처리 결과 비교)
                               python3 analysis.py --check                 (책의 예상 결과와 비교)
                               python3 analysis.py --feature 4.3 4.4       (특징 구간 좁히기)
                               python3 analysis.py --compare 5.0 5.3       (비교 구간 옮기기)
                               python3 analysis.py --keep-flagged          (TIBERIUS 불량 픽셀 표시 점도 포함)
자료: JWST Transiting Exoplanet Community ERS Team, WASP-39 b 첫 관측 네 처리 결과, Zenodo 10.5281/zenodo.6959427 (CC BY 4.0).
같은 통과를 네 팀이 각자 처리한 것이다. 통과 깊이를 ppm으로 바꾼 것 말고는 손대지 않았다.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
FILE = HERE / "data" / "wasp39b_spectra.csv"
PIPES = ("FIREFLY", "TSHIRT", "TIBERIUS", "EUREKA")


def load():
    with open(FILE, newline="") as f:
        return [{"pipe": r["pipeline"], "w": float(r["wavelength_um"]), "d": float(r["depth_ppm"]),
                 "flag": float(r["flag"] or 0)} for r in csv.DictReader(f)]


def sha8():
    return hashlib.sha256(FILE.read_bytes()).hexdigest()[:8]


def summarize(rows, pipe, feature=(4.2, 4.5), compare=(3.6, 3.9), keep_flagged=False):
    """한 처리 결과에서 두 구간 [시작, 끝)의 점 수·산술평균, 평균의 차이, 가장 깊은 점의 파장을 구한다."""
    pts = [r for r in rows if r["pipe"] == pipe and (keep_flagged or r["flag"] == 0)]

    def band(b):
        v = [r["d"] for r in pts if b[0] <= r["w"] < b[1]]     # 시작 포함, 끝 제외
        if not v:
            raise ValueError(f"구간 {b}에 점이 없다")
        return len(v), sum(v) / len(v)

    na, ma = band(feature)
    nb, mb = band(compare)
    deepest = max(pts, key=lambda r: r["d"])
    return {"points": len(pts), "n_feature": na, "mean_feature": ma, "n_compare": nb, "mean_compare": mb,
            "diff": ma - mb, "deepest_um": deepest["w"], "deepest_ppm": deepest["d"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature", type=float, nargs=2, default=(4.2, 4.5), metavar=("LO", "HI"))
    ap.add_argument("--compare", type=float, nargs=2, default=(3.6, 3.9), metavar=("LO", "HI"))
    ap.add_argument("--keep-flagged", action="store_true", help="TIBERIUS의 불량 픽셀 표시(flag≠0) 점도 쓴다")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows = load()
    print(f"wasp39b_spectra.csv sha256 {sha8()} | 특징 구간 [{a.feature[0]:g}, {a.feature[1]:g}) · 비교 구간 [{a.compare[0]:g}, {a.compare[1]:g}) μm"
          f"{' · 표시 점 포함' if a.keep_flagged else ''}")
    res = {}
    for p in PIPES:
        r = summarize(rows, p, tuple(a.feature), tuple(a.compare), a.keep_flagged)
        res[p] = r
        print(f"{p:<9} {r['points']:>3}점 | 가장 깊은 점 {r['deepest_um']:.3f}μm | 특징 {r['n_feature']}점 평균 {r['mean_feature']:,.1f} · 비교 {r['n_compare']}점 평균 {r['mean_compare']:,.1f} | 차이 {r['diff']:,.1f} ppm")
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        base = {p: summarize(rows, p) for p in PIPES}
        ok = sha8() == exp["sha256_8"]
        print(f"[{'같음' if ok else '다름'}] 파일 지문: 당신 {sha8()} / 기대 {exp['sha256_8']}")
        for p in PIPES:
            for key, tol, lab, unit in (("deepest_um", exp["tolerance_um"], "가장 깊은 점의 파장", "μm"),
                                        ("diff", exp["tolerance_ppm"], "두 구간 평균의 차이", "ppm")):
                book = exp[key][p]
                mine = base[p][key]
                same = abs(mine - book) <= tol
                ok &= same
                print(f"[{'같음' if same else '다름'}] {p} {lab}: 당신 {mine:,.3f} / 책 {book:,} {unit}")
            same = base[p]["points"] == exp["points"][p]
            ok &= same
            print(f"[{'같음' if same else '다름'}] {p} 쓴 점 수: 당신 {base[p]['points']} / 책 {exp['points'][p]}")
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문(sha256), 구간 경계 규칙([시작, 끝))과 TIBERIUS 표지 제외를 먼저 확인하자.")


if __name__ == "__main__":
    main()
