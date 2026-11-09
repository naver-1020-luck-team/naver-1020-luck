# 팀 프로토타입에서 덧붙인 것 (원본 chiring 코드에 옮겨 주세요)

`index.html`은 빌드 결과물이라, 원본에서 다시 빌드하면 아래 두 가지가 사라져요. 원본(unahynn/chiring)에 옮겨 두면 다시 빌드해도 유지돼요.

## 1. 기운 선물 완료 → 참 등장 효과
시나리오 1(홈에서 나무 참 받기)처럼 살살: 아래 빛이 천천히 차오르고 → 참이 살짝 위에서 내려오며 아주 조금 흔들리다 멈추고 → 은은하게 빛나며 떠 있어요. (원형 파동 효과는 없앴어요)

`src/screens/Frequency.css` 맨 아래에 그대로 붙이면 돼요.

```css
/* 팀 프로토타입: 기운 선물 완료 → 참 등장 (시나리오 1 나무 참처럼 살살: 아래 빛이 천천히 차오르고, 참이 살짝 위에서 내려와 아주 조금 흔들리다 멈춤) */
.gifted:has(.gifted__charm) .gifted__glow{animation:tcf-glow-rise 2.2s cubic-bezier(.22,.8,.3,1) both,gifted-glow 5s ease-in-out 2.2s infinite alternate}
@keyframes tcf-glow-rise{0%{transform:scaleY(.75);opacity:.7}100%{transform:scaleY(1);opacity:1}}
.gifted__charm{transform-origin:50% 8%;animation:tcf-charm-fade .9s cubic-bezier(.65,0,.35,1) .45s both,tcf-charm-drop 2.4s cubic-bezier(.22,1,.36,1) .45s both}
@keyframes tcf-charm-fade{from{opacity:0}to{opacity:1}}
@keyframes tcf-charm-drop{0%{transform:translateY(-16px) scale(.97) rotate(0)}30%{transform:translateY(-3px) scale(.99) rotate(2.2deg)}52%{transform:translateY(0) scale(1) rotate(-1.4deg)}72%{transform:rotate(.7deg)}88%{transform:rotate(-.25deg)}100%{transform:none}}
.gifted__charm img{animation:charm-float 3.4s ease-in-out 2.6s infinite,tcf-charm-glow 4s ease-in-out 1.6s infinite}
@keyframes tcf-charm-glow{0%,100%{filter:drop-shadow(0 0 4px color-mix(in srgb,var(--wish,#fff) 25%,transparent))}50%{filter:drop-shadow(0 0 14px color-mix(in srgb,var(--wish,#fff) 45%,transparent))}}
.gifted__btn{animation-delay:1.5s}
@media (prefers-reduced-motion:reduce){.gifted__charm,.gifted__charm img{animation:none}}
```

## 2. 기운 주파수 소리 (magenta.js)
- `team-sound.js` + `vendor/magentamusic-1.23.1.js` (@magenta/music 1.23.1, Apache-2.0)
- magenta.js의 MusicVAE(`mel_4bar_small_q2`)가 짧은 선율을 만들고, 기운마다 다른 바탕 주파수(tone.ts의 BASE_HZ와 같은 높이) 음계에 맞춰 맑은 종소리로 연주해요.
- 주파수 다시 듣기 → 주파수 선택 → 재생 중: 보통 크기 (tone.ts 바탕음 위에 선율만 얹음)
- 기운 선물 완료: 문지르기 안내(어두운 화면)에서는 가장 작게(-30dB), 문지르는 중·참 등장 후에는 보통 크기(-11dB)
- 상황별 리듬: 안내(72bpm, 성긴 선율) · 문지르는 중(92bpm, 아르페지오·셰이커·작은 킥) · 참 등장 후(100bpm, 밝은 종소리·킥·박수·베이스) · 다시 듣기(84bpm, 로파이 그루브)
- 원본에서는 `team.html`(빌드 진입 파일)의 `</body>` 앞에 `<script src="team-sound.js"></script>`를 넣고, 두 파일을 `public/`에 두면 돼요.
