# 0002. Gradle 없이 SDK 도구로 직접 빌드한다

*2026-08-08 · 상태: 채택*

## 결정
`aapt2 → javac → d8 → zipalign → apksigner` 다섯 단계를 셸 스크립트로 직접 호출한다.

## 이유
액티비티 하나에 외부 의존성이 0개다. Gradle+AGP는 수백 MB와 수 분을 추가하는데
이 앱에서 얻는 게 없다.

## 대가
- 람다 desugaring 같은 AGP가 해 주던 처리를 직접 피해야 한다(익명 클래스 사용).
- 의존성 해결 기능이 없다.

## 재검토 조건
AndroidX·AdMob·Play Billing 등 외부 SDK를 도입하는 순간 Gradle로 전환한다.
