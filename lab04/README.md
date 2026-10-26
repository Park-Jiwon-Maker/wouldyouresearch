# 직접 해보기 04 · 표범 무늬의 원소 세기

- 브라우저: `index.html` (설치 없음) — 산화물과 구역을 골라 바탕 대비 배수를 다시 계산한다.
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--oxide NiO --region cores`
- 노트북: `notebook.ipynb`
- 자료: `data/` — NASA PDS 지구과학 노드, 퍼서비어런스 PIXL sol 1188(2024-06-23) 체야바 폭포, doi:10.17189/vth5-0676 (미국 정부 공공 자료). 산화물 표·빔 위치 표·구역 목록 3개. `points.csv`는 브라우저용으로 합친 파생 파일(`python3 analysis.py --build`). 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 점 평균이다. 논문 보충 자료(CC BY-NC-ND)의 값은 보정이 달라 조금 다르며 이 폴더에 넣지 않았다. 원소가 몰렸다는 것만으로 광물을, 더구나 생명을 말할 수 없다.
