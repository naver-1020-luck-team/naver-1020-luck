# 운세 겹쳐보기: 물음표 묶음(n_mix_stack) 속 세 장의 자리·기울기를 펼친 카드(n_mix_item·place·music)에 맞춰
# ① 겹친 자리로 보내는 transform 값(--tx --ty --r --s)을 계산하고
# ② 각 카드가 겹쳐 있을 때 보일 '앞면'(묶음 그림에서 그 카드 부분, 가려진 곳은 흐린 자기 그림으로 메움)을 만듦
# → 묶음 그림이 사라지고 새 카드가 나타나는 대신, 뭉쳐 있던 카드가 그대로 펼쳐짐
import numpy as np
from PIL import Image, ImageFilter
D = 'img'
STACK_AT = (70, 320)                 # n_mix_stack 화면 위치
# 묶음 속 카드 (묶음 그림 좌표: 중심 x, y, 기울기 deg, 카드 폭) — 실제 카드 모양을 묶음 그림에 맞춰 찾은 값
IN_STACK = {'item': (103, 127.5, -9), 'music': (167, 163, 15), 'place': (135, 239.5, 0)}
CARD_W = 160
ELEM = {'item': (30, 80), 'place': (160, 228), 'music': (70, 448)}   # 펼친 카드 img 위치 (left, top)
ORDER = ['item', 'music', 'place']   # 묶음에서 아래 → 위

def rect(mask):                      # 회전된 카드 사각형: 기울기·폭·높이·중심
    ys, xs = np.nonzero(mask); P = np.stack([xs, ys], 1).astype(float); c = P.mean(0); Q = P - c; best = None
    for deg in np.arange(-45, 45, .1):
        t = np.radians(deg); u = Q[:, 0] * np.cos(t) + Q[:, 1] * np.sin(t); v = -Q[:, 0] * np.sin(t) + Q[:, 1] * np.cos(t)
        w, h = np.ptp(u), np.ptp(v)
        if best is None or w * h < best[0]: best = (w * h, deg, w, h, (u.max() + u.min()) / 2, (v.max() + v.min()) / 2)
    _, deg, w, h, ou, ov = best; t = np.radians(deg)
    return deg, w, h, c[0] + ou * np.cos(t) - ov * np.sin(t), c[1] + ou * np.sin(t) + ov * np.cos(t)

stack = Image.open(f'{D}/n_mix_stack.png').convert('RGBA')
cards, aff, RECT = {}, {}, {}
for k in ORDER:
    im = Image.open(f'{D}/n_mix_{k}.png').convert('RGBA'); w, h = im.size
    deg, cw, ch, icx, icy = rect(np.asarray(im)[:, :, 3] > 128); RECT[k] = (deg, cw, ch, icx, icy)
    sx, sy, sdeg = IN_STACK[k]; s = CARD_W / cw; r = sdeg - deg
    t = np.radians(r); R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    L, T = ELEM[k]; ec = np.array([L + w / 2, T + h / 2]); o = np.array([icx - w / 2, icy - h / 2])
    target = np.array([STACK_AT[0] + sx, STACK_AT[1] + sy])
    tr = target - ec - s * R @ o
    print(f'{k}: --tx:{tr[0]:.1f}px;--ty:{tr[1]:.1f}px;--r:{r:.1f}deg;--s:{s:.4f}')
    # 카드 그림 좌표 → 묶음 그림 좌표 (아핀)
    A = s * R; off = ec + tr - A @ np.array([w / 2, h / 2]) - np.array(STACK_AT)
    aff[k] = (A, off); cards[k] = im

S = 3   # 앞면은 고화질(3배)로 바로 만듦 (build.py가 다시 키우지 않음 → 물음표 주변 번짐 없음)
def up(im):   # build.py와 같은 방식의 3배 확대 + 선명화 (묶음 그림이 앱에서 보이던 것과 같은 결)
    big = im.convert('RGBa').resize((im.width * S, im.height * S), Image.LANCZOS).convert('RGBA')
    rgb = big.convert('RGB').filter(ImageFilter.UnsharpMask(radius=2.4, percent=70, threshold=4)); rgb.putalpha(big.getchannel('A')); return rgb
