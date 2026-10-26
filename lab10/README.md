# 직접 해보기 10 · 우주의 자로 팽창률 재기

- 브라우저: `index.html` (설치 없음)
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--h0 71.4 --rd 140`, `--om 0.35`, `--scan-om`
- 노트북: `notebook.ipynb`
- 자료: `data/mean.txt`, `data/cov.txt` — DESI DR2 BAO 거리비 13개와 13×13 공분산. DESI Collaboration, Phys. Rev. D 112, 083515 (2025), doi:10.1103/tr6y-kpc6. CobayaSampler/bao_data 커밋 b7b8a36, CC BY 4.0, 원본 그대로. `data/bao.csv`는 같은 값에 오차(공분산 대각 원소의 제곱근)를 붙인 것. 처리 내역·감사문은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 모형은 평탄 ΛCDM 교육용 계산이다. χ²는 이 조건에서의 어긋남 요약일 뿐 모형이 참일 확률이 아니며, 93.3은 z=0.51의 팽창률이지 오늘의 허블 상수가 아니다. BAO만으로는 H₀와 rd를 따로 정할 수 없다.
