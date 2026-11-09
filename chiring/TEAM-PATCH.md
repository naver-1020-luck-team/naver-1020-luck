# 팀 프로토타입에서 덧붙인 것 (원본 chiring 코드에 옮겨 주세요)

`index.html`은 빌드 결과물이라, 원본에서 다시 빌드하면 아래 두 가지가 사라져요. 원본(unahynn/chiring)에 옮겨 두면 다시 빌드해도 유지돼요.

## 1. 기운 선물 완료 → 참 등장 효과
시나리오 1(홈에서 참 받기)처럼: 아래 빛이 차오르고 → 참이 위에서 툭 떨어져 흔들리다 자리 잡고 → 뒤에서 빛이 터지며 고리 물결 → 은은하게 빛나며 떠 있어요.

`src/screens/Frequency.css` 맨 아래에 그대로 붙이면 돼요.

```css
/* 팀 프로토타입: 기운 선물 완료 → 참 등장을 시나리오 1 참 화면처럼 (빛이 차오르고 → 참이 툭 떨어져 흔들리다 자리 잡고 → 반짝임) */
.gifted:has(.gifted__charm) .gifted__glow{animation:tcf-glow-rise 1.9s cubic-bezier(.22,.8,.3,1) both,gifted-glow 5s ease-in-out 1.9s infinite alternate}
@keyframes tcf-glow-rise{0%{transform:scaleY(.6);opacity:.6;filter:brightness(.85)}45%{transform:scaleY(1.2);opacity:1;filter:brightness(1.45)}100%{transform:scaleY(1);opacity:1;filter:brightness(1)}}
.gifted__charm{transform-origin:50% 12%;animation:tcf-charm-in 1.25s cubic-bezier(.2,.9,.3,1) .5s both}
@keyframes tcf-charm-in{0%{opacity:0;transform:translateY(-38px) scale(.78);filter:blur(10px) brightness(2)}36%{opacity:1;transform:translateY(7px) scale(1.07) rotate(5deg);filter:blur(0) brightness(1.4)}56%{transform:translateY(-3px) scale(.98) rotate(-3.5deg);filter:brightness(1.12)}76%{transform:translateY(1px) scale(1.01) rotate(1.4deg);filter:none}100%{opacity:1;transform:none;filter:none}}
.gifted__charm img{animation:charm-float 3.4s ease-in-out 1.8s infinite,tcf-charm-glow 3.4s ease-in-out 1.8s infinite}
@keyframes tcf-charm-glow{0%,100%{filter:drop-shadow(0 0 6px color-mix(in srgb,var(--wish,#fff) 35%,transparent))}50%{filter:drop-shadow(0 0 22px color-mix(in srgb,var(--wish,#fff) 60%,transparent))}}
/* 참 뒤에서 퍼지는 빛 + 고리처럼 번지는 물결 */
.gifted__charm:before,.gifted__charm:after{content:"";position:absolute;z-index:-1;pointer-events:none;border-radius:50%}
.gifted__charm:before{inset:-45%;background:radial-gradient(circle,color-mix(in srgb,var(--wish,#fff) 55%,#fff) 0%,color-mix(in srgb,var(--wish,#fff) 40%,transparent) 28%,transparent 62%);animation:tcf-burst 1.5s ease-out .62s both}
@keyframes tcf-burst{0%{opacity:0;transform:scale(.25)}22%{opacity:.95}100%{opacity:0;transform:scale(1.45)}}
.gifted__charm:after{inset:6%;border:2px solid color-mix(in srgb,var(--wish,#fff) 80%,#fff);box-shadow:0 0 18px var(--wish,#fff);animation:tcf-ring 1.3s cubic-bezier(.2,.7,.3,1) .7s both}
@keyframes tcf-ring{0%{opacity:0;transform:scale(.4)}20%{opacity:.85}100%{opacity:0;transform:scale(1.9)}}
.gifted__btn{animation-delay:1.55s}
@media (prefers-reduced-motion:reduce){.gifted__charm,.gifted__charm img,.gifted__charm:before,.gifted__charm:after{animation:none}}
```

## 2. 기운 주파수 소리 (magenta.js)
- `team-sound.js` + `vendor/magentamusic-1.23.1.js` (@magenta/music 1.23.1, Apache-2.0)
- magenta.js의 MusicVAE(`mel_4bar_small_q2`)가 짧은 선율을 만들고, 기운마다 다른 바탕 주파수(tone.ts의 BASE_HZ와 같은 높이) 음계에 맞춰 맑은 종소리로 연주해요.
- 주파수 다시 듣기 → 주파수 선택 → 재생 중: 보통 크기 (tone.ts 바탕음 위에 선율만 얹음)
- 기운 선물 완료: 문지르기 안내(어두운 화면)에서는 가장 작게(-30dB), 문지르는 중·참 등장 후에는 보통 크기(-11dB)
- 원본에서는 `team.html`(빌드 진입 파일)의 `</body>` 앞에 `<script src="team-sound.js"></script>`를 넣고, 두 파일을 `public/`에 두면 돼요.
