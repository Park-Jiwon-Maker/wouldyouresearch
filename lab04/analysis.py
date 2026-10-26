"""직접 해보기 04 · 표범 무늬의 원소 세기 — 같은 계산을 Python으로.

표준 라이브러리만 쓴다. 실행:  python3 analysis.py                      (결과 출력)
                               python3 analysis.py --check              (책의 예상 결과와 비교)
                               python3 analysis.py --oxide NiO --region cores   (조건 바꾸기)
                               python3 analysis.py --build              (브라우저용 data/points.csv 다시 만들기)
자료: NASA PDS 지구과학 노드, 퍼서비어런스 PIXL, sol 1188 체야바 폭포, doi:10.17189/vth5-0676 (미국 정부 공공 자료).
"""
import argparse
import csv
import hashlib
import json
import math
import statistics as st
from pathlib import Path

HERE = Path(__file__).parent
D = HERE / "data"
OXIDE = "ps__1188_0772445544_000rqc__05410104308341770000___j01.csv"
BEAM = "pe__1188_0772443549_000rxl__05410104308341770003___j02.csv"
ROI = {"matrix": "sol_01188_cheyava_falls_matrix_without_fe_phosphate_pmc.csv",
       "rims": "sol_01188_cheyava_falls_leopard_spot_rims_and_poppy_seeds_pmc.csv",
       "cores": "sol_01188_cheyava_falls_leopard_spot_cores_pmc.csv"}
REGIONS = {"rims": "테두리·양귀비씨", "cores": "반점 속", "band": "띠 전체", "matrix": "바탕(인산철 없는 이암)"}
OXIDES = ["Na2O", "MgO", "Al2O3", "SiO2", "P2O5", "SO3", "Cl", "K2O", "CaO", "TiO2", "Cr2O3", "MnO", "FeO-T", "NiO", "ZnO", "Br"]


def sha8(name):
    return hashlib.sha256((D / name).read_bytes()).hexdigest()[:8]


def load():
    """산화물 표(PMC별)와 구역 목록. 구역 목록에는 머리줄이 없으므로 첫 줄도 PMC 번호다."""
    with open(D / OXIDE, encoding="utf-8") as f:
        ox = {int(r["PMC"]): r for r in csv.DictReader(f)}
    roi = {}
    for k, name in ROI.items():
        roi[k] = [int(l.split(",")[0]) for l in open(D / name, encoding="utf-8") if l.strip()[:1].isdigit()]
    roi["band"] = list(ox)
    return ox, roi


def mean_se(ox, pmcs, oxide):
    a = [float(ox[p][f"{oxide}_wt%"]) for p in pmcs]
    return st.mean(a), st.stdev(a) / math.sqrt(len(a)), len(a)


def enrichment(ox, roi, region, oxide):
    """구역 평균 ÷ 바탕 평균, 그리고 표준오차를 전파한 범위."""
    v, se, n = mean_se(ox, roi[region], oxide)
    b, bse, nb = mean_se(ox, roi["matrix"], oxide)
    r = v / b
    return {"mean": v, "n": n, "base": b, "nbase": nb, "ratio": r, "err": r * math.sqrt((se / v) ** 2 + (bse / b) ** 2)}


def build_points():
    """측정 띠를 긴 방향으로 돌려 mm 좌표(u, v)를 만들고, 점마다 구역·산화물 값을 한 표로 묶는다."""
    ox, roi = load()
    bm = {int(r["PMC"]): (float(r["x"]) * 1000, float(r["y"]) * 1000) for r in csv.DictReader(open(D / BEAM, encoding="utf-8"))}
    pts = [p for p in ox if p in bm]
    mx, my = st.mean(bm[p][0] for p in pts), st.mean(bm[p][1] for p in pts)
    sxx = sum((bm[p][0] - mx) ** 2 for p in pts)
    syy = sum((bm[p][1] - my) ** 2 for p in pts)
    sxy = sum((bm[p][0] - mx) * (bm[p][1] - my) for p in pts)
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    c, s = math.cos(th), math.sin(th)
    uv = {p: ((bm[p][0] - mx) * c + (bm[p][1] - my) * s, -(bm[p][0] - mx) * s + (bm[p][1] - my) * c) for p in pts}
    u0, v0 = min(a for a, _ in uv.values()), min(b for _, b in uv.values())
    grp = {}
    for k in ("matrix", "rims", "cores"):
        for p in roi[k]:
            grp[p] = k
    with open(D / "points.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["PMC", "u_mm", "v_mm", "group"] + OXIDES)
        for p in ox:
            u, v = uv.get(p, (u0, v0))
            w.writerow([p, f"{u - u0:.3f}", f"{v - v0:.3f}", grp.get(p, "none")] + [ox[p][f"{o}_wt%"] for o in OXIDES])
    print(f"data/points.csv {len(ox)}행 · sha256 {sha8('points.csv')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oxide", default="P2O5", choices=OXIDES)
    ap.add_argument("--region", default="rims", choices=["rims", "cores", "band"])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.build:
        build_points()
        return
    ox, roi = load()
    print("파일 지문(sha256 앞 8자리):", " · ".join(f"{n.split('_')[0]} {sha8(n)}" for n in (OXIDE, BEAM, *ROI.values())))
    print("점 수:", " · ".join(f"{REGIONS[k]} {len(v):,}" for k, v in roi.items()))
    e = enrichment(ox, roi, a.region, a.oxide)
    print(f"{REGIONS[a.region]} {a.oxide}: {e['mean']:.2f}% ÷ 바탕 {e['base']:.2f}% = {e['ratio']:.2f}배 (±{e['err']:.2f})")
    if a.check:
        exp = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
        ok = True
        for row in exp["rows"]:
            e = enrichment(ox, roi, row["region"], row["oxide"])
            mine = e["ratio"] if row["kind"] == "ratio" else e["mean"] if row["kind"] == "mean" else e["base"]
            same = abs(mine - row["value"]) <= exp["tolerance"]
            ok &= same
            print(f"[{'같음' if same else '다름'}] {row['label']}: 당신 {mine:.2f} / 책 {row['value']:.2f}")
        for k, n in exp["counts"].items():
            same = len(roi[k]) == n
            ok &= same
            print(f"[{'같음' if same else '다름'}] {REGIONS[k]} 점 수: 당신 {len(roi[k]):,} / 책 {n:,}")
        for n, h in exp["sha256_8"].items():
            same = sha8(n) == h
            ok &= same
            print(f"[{'같음' if same else '다름'}] 파일 지문 {n[:12]}…: 당신 {sha8(n)} / 기대 {h}")
        print("모두 같다." if ok else "다른 값이 있다. 파일 지문(sha256)과 구역 목록 첫 줄(머리줄 없음)을 먼저 확인하자.")


if __name__ == "__main__":
    main()
