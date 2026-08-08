# 프로젝트 대장

만든 앱과 그 결과를 한 줄씩 남긴다. 회고는 짧게, 다음에 쓸 것만.

| 앱 | 시작 | 현재 단계 | 저장소 |
|---|---|---|---|
| 마켓 히트맵 | 2026-08 | 사이드로드 배포, Play 내부 테스트 준비 | [market-heatmap](https://github.com/jinhae8971/market-heatmap) |

---

## 마켓 히트맵

**무엇** 기능별 3개 탭 앱.
· 히트맵 — 한국·일본·유럽·미국·암호화폐 186종목 트리맵 (면적=USD 시총, 색=등락률)
· 반도체 — 밸류체인 6계층 34종목, 계층 로테이션, 상대평가 산점도, 메모리 점유율·영업이익률
· 트렌드 — 미국·한국·일본·대만 지수 + 금·은·WTI 13종, 금리역전 구간, USD 환산

**구조** GitHub Actions 수집 → 정적 JSON → Pages → WebView 셸 APK

**버전** 앱 셸 v1.1.0(versionCode 2) · 콘텐츠 v1.4.0 — [CHANGELOG](https://github.com/jinhae8971/market-heatmap/blob/main/CHANGELOG.md)

**하루 만에 어디까지** 웹 대시보드 → PWA → 서명 APK → Play용 AAB + 스토어 자산 → 기능 탭 3개

**배운 것** → [오답노트](../lessons/2026-08-08-market-heatmap.md)

**다음** Play 내부 테스트 업로드. 수익화는 데이터 라이선스 견적을 받은 뒤 판단.
