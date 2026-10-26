"""직접 해보기 05 · 펄서 후보 분류기 시험하기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:
  python3 analysis.py                         # 문턱 선택과 시험 결과
  python3 analysis.py --check                 # 책의 예상 결과와 비교
  python3 analysis.py --threshold 0.5         # 시험 묶음에 다른 문턱 적용(사후 탐색)
  python3 analysis.py --target-recall 0.95    # 검증 묶음 재현율 목표를 바꿔 문턱을 다시 고르기
  python3 analysis.py --retrain               # (NumPy 필요) 분할·학습부터 처음부터 다시 계산해 model.json과 대조

빠른 경로는 data/model.json에 담긴 학습 결과(평균·표준편차·가중치)와 data/scores.csv의 묶음 배정을
읽어 점수를 다시 계산한다. 4,000번 경사하강을 순수 Python으로 돌리면 몇 분이 걸리므로
처음부터의 재계산은 --retrain(NumPy)으로 따로 둔다.
자료: HTRU2 (Lyon et al.), UCI doi:10.24432/C5DK6R, CC BY 4.0.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
SEED = 20261023


def sha8(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def load_raw():
    X, y = [], []
    with open(DATA / "HTRU_2.csv") as f:
        for r in csv.reader(f):
            v = [float(c) for c in r]
            X.append(v[:8])
            y.append(int(v[8]))
    return X, y


def load_split():
    with open(DATA / "scores.csv") as f:
        r = csv.DictReader(f)
        return [row["split"] for row in r]


def sigmoid(z):
    z = max(-50.0, min(50.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def scores_from_model(X, model):
    mu, sd, w, b = model["mean"], model["std"], model["weights"], model["intercept"]
    return [sigmoid(sum(((x - m) / s) * wi for x, m, s, wi in zip(row, mu, sd, w)) + b) for row in X]


def confusion(y, s, split, name, t):
    tp = fp = fn = tn = 0
    for yi, si, sp in zip(y, s, split):
        if sp != name:
            continue
        keep = si >= t
        if yi:
            tp += keep
            fn += not keep
        else:
            fp += keep
            tn += not keep
    n = tp + fp + fn + tn
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "n": n, "kept": tp + fp,
            "recall": tp / (tp + fn), "precision": tp / (tp + fp) if tp + fp else None,
            "accuracy": (tp + tn) / n}


def pick_threshold(y, s, split, target=0.90):
    """검증 묶음에서 재현율이 목표 이상인 문턱(0.01 간격) 중 가장 높은 값."""
    ok = [k / 100 for k in range(1, 100) if confusion(y, s, split, "validation", k / 100)["recall"] >= target]
    return max(ok) if ok else 0.01


def retrain():
    import numpy as np
    a = np.loadtxt(DATA / "HTRU_2.csv", delimiter=",")
    X, y = a[:, :8], a[:, 8].astype(int)
    rng = np.random.default_rng(SEED)
    parts = [[], [], []]
    for c in (0, 1):
        ids = np.flatnonzero(y == c)
        rng.shuffle(ids)
        n = len(ids); n1 = int(n * .6); n2 = int(n * .2)
        for dst, p in zip(parts, (ids[:n1], ids[n1:n1 + n2], ids[n1 + n2:])):
            dst.extend(p)
    tr, va, te = [np.array(sorted(p)) for p in parts]
    mu, sd = X[tr].mean(0), X[tr].std(0)
    Z = (X - mu) / sd
    w, b = np.zeros(8), 0.0
    sig = lambda z: 1 / (1 + np.exp(-np.clip(z, -50, 50)))
    for _ in range(4000):
        e = sig(Z[tr] @ w + b) - y[tr]
        w -= .08 * (Z[tr].T @ e / len(tr) + .001 * w)
        b -= .08 * e.mean()
    s = sig(Z @ w + b)
    split = ["train"] * len(y)
    for ids, nm in ((va, "validation"), (te, "test")):
        for i in ids:
            split[i] = nm
    return {"mean": mu.tolist(), "std": sd.tolist(), "weights": w.tolist(), "intercept": float(b)}, list(map(float, s)), split


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, help="시험 묶음에 적용할 문턱(기본: 검증에서 고른 값)")
    ap.add_argument("--target-recall", type=float, default=0.90)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--retrain", action="store_true")
    a = ap.parse_args()

    model = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
    X, y = load_raw()
    split = load_split()
    s = scores_from_model(X, model)
    print(f"HTRU_2.csv sha256 {sha8(DATA / 'HTRU_2.csv')} · {len(y):,}행 · 펄서 {sum(y):,}행")
    counts = {nm: sum(1 for p in split if p == nm) for nm in ("train", "validation", "test")}
    print("묶음 행 수:", counts)

    if a.retrain:
        m2, s2, sp2 = retrain()
        same_split = sp2 == split
        dmax = max(abs(p - q) for p, q in zip(s, s2))
        print(f"[{'같음' if same_split else '다름'}] 60/20/20 분할(시작값 {SEED})이 scores.csv와 같다")
        print(f"[{'같음' if dmax < 1e-9 else '다름'}] 다시 학습한 점수와 model.json 점수의 최대 차이 {dmax:.2e}")

    t = pick_threshold(y, s, split, a.target_recall)
    print(f"검증에서 고른 문턱(재현율 ≥ {a.target_recall:.0%}인 가장 높은 값): {t:.2f}")
    v = confusion(y, s, split, "validation", t)
    print(f"검증  문턱 {t:.2f}: 남김 {v['tp']}/{v['tp'] + v['fn']} 재현율 {v['recall']:.1%}")
    tt = a.threshold if a.threshold is not None else t
    te = confusion(y, s, split, "test", tt)
    tag = "" if abs(tt - t) < 1e-9 else "  (사후 탐색)"
    print(f"시험  문턱 {tt:.2f}: 남김 {te['tp']}/{te['tp'] + te['fn']} 재현율 {te['recall']:.1%} · "
          f"정밀도 {te['precision']:.1%}({te['tp']}/{te['kept']}) · 정확도 {te['accuracy']:.1%} · 놓침 {te['fn']} · 잘못 남김 {te['fp']}{tag}")
    npos = te["tp"] + te["fn"]
    print(f"기준선(모두 ‘아님’): 시험 정확도 {(te['n'] - npos) / te['n']:.1%} · 재현율 0%")

    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        t16 = pick_threshold(y, s, split, 0.90)
        val = confusion(y, s, split, "validation", t16)
        tst = confusion(y, s, split, "test", t16)
        half = confusion(y, s, split, "test", 0.5)
        base = (tst["n"] - (tst["tp"] + tst["fn"])) / tst["n"]
        tol = exp["tolerance"]
        rows = [
            ("묶음 행 수 학습/검증/시험", f"{counts['train']}/{counts['validation']}/{counts['test']}", "/".join(map(str, exp["split_rows"]))),
            ("검증에서 고른 문턱", f"{t16:.2f}", f"{exp['threshold']:.2f}"),
            ("검증 재현율 (남긴/전체 펄서)", f"{val['tp']}/{val['tp'] + val['fn']}", f"{exp['validation_tp']}/{exp['validation_pos']}"),
            ("시험 남긴 펄서 / 전체 펄서", f"{tst['tp']}/{tst['tp'] + tst['fn']}", f"{exp['test_tp']}/{exp['test_pos']}"),
            ("시험 남긴 후보 중 펄서", f"{tst['tp']}/{tst['kept']}", f"{exp['test_tp']}/{exp['test_kept']}"),
            ("시험 재현율", f"{tst['recall']:.3f}", f"{exp['test_recall']:.3f}"),
            ("시험 정밀도", f"{tst['precision']:.3f}", f"{exp['test_precision']:.3f}"),
            ("시험 정확도", f"{tst['accuracy']:.3f}", f"{exp['test_accuracy']:.3f}"),
            ("모두 ‘아님’ 정확도", f"{base:.3f}", f"{exp['baseline_accuracy']:.3f}"),
            ("문턱 0.5: 남김/놓침/잘못 남김", f"{half['tp']}/{half['fn']}/{half['fp']}", "/".join(map(str, exp["test_at_0_5"]))),
        ]
        ok = True
        for label, mine, book in rows:
            same = mine == book
            ok &= same
            print(f"[{'같음' if same else '다름'}] {label}: 당신 {mine} / 책 {book}")
        fp = sha8(DATA / "HTRU_2.csv")
        same = fp == exp["sha256_8"]["HTRU_2.csv"]
        ok &= same
        print(f"[{'같음' if same else '다름'}] 파일 지문 HTRU_2.csv: {fp} / {exp['sha256_8']['HTRU_2.csv']}")
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문과 조건(--threshold, --target-recall)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
