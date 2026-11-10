# 팀 프로토타입에서 덧붙인 것 (원본 chiring 코드에 옮겨 주세요)

`index.html`은 빌드 결과물이라, 원본에서 다시 빌드하면 아래 두 가지가 사라져요. 원본(unahynn/chiring)에 옮겨 두면 다시 빌드해도 유지돼요.

## 1. 기운 선물 완료 → 참 등장 효과 (1110 개선)
시나리오 1 '오늘 행운 담기_참' 등장과 같은 결로 바꿨어요: 아래 빛이 먼저 차오름 → 참이 0.8초에 걸쳐 나타나며 살짝 위(-16px)에서 내려와 자리 잡고(.97→1) → 입체로 살짝 기울었다 잦아듦(rotateY) → 빛줄기가 한 번 훑고 반짝임 → 둥실.
이전 버전은 참을 위 꼭짓점 기준으로 매달린 듯 흔들어서, 고리가 없는 별 참에서 어색했어요.

`index.html`의 `<style id="team-charm-fx">`와 `<script id="team-charm-js">`를 그대로 옮기면 돼요.
- CSS → `src/screens/Frequency.css` 맨 아래
- 스크립트(빛줄기·반짝임 요소를 참에 붙임) → 원본에서는 `gifted__charm` JSX 안에 `tcf-sheen`(참 이미지를 mask-image로 지정)과 `tcf-spark` 요소를 직접 넣는 게 더 깔끔해요.

## 1-1. 온보딩 '나의 캐해 리포트' 확인 버튼: 떠 있는 버튼
`<style id="team-onb-fx">`: `.report__footer`를 `position:sticky; bottom:34px; margin-bottom:34px`, `.report__scroll` 아래 여백 0 → 카드가 버튼 뒤로 스크롤되고, 버튼 위치가 앞 화면 '나의 캐해 확인하기'와 같아요(위 784px · 아래에서 34px). `src/screens/Report.css`(또는 리포트 스타일 파일)에 옮겨 주세요.

## 1-2. 주파수 선택 → 메세지 보기 서체
위 CSS 맨 아래 `.replay-card__message`: 시안처럼 ZEN SERIF, 31px / 줄 간격 48px, 조금 굵게(-webkit-text-stroke). `src/screens/FrequencyReplay.css`의 `.replay-card__message`에 옮겨 주세요.

## 1-3. 메세지 문구: 줄표 모양 (시안)
시안의 `잠이나 자 ㅡㅡ`는 붙은 긴 줄표(`——`)가 아니라 한글 `ㅡ` 두 개예요. `src/` 메세지 데이터(`water-2`, Jiwon)의 `잠이나 자 ——`를 `잠이나 자 ㅡㅡ`로 바꿔 주세요. (`index.html`에는 직접 바꿔 두었어요)

## 2. 기운 주파수 소리 (magenta.js)
- `team-sound.js` + `vendor/magentamusic-1.23.1.js` (@magenta/music 1.23.1, Apache-2.0)
- magenta.js MusicVAE 두 모델이 상황마다 새로 생성: 선율(`mel_4bar_small_q2`, 4마디마다) · 드럼(`drums_2bar_lokl_small`, 2마디마다)
- 기운별 바탕 주파수(tone.ts BASE_HZ와 같은 높이, 양쪽 귀 4Hz 차이) + 코드 패드 + 서브 베이스, 킥마다 패드가 눌렸다 올라오는 사이드체인
- 상황별로 다르게 생성:
  - 문지르기 안내: 80bpm, 잔잔한 패드 + 성긴 선율, 드럼 없음, 가장 작게(-30dB)
  - 문지르는 중: 96bpm, 문지르는 속도만큼 소리가 커지고(-30 → -7dB) 밝아짐(필터 380Hz → 9kHz), 빨리 문지를수록 하이햇 → 킥 → 탐 → 클랩 → 오픈햇 순으로 드럼이 들어옴
  - 참 등장 후: 104bpm 퓨처베이스풍, 4박 킥·2·4박 클랩, 바탕 주파수 5도 위, 한 옥타브 밝은 선율
  - 다시 듣기 재생: 88bpm 로파이 하우스, 스윙 하이햇·오픈햇 (tone.ts 바탕음 위에 얹음)
- 원본에서는 `team.html`(빌드 진입 파일)의 `</body>` 앞에 `<script src="team-sound.js"></script>`를 넣고, 두 파일을 `public/`에 두면 돼요.
