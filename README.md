# 오늘의 행운 · 클릭 프로토타입

네이버 1020세대 체류시간 증가 프로젝트의 앱 프로토타입이에요.
오늘의 운세 → 홈 → Lucky Item·Place·Music → 행운 담기(촬영·참) → 모아보기 → 저녁 키링,
친구방(Lucky Talk · 운세 순위 비교 · 운세 겹쳐보기)까지 눌러 볼 수 있어요.

**바로 보기:** https://naver-1020-luck-team.github.io/naver-1020-luck/
(`main`에 올라간 내용이 1~2분 뒤 자동 반영돼요. 안 바뀌어 보이면 Cmd + Shift + R)

## 폴더 구성

| 파일 | 하는 일 |
| --- | --- |
| `src.html` | **수정은 여기서.** 화면 구조, 모션(CSS), 동작(JS) 원본 |
| `index.html` | `build.py`가 만드는 완성본 (이미지·폰트·사운드를 한 파일에 담음). 직접 고치지 않기 |
| `img/` | 디자인 시안에서 잘라낸 이미지 |
| `snd/` | 키링 등장 사운드 |
| `fonts/` | Pretendard · ZEN SERIF (페이지에 쓰인 글자만 담은 파일) |
| `make_assets.py` | 시안 이미지에서 `img/`를 잘라내는 스크립트 |
| `make_fonts.py` | 새 글자를 넣었을 때 폰트를 다시 만드는 스크립트 |
| `make_assets_v7.py` | 오늘의 운세(딤1·딤2·운세 화면) 1110 시안 → 글자를 지운 바탕·열쇠 이미지 |
| `build.py` | `src.html` + `img/` → `index.html` |

## 수정하는 방법

### 1. 문구·타이밍·색 같은 작은 수정 (GitHub 웹에서)
1. `src.html`을 열고 연필(✏️) 아이콘으로 수정
2. **Commit changes** → 이때는 `index.html`이 다시 만들어지지 않으니, 컴퓨터에서 `python3 build.py`를 실행해 함께 올려 주세요.

### 2. 컴퓨터에서 수정 (권장)
```bash
git clone https://github.com/naver-1020-luck-team/naver-1020-luck.git
cd naver-1020-luck
pip install pillow numpy          # 처음 한 번
# src.html 수정 후
python3 build.py                  # index.html 다시 만들기 (처음엔 2~3분, 이후 빠름)
git add -A && git commit -m "무엇을 바꿨는지" && git push
```
- 새 한글 문구를 넣었다면 `pip install fonttools brotli` 후 `python3 make_fonts.py <pretendard 경로> <ZEN-SERIF-TTF-Regular.ttf>`도 실행해 주세요. (pretendard 경로는 패키지 폴더 또는 `Pretendard-*.otf`가 있는 폴더, 예: `~/Library/Fonts`)

## 고화질 원칙
- 화면 속 **글자·버튼·닫기 버튼은 이미지가 아니라 실제 글꼴(Pretendard · ZEN SERIF)과 SVG**로 그려요. 이미지는 카드·빛·사진처럼 글자가 아닌 것만 → 레티나·고해상도에서도 글자가 선명해요.
- 시안을 고칠 때도 같은 방식으로: 시안에서 글자를 지운 바탕만 `img/`에 두고, 글자는 `src.html`에 HTML로 넣기.

## 같이 작업할 때 약속
- 작업 전에 `git pull`로 최신 상태 받기
- 큰 변경은 브랜치를 만들어 Pull Request로 올리고, 다른 사람이 확인 후 합치기
- 커밋 메시지는 "무엇을, 왜" 한 줄로 (예: `키링 등장 속도 느리게`)