stack3 = up(stack); cards3 = {k: up(v) for k, v in cards.items()}
def to_stack(k, img):                # 카드 그림 공간(3배) → 묶음 그림 공간(3배)
    A, off = aff[k]; Ai = np.linalg.inv(A); b = -Ai @ (off * S)
    return img.transform(stack3.size, Image.AFFINE, (Ai[0, 0], Ai[0, 1], b[0], Ai[1, 0], Ai[1, 1], b[1]), Image.BICUBIC)
def from_stack(k, img):              # 묶음 그림 공간(3배) → 카드 그림 공간(3배)
    A, off = aff[k]; w, h = cards3[k].size
    return img.transform((w, h), Image.AFFINE, (A[0, 0], A[0, 1], off[0] * S, A[1, 0], A[1, 1], off[1] * S), Image.BICUBIC)

RAD = 19   # 카드 모서리 반지름 (1배 기준)
def smooth_shape(k):   # 카드 크기·기울기로 그린 매끄러운 둥근 사각형 (원본 알파의 계단 대신) — 4배로 그려 줄임
    from PIL import ImageDraw
    deg, cw, ch, icx, icy = RECT[k]; w, h = cards3[k].size; SS = 4; q = S * SS
    pts = []
    for cx, cy, a0 in [(cw / 2 - RAD, ch / 2 - RAD, 0), (-cw / 2 + RAD, ch / 2 - RAD, 90), (-cw / 2 + RAD, -ch / 2 + RAD, 180), (cw / 2 - RAD, -ch / 2 + RAD, 270)]:
        for a in np.radians(np.arange(a0, a0 + 90.1, 3)): pts.append((cx + RAD * np.cos(a), cy + RAD * np.sin(a)))
    t = np.radians(deg); P = [((icx + u * np.cos(t) - v * np.sin(t)) * q, (icy + u * np.sin(t) + v * np.cos(t)) * q) for u, v in pts]
    m = Image.new('L', (w * SS, h * SS), 0); ImageDraw.Draw(m).polygon(P, fill=255)
    return m.resize((w, h), Image.LANCZOS)

for i, k in enumerate(ORDER):
    im = cards3[k]; alpha = im.getchannel('A')
    cover = Image.new('L', stack3.size, 0)                            # 이 카드를 덮는 위 카드들의 자리
    for j in ORDER[i + 1:]:
        cover = Image.fromarray(np.maximum(np.asarray(cover), np.asarray(to_stack(j, cards3[j].getchannel('A')))))
    cover = cover.filter(ImageFilter.MaxFilter(13 * S // 2 * 2 + 1))   # 위 카드의 테두리·그림자까지 덮음
    seen = from_stack(k, stack3)                                      # 묶음에서 이 카드 자리의 그림
    vis = from_stack(k, Image.fromarray(255 - np.asarray(cover))).filter(ImageFilter.GaussianBlur(4 * S))
    own = alpha.filter(ImageFilter.MinFilter(13 * S // 2 * 2 + 1)).filter(ImageFilter.GaussianBlur(3 * S))   # 가장자리 띠는 자기 색으로
    vis = Image.fromarray((np.asarray(vis).astype(int) * np.asarray(own) // 255).astype(np.uint8))
    fill = im.convert('RGBa').filter(ImageFilter.GaussianBlur(14 * S)).convert('RGBA').convert('RGB')   # 가려진 곳: 자기 그림을 크게 흐려서(글자 없이)
    face = Image.composite(seen.convert('RGB'), fill, vis)
    # 가장자리: 원본 카드 테두리의 어두운 1px(배경이 섞인 픽셀)을 안쪽 색으로 바꿈 → 돌려 놓아도 점선처럼 보이지 않음
    al = np.asarray(alpha).astype(float)
    inner = Image.fromarray(((al >= 250) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9))
    fr = np.asarray(face).astype(float); m = np.asarray(inner).astype(float)[..., None] / 255
    num = np.asarray(Image.fromarray((fr * m).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(float)
    den = np.asarray(Image.fromarray((m[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(float)[..., None] / 255
    clean = Image.fromarray(np.clip(num / np.maximum(den, 1e-3), 0, 255).astype(np.uint8))
    face = Image.composite(face, clean, inner.filter(ImageFilter.GaussianBlur(1.5)))
    face.putalpha(smooth_shape(k))
    face.save(f'{D}/n_mix_face_{k}.png', optimize=True)
print('ok')
