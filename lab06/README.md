# 직접 해보기 06 · 이산화탄소의 봉우리 재기

- 브라우저: `index.html` (설치 없음)
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--feature 4.3 4.4`, `--compare 5.0 5.3`, `--keep-flagged`
- 노트북: `notebook.ipynb`
- 자료: `data/wasp39b_spectra.csv` — JWST Transiting Exoplanet Community ERS Team (2022), Zenodo doi:10.5281/zenodo.6959427, CC BY 4.0. 한 번의 관측을 네 팀(FIREFLY·TSHIRT·TIBERIUS·EUREKA)이 처리한 결과. 통과 깊이와 오차에 10⁶을 곱해 ppm으로 바꿈. 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 같은 관측의 네 처리이므로 합쳐서 오차를 줄일 수 없다. 구간 평균의 차이는 검출의 통계적 강도나 이산화탄소의 양이 아니다.
