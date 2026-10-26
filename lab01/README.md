# 직접 해보기 01 · 경보선을 어디에 그을까

- 브라우저: `index.html` (설치 없음)
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--threshold 0.1` `--kind M --lead 2 --period recent`
- 노트북: `notebook.ipynb`
- 자료: `data/forecast_pairs.csv` — Camporeale (2025), Zenodo doi:10.5281/zenodo.16620803, CC BY 4.0. 발행일 1998–2024의 NOAA SWPC 플레어 확률 예보와 실제 기록을 실제 달력 날짜로 짝지은 58,814행. 브라우저용 집계 `forecast_counts.csv`, `persistence_counts.csv`는 이 표에서 센 것. 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 과거 예보의 교육용 재계산이다. 원 논문의 모든 점수를 재현한 것이 아니며 실시간 예보나 설비 운영의 근거로 쓸 수 없다.
