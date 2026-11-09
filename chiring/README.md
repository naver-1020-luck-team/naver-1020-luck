# 친구방 · 주파수 (chiring)

팀 프로토타입에 붙이는 **친구방(Lucky Talk·Lucky Moments·스토리)**, **주파수(기운 선물)**, **받은 주파수 듣기** 화면이에요.

- 이 폴더는 빌드된 결과물이에요. `index.html` 한 파일에 이미지·폰트까지 다 들어 있어요 (새 디자인: 기운 충전 + 온보딩).
- 원본 코드(React + Vite): https://github.com/unahynn/chiring
- 따로 보기: https://unahynn.github.io/chiring/

수정은 원본 저장소에서 하고, `npm run build:team` 결과물(`dist-team/index.html`)을 이 폴더의 `index.html`에 덮어쓰면 돼요. 팀 프로토타입 연결 코드(시작 화면 `#frequency`·`#onboarding`, 신호 `chiring:*`)는 원본 `src/TeamApp.tsx`에 들어 있어요.

## 팀 프로토타입 연결
민재님이 처음 붙이면서 빌드 파일에 직접 넣었던 연결(시작 탭 `#frequency`, 홈·친구방 버튼 → `chiring:home` / `chiring:friends`, `chiring:reset`, 사파리 키워드 칩 잘림 수정)은 이제 원본 코드에 들어가 있어서, 다시 빌드해도 유지돼요.
