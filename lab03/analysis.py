"""직접 해보기 03 · 33분에서 β까지 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py           (결과 출력)
                               python3 analysis.py --check   (책의 예상 결과와 비교)
                               python3 analysis.py --rho 3000 --p-post 11.4 --a 1.2   (조건 바꾸기)
자료: Cheng 외(2023) Nature 616:457 확장 자료 표 1, Thomas 외(2023) Nature 616:448 — 논문에 공개된 표의 값.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
CSV = HERE / "data" / "dart_published_values.csv"


def sha8():
    return hashlib.sha256(CSV.read_bytes()).hexdigest()[:8]


def load():
    with open(CSV, encoding="utf-8") as f:
        return {r["symbol"]: float(r["value"]) for r in csv.DictReader(f)}


def dot(x, y):
    return sum(a * b for a, b in zip(x, y))


def compute(v, rho=2400.0, p_post=None, a=None, use_paper_dv=True):
    """주기 변화 → 공전 속도 → Δv → 부피·질량 → β (Cheng 외 2023 식 2)."""
    P0 = v["P_pre"]
    P1 = v["P_post"] if p_post is None else p_post
    a_km = v["a"] if a is None else a
    U = [v["U_x"], v["U_y"], v["U_z"]]
    E = [v["E_x"], v["E_y"], v["E_z"]]
    eT = [v["eT_x"], v["eT_y"], v["eT_z"]]
    dP_min = (P1 - P0) * 60
    vorb = 2 * math.pi * a_km * 1e3 / (P0 * 3600)          # m/s
    dv_mine = vorb * (P1 - P0) / (3 * P0)                    # m/s, ΔP/P = 3Δv/v
    V = math.pi / 6 * v["B_x"] * v["B_y"] * v["B_z"]
    dvT = v["dv_T"] * 1e-3 if use_paper_dv else dv_mine

    def beta(r, d=dvT):
        return 1 + ((r * V / v["m"]) * d - dot(U, eT) * 1e3) / ((dot(E, U) * 1e3) * dot(E, eT))

    return {"dP_min": dP_min, "v_cm_s": vorb * 100, "dv_mm_s": dv_mine * 1e3,
            "volume_m3": V, "mass_kg": rho * V, "beta": beta(rho), "beta_fn": beta,
            "beta1_dv_mm_s": v["m"] * dot(U, eT) * 1e3 / (rho * V) * 1e3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rho", type=float, default=2400.0, help="가정한 밀도(kg/m³)")
    ap.add_argument("--p-post", type=float, default=None, help="충돌 뒤 주기(시간), 기본 11.372")
    ap.add_argument("--a", type=float, default=None, help="궤도 반지름(km), 기본 1.206")
    ap.add_argument("--own-dv", action="store_true", help="β에 논문의 Δv(−2.70) 대신 내가 구한 Δv를 쓴다")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    v = load()
    r = compute(v, a.rho, a.p_post, a.a, not a.own_dv)
    print(f"파일 지문 dart_published_values.csv sha256 {sha8()}")
    print(f"주기 변화 ΔP = {r['dP_min']:.1f} 분 (논문 −33.0±1.0)")
    print(f"공전 속도 v = {r['v_cm_s']:.1f} cm/s")
    print(f"속도 변화 Δv = {r['dv_mm_s']:.2f} mm/s (논문 −2.70±0.10)")
    print(f"부피 {r['volume_m3']:.3e} m³, 밀도 {a.rho:g}일 때 질량 {r['mass_kg']:.2e} kg")
    print(f"β = {r['beta']:.2f}   (β=1이었다면 Δv = {r['beta1_dv_mm_s']:.2f} mm/s)")
    for rho in (1500, 2400, 3300):
        print(f"밀도 {rho} kg/m³ → β = {r['beta_fn'](rho):.2f}")
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        d = compute(v)  # 책의 기본 조건
        tol = exp["tolerance"]
        rows = [("주기 변화(분)", d["dP_min"], exp["dP_min"], tol["dP_min"]),
                ("공전 속도(cm/s)", d["v_cm_s"], exp["v_cm_s"], tol["v_cm_s"]),
                ("Δv(mm/s)", d["dv_mm_s"], exp["dv_mm_s"], tol["dv_mm_s"])]
        rows += [(f"β(밀도 {k})", d["beta_fn"](float(k)), b, tol["beta"]) for k, b in exp["beta"].items()]
        ok = sha8() == exp["sha256_8"]
        print(f"[{'같음' if ok else '다름'}] 파일 지문: 당신 {sha8()} / 책 {exp['sha256_8']}")
        for name, mine, book, t in rows:
            same = abs(mine - book) <= t
            ok &= same
            print(f"[{'같음' if same else '다름'}] {name}: 당신 {mine:.2f} / 책 {book:.2f}")
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문(sha256)과 조건(--rho, --p-post, --a)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
