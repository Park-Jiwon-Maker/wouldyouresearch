# 직접 해보기 09 · 341개 목록에서 표본을 직접 고르기

- 브라우저: `index.html` (설치 없음)
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--mag-limit 27`, `--method spec`
- 노트북: `notebook.ipynb`
- 자료: `data/catalog.csv` — Kocevski 외(2025), ApJ 986, 126, doi:10.3847/1538-4357/adbc7d. 저자 저장소 github.com/dalekocevski/Kocevski24 커밋 b47c187의 Table 3를 CSV로 옮긴 것(행·값 변경 없음). 원본은 `data/Kocevski24.Table3.dat`(SHA-256 27372eee…711de). 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 무작위 표본이 아니다. zflag는 적색편이를 잰 방법일 뿐 블랙홀 확인 여부가 아니다. 학술지 PDF는 zflag 표기(1=광도, 2=분광)가 저장소판(0=광도, 1=분광)과 다르다. 개수 분포를 시대별 실제 천체 수로 읽지 않는다.
