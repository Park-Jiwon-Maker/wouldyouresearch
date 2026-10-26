"""직접 해보기 08 · 우주의 자로 팽창률 재기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py            (기본: H0=68, rd=147, Ωm=0.30)
                               python3 analysis.py --check    (책의 예상 결과와 비교)
                               python3 analysis.py --h0 71.4 --rd 140        (조건 바꾸기)
                               python3 analysis.py --om 0.35
                               python3 analysis.py --scan-om                 (Ωm을 0.25–0.35에서 훑기)
자료: DESI Collaboration, DESI DR2 Results II, PRD 112, 083515 (2025), doi:10.1103/tr6y-kpc6.
      CobayaSampler/bao_data 커밋 b7b8a36 (mean.txt, cov.txt 원본 그대로) · CC BY 4.0.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
C_KMS = 299792.458


def load_bao():
    with open(HERE / "data" / "bao.csv", encoding="utf-8-sig") as f:
        return [dict(z=float(r["z"]), v=float(r["value"]), q=r["quantity"], s=float(r["sigma"])) for r in csv.DictReader(f)]


def load_cov():
    return [[float(x) for x in line.split()] for line in (HERE / "data" / "cov.txt").read_text().splitlines() if line.strip()]


def sha8(name):
    return hashlib.sha256((HERE / "data" / name).read_bytes()).hexdigest()[:8]


def E(z, om):
    """평탄한 우주에서 H(z)/H0."""
    return math.sqrt(om * (1 + z) ** 3 + 1 - om)


def integral(z, om, n=400):
    """∫0^z dz'/E(z') — 심프슨 법칙."""
    if z <= 0:
        return 0.0
    h = z / n
    return h / 3 * sum((1 if i in (0, n) else 4 if i % 2 else 2) / E(i * h, om) for i in range(n + 1))


def model(q, z, om=0.30, h0=68.0, rd=147.0):
    s = C_KMS / (h0 * rd)
    dm, dh = s * integral(z, om), s / E(z, om)
    return {"DM_over_rs": dm, "DH_over_rs": dh, "DV_over_rs": (z * dm * dm * dh) ** (1 / 3)}[q]


def solve(a, b):
    """가우스 소거법으로 a·x = b를 푼다(부분 피벗)."""
    n = len(b)
    m = [a[i][:] + [b[i]] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[p] = m[p], m[i]
        for r in range(i + 1, n):
            f = m[r][i] / m[i][i]
            for c in range(i, n + 1):
                m[r][c] -= f * m[i][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (m[i][n] - sum(m[i][c] * x[c] for c in range(i + 1, n))) / m[i][i]
    return x


def chi2(rows, cov, om=0.30, h0=68.0, rd=147.0):
    """χ² = dᵀ C⁻¹ d,  d = 관측 − 모형. 13×13 공분산 전체를 쓴다."""
    d = [r["v"] - model(r["q"], r["z"], om, h0, rd) for r in rows]
    return sum(a * b for a, b in zip(d, solve(cov, d)))


def hubble_at(rows, z, rd):
    """DH/rd 줄에서 H(z) = c / (DH/rd × rd)와 오차(rd 고정, 대각 원소만)."""
    r = next(r for r in rows if r["q"] == "DH_over_rs" and abs(r["z"] - z) < 1e-9)
    h = C_KMS / (r["v"] * rd)
    return h, h * r["s"] / r["v"], r["v"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h0", type=float, default=68.0)
    ap.add_argument("--rd", type=float, default=147.0)
    ap.add_argument("--om", type=float, default=0.30)
    ap.add_argument("--scan-om", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows, cov = load_bao(), load_cov()
    print(f"파일 지문  mean.txt {sha8('mean.txt')} · cov.txt {sha8('cov.txt')} · bao.csv {sha8('bao.csv')}")
    h, e, ratio = hubble_at(rows, 0.51, a.rd)
    print(f"z=0.510  DH/rd = {ratio:.3f}  →  H(z) = {h:.1f} ± {e:.1f} km/s/Mpc  (rd={a.rd:g})")
    print(f"H0={a.h0:g} rd={a.rd:g} Ωm={a.om:g}:  χ² = {chi2(rows, cov, a.om, a.h0, a.rd):.1f}  (자료 13개)")
    if a.scan_om:
        best = None
        for k in range(25, 36):
            om = k / 100
            c = chi2(rows, cov, om, a.h0, a.rd)
            best = min(best or (c, om), (c, om))
            print(f"  Ωm {om:.2f}  χ² {c:.1f}")
        print(f"  가장 작은 곳: Ωm = {best[1]:.2f} (χ² {best[0]:.1f}) — 이 계산 조건 안에서만 그렇다.")
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        ok = True
        def line(label, mine, book, tol):
            nonlocal ok
            same = abs(mine - book) <= tol
            ok &= same
            print(f"[{'같음' if same else '다름'}] {label}: 당신 {mine:.2f} / 책 {book:.2f}")
        for rd, (hb, eb) in ((147.0, exp["H_0510"]["147"]), (140.0, exp["H_0510"]["140"])):
            hh, ee, _ = hubble_at(rows, 0.51, rd)
            line(f"H(0.51) rd={rd:g}", hh, hb, exp["tolerance_H"])
            line(f"  오차 rd={rd:g}", ee, eb, exp["tolerance_H"])
        line("χ² (H0 68, rd 147, Ωm 0.30)", chi2(rows, cov, 0.30, 68.0, 147.0), exp["chi2"]["68_147_0.30"], exp["tolerance_chi2"])
        line("χ² (H0 71.4, rd 140, Ωm 0.30)", chi2(rows, cov, 0.30, 71.4, 140.0), exp["chi2"]["71.4_140_0.30"], exp["tolerance_chi2"])
        line("χ² (H0 68, rd 147, Ωm 0.35)", chi2(rows, cov, 0.35, 68.0, 147.0), exp["chi2"]["68_147_0.35"], exp["tolerance_chi2"])
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문과 조건(--h0, --rd, --om), 빛의 속도 단위(km/s)를 먼저 확인하자.")


if __name__ == "__main__":
    main()
