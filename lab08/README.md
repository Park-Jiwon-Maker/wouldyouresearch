# 직접 해보기 08 · 두 관측소의 떨림 겹쳐 보기

- 브라우저: `index.html` (설치 없음) — H를 앞당기는 양 슬라이더, 부호 뒤집기, 비교 구간, NANOGrav 막대 수
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--shift 7.4 --no-flip --start 0.40 --end 0.43 --component 1`
- 노트북: `notebook.ipynb`
- 자료: `data/fig1-observed-H.txt`, `fig1-observed-L.txt` — GWOSC(LIGO Scientific Collaboration · Virgo Collaboration), Abbott 외 (2016) PRL 116, 061102 그림 1의 필터 처리 파형. `data/pta_summary_ratios.csv` — NANOGrav 15년 교육용 요약(MIT 저장소 고정 판본)의 A/A_err. 원본 그대로이며 출처·처리·한계는 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 필터를 거친 그림용 자료다. 새 시간차를 쟀다고, 신호가 진짜일 확률이나 질량을 구했다고 쓸 수 없다. NANOGrav의 값/오차는 검출 시그마가 아니다.
