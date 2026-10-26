"""직접 해보기 07 · 341개 목록에서 표본을 직접 고르기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py            (기본: mag444 < 26.5)
                               python3 analysis.py --check    (책의 예상 결과와 비교)
                               python3 analysis.py --mag-limit 27   (조건 바꾸기)
                               python3 analysis.py --method spec    (분광 적색편이만)
자료: Kocevski 외 (2025) ApJ 986, 126 · 저자 저장소 github.com/dalekocevski/Kocevski24 (커밋 b47c187) Table 3.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
BINS = range(2, 12)  # 적색편이 구간 [z, z+1)


def load():
    with open(HERE / "data" / "catalog.csv", encoding="utf-8-sig") as f:
        return [dict(survey=r["survey"], z=float(r["zbest"]), flag=int(r["zflag"]), mag=float(r["mag444"])) for r in csv.DictReader(f)]


def sha8(name="catalog.csv"):
    return hashlib.sha256((HERE / "data" / name).read_bytes()).hexdigest()[:8]


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def select(rows, limit, method="all"):
    """mag444 < limit (같다는 포함하지 않는다). method='spec'이면 분광 적색편이(zflag=1)만."""
    return [r for r in rows if r["mag"] < limit and (method == "all" or r["flag"] == 1)]


def summarize(rows, limit=26.5, method="all"):
    kept = select(rows, limit, method)
    base = [r for r in rows if method == "all" or r["flag"] == 1]
    ids = {id(r) for r in kept}
    dropped = [r for r in base if id(r) not in ids]
    per_bin = {}
    for b in BINS:
        a = sum(1 for r in base if int(r["z"]) == b)
        k = sum(1 for r in kept if int(r["z"]) == b)
        per_bin[b] = {"all": a, "kept": k, "pct": round(100 * k / a) if a else None}
    return {
        "denominator": len(base),
        "kept": len(kept),
        "kept_spec": sum(1 for r in kept if r["flag"] == 1),
        "dropped": len(dropped),
        "median_all": median([r["z"] for r in base]),
        "median_kept": median([r["z"] for r in kept]) if kept else None,
        "median_dropped": median([r["z"] for r in dropped]) if dropped else None,
        "per_bin": per_bin,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mag-limit", type=float, default=26.5)
    ap.add_argument("--method", choices=("all", "spec"), default="all")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows = load()
    print(f"catalog.csv sha256 {sha8()} · {len(rows)}행 · 분광 {sum(r['flag'] for r in rows)}개")
    s = summarize(rows, a.mag_limit, a.method)
    print(f"조건 mag444 < {a.mag_limit:g} ({'분광만' if a.method == 'spec' else '전체'}) : 분모 {s['denominator']} → 남음 {s['kept']} (그중 분광 {s['kept_spec']}), 빠짐 {s['dropped']}")
    f = lambda v: "—" if v is None else f"{v:.2f}"
    print(f"적색편이 중앙값: 전체 {f(s['median_all'])} / 남은 것 {f(s['median_kept'])} / 빠진 것 {f(s['median_dropped'])}")
    print("구간 z:  " + "  ".join(f"{b:>4}" for b in BINS))
    print("전체:    " + "  ".join(f"{s['per_bin'][b]['all']:>4}" for b in BINS))
    print("남음:    " + "  ".join(f"{s['per_bin'][b]['kept']:>4}" for b in BINS))
    print("비율 %:  " + "  ".join(f"{'—' if s['per_bin'][b]['pct'] is None else s['per_bin'][b]['pct']:>4}" for b in BINS))
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        ok = True
        def line(label, mine, book, tol=0):
            nonlocal ok
            same = abs(mine - book) <= tol
            ok &= same
            print(f"[{'같음' if same else '다름'}] {label}: 당신 {mine:g} / 책 {book:g}")
        r0 = summarize(rows, 26.5)
        line("전체 / 분광", len(rows), exp["total"]); line("분광 수", sum(r["flag"] for r in rows), exp["spec_total"])
        for lim, (n, sp) in exp["kept_by_limit"].items():
            s2 = summarize(rows, float(lim))
            line(f"mag444<{lim} 남은 수", s2["kept"], n); line(f"mag444<{lim} 그중 분광", s2["kept_spec"], sp)
        line("중앙값 전체", r0["median_all"], exp["median_z"]["all"], exp["tolerance"])
        line("중앙값 통과", r0["median_kept"], exp["median_z"]["kept"], exp["tolerance"])
        line("중앙값 빠짐", r0["median_dropped"], exp["median_z"]["dropped"], exp["tolerance"])
        line("z 5–6 남은 비율(%)", r0["per_bin"][5]["pct"], exp["pct_kept_by_bin"]["5"]); line("z 9–10 남은 비율(%)", r0["per_bin"][9]["pct"], exp["pct_kept_by_bin"]["9"])
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문(sha256)과 조건(--mag-limit, '<' 인지 '≤' 인지)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
