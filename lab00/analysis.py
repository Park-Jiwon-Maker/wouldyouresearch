"""직접 해보기 00 · 연구 동향을 다시 계산하기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py                         (책에 나온 네 항목)
                               python3 analysis.py --check                 (책의 예상 결과와 비교)
                               python3 analysis.py --topic lrd             (주제 하나)
                               python3 analysis.py --early 2022 2023 --recent 2024 2025   (연도 묶음 바꾸기)
                               python3 analysis.py --denominator all       (분모를 공학 포함으로)
자료: OpenAlex 논문 기록 집계(2026-10-22 동결본). 연도별 건수와 분모는 data/ 에 있다.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
YEARS = ("2021", "2022", "2023", "2024", "2025")
BOOK_TOPICS = ("exoplanet_atmosphere", "gravitational_wave", "lrd")


def read(name):
    with open(HERE / "data" / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sha8(name):
    return hashlib.sha256((HERE / "data" / name).read_bytes()).hexdigest()[:8]


def denominator(den_rows, years, kind):
    """kind: 'science'(과학 19개 주제군) / 'all'(공학 포함)."""
    return sum(int(r[kind]) for r in den_rows if r["year"] in years)


def trend(topic, den_rows, early, recent, den="auto"):
    """두 기간의 건수 합, 증가율(%), 전체 분모, 비중(%)과 변화(퍼센트포인트)."""
    kind = (("all" if topic["corpus"] == "all24" else "science") if den == "auto" else den)
    e = sum(int(topic[y]) for y in early)
    r = sum(int(topic[y]) for y in recent)
    de, dr = denominator(den_rows, early, kind), denominator(den_rows, recent, kind)
    return {
        "id": topic["id"], "label": topic["label_ko"], "denominator": kind,
        "early": e, "recent": r,
        "growth_pct": (r / e - 1) * 100 if e else None,
        "den_early": de, "den_recent": dr, "den_growth_pct": (dr / de - 1) * 100,
        "share_early_pct": e / de * 100, "share_recent_pct": r / dr * 100,
        "share_change_pp": r / dr * 100 - e / de * 100,
        "yearly": [int(topic[y]) for y in YEARS],
    }


def show(t):
    g = "계산 불가(기준 0건)" if t["growth_pct"] is None else f"{t['growth_pct']:+.1f}%"
    print(f"{t['label']:<22} {t['early']:>6,} → {t['recent']:>6,}건 ({g})  "
          f"비중 {t['share_early_pct']:.2f}% → {t['share_recent_pct']:.2f}% ({t['share_change_pp']:+.2f}%p)  분모 {t['denominator']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", help="주제 id(예: lrd). 생략하면 책에 나온 항목")
    ap.add_argument("--early", nargs="+", default=["2021", "2022"])
    ap.add_argument("--recent", nargs="+", default=["2024", "2025"])
    ap.add_argument("--denominator", choices=["auto", "science", "all"], default="auto")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    topics = {r["id"]: r for r in read("keyword_metrics.csv")}
    den_rows = read("denominators.csv")
    print(f"파일 지문 sha256 keyword_metrics.csv {sha8('keyword_metrics.csv')} · denominators.csv {sha8('denominators.csv')}")
    ids = [a.topic] if a.topic else list(BOOK_TOPICS)
    res = {i: trend(topics[i], den_rows, a.early, a.recent, a.denominator) for i in ids}
    first = res[ids[0]]
    print(f"전체 분모({first['denominator']}): {first['den_early']:,}건 → {first['den_recent']:,}건 ({first['den_growth_pct']:+.1f}%)")
    for t in res.values():
        show(t)
        if t["early"] == 0:
            print("   연도별 건수:", ", ".join(map(str, t["yearly"])))
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        base = {i: trend(topics[i], den_rows, ["2021", "2022"], ["2024", "2025"], "science") for i in BOOK_TOPICS}
        ok = True

        def line(label, mine, book, tol, d=2):
            nonlocal ok
            same = abs(mine - book) <= tol
            ok &= same
            print(f"[{'같음' if same else '다름'}] {label}: 당신 {mine:,.{d}f} / 책 {book:,.{d}f}")
        b = base["lrd"]
        line("전체 2021–22 합", b["den_early"], exp["baseline"]["early"], 0, 0)
        line("전체 2024–25 합", b["den_recent"], exp["baseline"]["recent"], 0, 0)
        line("전체 증가율(%)", b["den_growth_pct"], exp["baseline"]["growth_pct"], exp["tolerance_pct"], 1)
        for k, v in exp["topics"].items():
            t = base[k]
            line(f"{t['label']} 2021–22 건수", t["early"], v["early"], 0, 0)
            line(f"{t['label']} 2024–25 건수", t["recent"], v["recent"], 0, 0)
            if v["growth_pct"] is not None:
                line(f"{t['label']} 증가율(%)", t["growth_pct"], v["growth_pct"], exp["tolerance_pct"], 1)
            line(f"{t['label']} 비중 2021–22(%)", t["share_early_pct"], v["share_early_pct"], exp["tolerance_share"])
            line(f"{t['label']} 비중 2024–25(%)", t["share_recent_pct"], v["share_recent_pct"], exp["tolerance_share"])
        yr = base["lrd"]["yearly"]
        same = yr == exp["topics"]["lrd"]["yearly"]
        ok &= same
        print(f"[{'같음' if same else '다름'}] 작은 붉은 점 연도별 건수: 당신 {yr} / 책 {exp['topics']['lrd']['yearly']}")
        for k, v in exp["sha256_8"].items():
            same = sha8(k) == v
            ok &= same
            print(f"[{'같음' if same else '다름'}] 파일 지문 {k}: {sha8(k)} / {v}")
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문과 조건(--early, --recent, --denominator)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
