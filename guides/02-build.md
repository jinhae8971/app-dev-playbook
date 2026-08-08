# 02. 빌드 — APK와 AAB

*최종 확인: 2026-08-08 · 직접 수행함*

## Android Studio를 꼭 써야 하나

아니다. 의존성이 적은 앱이라면 SDK 도구를 직접 부르는 게 훨씬 빠르다.
액티비티 하나에 외부 라이브러리 0개인 앱을 Gradle 없이 빌드했고, 결과물은 21KB였다.

```
aapt2 compile → aapt2 link → javac → d8 → zipalign → apksigner
```

Gradle + AGP를 끌어오면 빌드 환경이 수백 MB로 불어나는데, 이런 앱에서는 얻는 게 없다.
반대로 AndroidX·Compose·외부 SDK(AdMob, Billing)를 쓰기 시작하면
의존성 해결이 필요해지므로 그때는 Gradle이 맞다.

**기준: 외부 의존성이 생기는 순간 Gradle로 간다.**

## APK vs AAB

| | APK | AAB |
|---|---|---|
| 용도 | 사이드로드(직접 배포) | Play Console 업로드 |
| 리소스 포맷 | 바이너리 | protobuf (`aapt2 link --proto-format`) |
| 폰에 직접 설치 | 가능 | 불가 |
| 서명 | 배포 키로 직접 | 업로드 키로만. 배포 서명은 Google이 |

AAB는 링크 단계에 `--proto-format`을 주고, 결과물을 bundletool이 요구하는
디렉터리 구조(`base/manifest`, `base/dex`, `base/res`, `base/resources.pb`)로
재배치한 뒤 `bundletool build-bundle`을 돌린다.

검증은 반대로 하면 된다 — `bundletool build-apks --mode=universal`로
설치 가능한 APK를 뽑아 `aapt2 dump badging`으로 확인.

## 키스토어 — 가장 중요한 파일

| 키 | 잃어버리면 |
|---|---|
| 사이드로드 배포 키 | 기존 사용자가 덮어쓰기 설치 불가. 삭제 후 재설치해야 함 |
| Play 업로드 키 | Play Console에서 재설정 요청 가능 (며칠 소요) |
| Play 배포 키 | Google이 보관하므로 내가 잃을 수 없음 |

**Play 앱 서명에 동의하면 최악의 경우가 크게 줄어든다.** 신규 앱은 기본으로 켜져 있다.

주의: 빌드 스크립트에 키스토어 비밀번호를 기본값으로 넣지 말 것. 저장소가
공개면 그대로 노출된다. 환경변수로만 받도록 한다.

```bash
KS_PASS="${KEYSTORE_PASS:?KEYSTORE_PASS 환경변수로 넘기세요}"
```

## targetSdk

Play는 신규 앱의 targetSdk 하한을 매년 올린다. **올리는 것 자체는 한 줄이지만,
동작이 바뀌는 게 문제다.** 예를 들어 targetSdk 35(Android 15)부터는
엣지투엣지가 강제되어, 인셋 처리를 안 하면 상단 UI가 상태바에 가려진다.

targetSdk를 올릴 때는 반드시 실기기에서 한 번 띄워 본다. 빌드가 통과하는 것과
화면이 멀쩡한 것은 다른 문제다.
