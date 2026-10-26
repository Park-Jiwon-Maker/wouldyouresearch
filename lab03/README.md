# 직접 해보기 03 · 33분에서 β까지

- 브라우저: `index.html` (설치 없음) · 밀도·충돌 뒤 주기·궤도 반지름을 바꿔 Δv와 β를 다시 계산
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--rho 3000 --p-post 11.4 --a 1.2 --own-dv`
- 노트북: `notebook.ipynb`
- 자료: `data/dart_published_values.csv` — Cheng 외(2023) Nature 616:457 확장 자료 표 1(doi:10.1038/s41586-023-05878-z), Thomas 외(2023) Nature 616:448(doi:10.1038/s41586-023-05805-2)에 공개된 표의 값. 가공 없음. 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 관측 원자료가 아니라 논문 표의 숫자다. 디모르포스의 밀도는 측정값이 아니라 가정이므로 β는 하나의 수가 아니라 밀도의 함수다. 내 계산(3.50)과 논문의 몬테카를로 중앙값(3.61)은 다를 수 있다.
