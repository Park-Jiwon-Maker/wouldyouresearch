# 직접 해보기 05 · 인산염의 지문 찾기

- 브라우저: `index.html` (설치 없음)
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--window 2 --range 110 200`
- 노트북: `notebook.ipynb`
- 자료: `data/*.csv` — Klenner, Postberg, Sekine (2023), Zenodo doi:10.5281/zenodo.7703848, CC BY 4.0. 원본 TXT에서 20≤m/z≤210만 골라 구간 최댓값으로 나눈 값. 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 지상 실험 자료다. 봉우리 하나로 물질을 단정하거나, 높이로 양을 말하거나, 우주에서 새로 발견했다고 쓸 수 없다.
