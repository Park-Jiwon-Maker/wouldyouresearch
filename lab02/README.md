# 직접 해보기 02 · 달의 두 얼굴, 지각 두께로 비교하기

- 브라우저: `index.html` (설치 없음)
- Python: `python3 analysis.py` · 책과 비교 `python3 analysis.py --check` · 조건 바꾸기 `--lat 30`, `--no-weight`
- 노트북: `notebook.ipynb`
- 자료: `data/lunar_crust_2deg.csv` — Wieczorek 외 (2013), GRAIL Crustal Thickness Archive v1, Zenodo doi:10.5281/zenodo.997347. 0.25° 원본에서 2° 간격 칸 중심 값을 보간 없이 고른 16,200행. 처리 내역은 `data/provenance.json`.
- 예상 결과: `expected.json`
- 주의: 중력과 지형에 밀도 등의 가정을 더해 계산한 **모형**이다. 두 모형은 같은 중력 자료에서 나왔으므로 독립된 두 관측이 아니다. 평균은 지역 차이를 가린다.
