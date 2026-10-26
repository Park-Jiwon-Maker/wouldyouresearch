# 직접 해보기 07 · 펄서 후보 분류기 시험하기

- 브라우저: `index.html` (설치 없음) — 문턱 슬라이더로 남김·놓침·잘못 남김, 재현율·정밀도·정확도를 본다
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 다른 문턱 `--threshold 0.5` · 처음부터 `--retrain`(NumPy)
- 노트북: `notebook.ipynb`
- 자료: `data/HTRU_2.csv` — HTRU2, Lyon 외 HTRU 공동연구진(파크스), UCI doi:10.24432/C5DK6R, CC BY 4.0. 원본 그대로. 파생: `scores.csv`(묶음·정답·점수), `model.json`(학습 결과). 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 행은 천체가 아니라 후보이고 같은 펄서가 여러 행에 있을 수 있다. 시험 성적은 이 표 안에서의 성적이며 새 펄서를 찾는 능력이 아니다.
