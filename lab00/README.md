# 직접 해보기 00 · 연구 동향을 다시 계산하기

- 브라우저: `index.html` (설치 없음)
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--topic lrd --early 2022 2023 --denominator all`
- 노트북: `notebook.ipynb`
- 자료: `data/*.csv` — OpenAlex(CC0)를 이 책의 검색식으로 집계한 표, 2026-10-22 동결본. 연도별 건수 열만 옮겼고 증가율·비중은 다시 계산한다. 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 제목·초록 검색에 걸린 기록 수의 변화다. 연구의 질이나 중요도의 변화가 아니다. 기준이 0건인 주제는 증가율을 쓰지 않는다.
