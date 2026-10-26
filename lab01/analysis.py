"""직접 해보기 01 · 경보선을 어디에 그을까 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py                              (X급 · 다음 날 · 전체 기간 · 경보선 50%)
                               python3 analysis.py --check                      (책의 예상 결과와 비교)
                               python3 analysis.py --threshold 0.1              (경보선 바꾸기)
                               python3 analysis.py --kind M --lead 2 --period recent   (급수 · 며칠 뒤 · 기간 바꾸기)
자료: Camporeale (2025) Zenodo 10.5281/zenodo.16620803 (CC BY 4.0) — NOAA SWPC 플레어 확률 예보와 실제 기록의 짝.
교육용 재계산이다. 원 논문의 모든 점수를 재현한 것이 아니며, 실시간 예보나 설비 운영의 근거로 쓸 수 없다.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
FILE = HERE / "data" / "forecast_pairs.csv"
PERIODS = {"all": (1998, 2024), "early": (1998, 2008), "middle": (2009, 2019), "recent": (2020, 2024)}


def sha8():
    return hashlib.sha256(FILE.read_bytes()).hexdigest()[:8]


def load():
    """각 행: 발행일(issue), 대상 날짜(target), 며칠 뒤(lead), 급수(kind), 확률(p, 0–1), 실제 발생(y, 0/1)."""
    with open(FILE, newline="") as f:
        return [(r["issue"], r["target"], int(r["lead"]), r["kind"], float(r["p"]), int(r["y"])) for r in csv.DictReader(f)]


def select(rows, kind="X", lead=1, period="all"):
    lo, hi = PERIODS[period]
    return [r for r in rows if r[3] == kind and r[2] == lead and lo <= int(r[0][:4]) <= hi]


def four_boxes(sel, threshold):
    """경보는 ‘확률 ≥ 경보선’일 때 울린다(같은 값 포함)."""
    tp = sum(1 for r in sel if r[4] >= threshold and r[5])
    fp = sum(1 for r in sel if r[4] >= threshold and not r[5])
    events = sum(r[5] for r in sel)
    return {"hit": tp, "false_alarm": fp, "miss": events - tp, "quiet": len(sel) - tp - fp - (events - tp)}


def reliability(sel, width=10):
    out = []
    for lo in range(0, 100, width):
        b = [r for r in sel if min(100 - width, int(round(r[4] * 100)) // width * width) == lo]
        if b:
            out.append({"lo": lo, "n": len(b), "mean_p": sum(r[4] for r in b) / len(b), "rate": sum(r[5] for r in b) / len(b)})
    return out


def persistence(rows, kind="X", period="all"):
    """‘어제(대상 날짜의 달력상 하루 전) 있었으면 오늘도 있다’는 지속 예보. 하루 전 기록이 없는 날은 뺀다."""
    lo, hi = PERIODS[period]
    pairs = [r for r in rows if r[3] == kind and r[2] == 1]
    by_target = {r[1]: r[5] for r in pairs}
    box = {"hit": 0, "false_alarm": 0, "miss": 0, "quiet": 0, "n": 0}
    for r in pairs:
        if not lo <= int(r[0][:4]) <= hi:
            continue
        prev = (dt.date.fromisoformat(r[1]) - dt.timedelta(days=1)).isoformat()
        if prev not in by_target:
            continue
        f, y = by_target[prev], r[5]
        box["hit" if f and y else "false_alarm" if f else "miss" if y else "quiet"] += 1
        box["n"] += 1
    return box


def summary(sel, threshold, width=10):
    n = len(sel)
    events = sum(r[5] for r in sel)
    box = four_boxes(sel, threshold)
    return {
        "n": n, "events": events,
        "always_no_accuracy_pct": (n - events) / n * 100 if n else None,
        "brier": sum((r[4] - r[5]) ** 2 for r in sel) / n if n else None,
        "days_at_or_above": box["hit"] + box["false_alarm"],
        "box": box, "bins": reliability(sel, width),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["M", "X"], default="X")
    ap.add_argument("--lead", type=int, choices=[1, 2, 3], default=1, help="예보가 말하는 날: 발행 다음 날=1")
    ap.add_argument("--period", choices=list(PERIODS), default="all", help="발행일 기준: all 1998–2024, early 1998–2008, middle 2009–2019, recent 2020–2024")
    ap.add_argument("--threshold", type=float, default=0.5, help="경보선(0–1). 확률 ≥ 이 값이면 경보")
    ap.add_argument("--width", type=int, choices=[10, 20], default=10)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not 0 <= a.threshold <= 1:
        ap.error("--threshold 는 0–1")
    rows = load()
    print(f"파일 지문 sha256 forecast_pairs.csv {sha8()}")
    sel = select(rows, a.kind, a.lead, a.period)
    s = summary(sel, a.threshold, a.width)
    b = s["box"]
    print(f"{a.kind}급 · {a.lead}일 뒤 · {a.period}({PERIODS[a.period][0]}–{PERIODS[a.period][1]}) · {s['n']:,}일, 실제 발생 {s['events']:,}일")
    print(f"경보선 {a.threshold * 100:g}%: 맞힌 날 {b['hit']:,} · 괜히 울린 날 {b['false_alarm']:,} · 놓친 날 {b['miss']:,} · 조용히 맞힌 날 {b['quiet']:,}")
    print(f"늘 ‘없음’이라고만 말하면 정답률 {s['always_no_accuracy_pct']:.1f}%, 그래도 발생한 {s['events']:,}일은 모두 놓친다. 브라이어 점수 {s['brier']:.4f}(같은 자료에서만 비교)")
    print("교정 곡선 (묶음: 예보 평균 → 실제 비율, 날짜 수):")
    for r in s["bins"]:
        print(f"  {r['lo']:>2}–{r['lo'] + a.width - 1:<2}%  {r['mean_p'] * 100:5.1f}% → {r['rate'] * 100:5.1f}%   n={r['n']:,}")
    if a.lead == 1:
        p = persistence(rows, a.kind, a.period)
        print(f"지속 예보(어제 있었으면 오늘도): 맞힌 날 {p['hit']:,} · 괜히 울린 날 {p['false_alarm']:,} · 놓친 날 {p['miss']:,} ({p['n']:,}일)")

    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        X = select(rows, "X", 1, "all")
        ok = True

        def line(label, mine, book):
            nonlocal ok
            same = mine == book
            ok &= same
            fm = (lambda v: f"{v:,}") if isinstance(mine, int) else str
            print(f"[{'같음' if same else '다름'}] {label}: 당신 {fm(mine)} / 책 {fm(book)}")
        line("짝의 수(일)", len(X), exp["n"])
        line("X급 발생일", sum(r[5] for r in X), exp["events"])
        line("늘 ‘없음’ 정답률(%, 소수 첫째)", round((len(X) - exp["events"]) / len(X) * 100, 1), exp["always_no_accuracy_pct"])
        line("X급 확률 50% 이상인 날", sum(1 for r in X if r[4] >= .5), exp["days_at_or_above_50"])
        line("확률이 정확히 50%인 날", sum(1 for r in X if r[4] == .5), exp["days_exactly_50"])
        for key, th in (("threshold_50", .5), ("threshold_10", .1)):
            bx = four_boxes(X, th)
            for k, label in (("hit", "맞힌 날"), ("false_alarm", "괜히 울린 날"), ("miss", "놓친 날"), ("quiet", "조용히 맞힌 날")):
                line(f"경보선 {int(th * 100)}% {label}", bx[k], exp[key][k])
        pb = persistence(rows, "X", "all")
        for k, label in (("hit", "맞힌 날"), ("false_alarm", "괜히 울린 날"), ("miss", "놓친 날")):
            line(f"지속 예보 {label}", pb[k], exp["persistence"][k])
        line("파일 지문", sha8(), exp["sha256_8"]["forecast_pairs.csv"])
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문과 조건(--kind, --lead, --period, --threshold)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
