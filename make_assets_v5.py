# 1109 친구방(+ 버튼·방 카드 회전) · Lucky Moments(스토리) 화면 레이어
# 사용: python3 make_assets_v5.py <시안 폴더> <chiring 원본 assets 폴더>
#  - 시안 폴더: 친구방.jpg, Lucky Moments.jpg, Lucky Moments_텍스트 입력.jpg
#  - chiring assets: friends/(방·모먼트 사진, 아바타), stickers/(4배 픽셀 스티커)
import sys, os, json
import numpy as np
from PIL import Image

SRC, CH = sys.argv[1], sys.argv[2]
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
L = lambda n: Image.open(os.path.join(SRC, n)).convert('RGB')
A = lambda im: np.asarray(im).astype(float)
save = lambda arr, n, q=94: Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{O}/{n}', quality=q)
info = {}

# ── 1. 친구방: 머리(0~104) + 위쪽(104~653). 방 카드 묶음 자리는 비워 두고 HTML 카드로 그림 ─────────────
fr = A(L('친구방.jpg'))
save(fr[:104], 'n_fr_head.jpg')
top = fr[104:653].copy()
y0, y1 = 212 - 104, 588 - 104
row = np.median(top[:, 2:8], 1)
top[y0:y1] = row[y0:y1][:, None, :]
save(top, 'n_fr_top.jpg')

# ── 2. 방 사진 · 모먼트 사진 · 아바타 (원본을 화면 3배 크기 안쪽으로) ─────────────
def copy(src, name, maxw):
    im = Image.open(os.path.join(CH, src)).convert('RGB')
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(f'{O}/{name}', quality=90)
for s, n in [('room-left.jpg', 'room_l.jpg'), ('room-center.jpg', 'room_c.jpg'), ('room-right.jpg', 'room_r.jpg'),
             ('room-4.jpg', 'room_4.jpg'), ('room-5.jpg', 'room_5.jpg')]:
    copy('friends/' + s, n, 600)
for s, n in [('moment-1.jpg', 'lm_m_unahynn.jpg'), ('moment-sumin.jpg', 'lm_m_sumin.jpg'), ('moment-3.jpg', 'lm_m_minhee.jpg'),
             ('moment-ssu.jpg', 'lm_m_ssu.jpg'), ('moment-kwon.jpg', 'lm_m_kwon.jpg')]:
    copy('friends/' + s, n, 1086)
for s, n in [('avatar-unahynn.jpg', 'lm_av_unahynn.jpg'), ('avatar-sumin.jpg', 'lm_av_sumin.jpg'), ('avatar-3.jpg', 'lm_av_minhee.jpg'),
             ('avatar-ssu.jpg', 'lm_av_ssu.jpg'), ('avatar-kwon.jpg', 'lm_av_kwon.jpg')]:
    copy('friends/' + s, n, 240)

# ── 3. 기운 스티커: 4배 픽셀 그림의 채움색을 시안처럼 위→아래 그라디언트로 (검은 테두리·속 그림은 그대로) ─────────────
GRAD = {   # 시안(Lucky Moments) 버튼 속 이모지에서 위·아래 색을 측정
    'fire': ((232, 150, 226), (255, 217, 255)), 'water': ((22, 222, 250), (202, 247, 253)),
    'diamond': ((212, 255, 110), (219, 234, 184)), 'leaf': ((98, 249, 196), (180, 244, 222)),
    'sprout': ((248, 85, 3), (242, 150, 103)),
}
KIND = {'fire': 'fire', 'water': 'water', 'diamond': 'diamond', 'leaf': 'leaf', 'sprout': 'sprout',
        'gem-a': 'diamond', 'gem-b': 'diamond', 'leaf-small-a': 'leaf', 'leaf-small-b': 'leaf'}
for name, kind in KIND.items():
    im = Image.open(os.path.join(CH, 'stickers', name + '.png')).convert('RGBA'); a = np.asarray(im).astype(float)
    rgb, al = a[..., :3], a[..., 3]
    lum = rgb @ [.299, .587, .114]
    fill = (al > 10) & (lum > 70)
    ys = np.nonzero(fill.any(1))[0]; t = np.clip((np.arange(a.shape[0]) - ys[0]) / max(1, ys[-1] - ys[0]), 0, 1)
    c0, c1 = np.array(GRAD[kind][0], float), np.array(GRAD[kind][1], float)
    grad = c0[None, :] * (1 - t[:, None]) + c1[None, :] * t[:, None]          # 행마다 색
    base = np.median(rgb[fill], 0)                                              # 원래 채움색 → 밝기 비율 유지 (하이라이트 등)
    ratio = np.clip(lum / max(1, base @ [.299, .587, .114]), .55, 1.35)[..., None]
    out = rgb.copy(); g = np.broadcast_to(grad[:, None, :], rgb.shape) * ratio
    out[fill] = np.clip(g[fill], 0, 255)
    Image.fromarray(np.dstack([out, al]).astype(np.uint8), 'RGBA').save(f'{O}/lm_st_{name.replace("-", "_")}.png')

# ── 4. 스토리 화면 조각 ─────────────
lm, lt = L('Lucky Moments.jpg'), L('Lucky Moments_텍스트 입력.jpg')
lm.crop((0, 0, 402, 112)).save(f'{O}/lm_head.jpg', quality=94)          # 상태바 + 뒤로 버튼
lt.crop((0, 566, 402, 874)).save(f'{O}/lm_kbd.jpg', quality=94)          # 키보드

# 사진 카드 모양: 모서리 = 초타원 (시안 윤곽에 맞춤)
prof = [(0, 52), (4, 31), (8, 22), (12, 16), (16, 12), (20, 9), (24, 7), (28, 5), (32, 4), (36, 3), (40, 2), (48, 1), (56, 0)]
best = None
for R in range(50, 140, 2):
    for n in np.arange(2, 8, .1):
        err = 0
        for dy, ins in prof[1:]:
            v = max(0, (R - dy - .5) / R); x = R - R * (1 - v ** n) ** (1 / n) if v < 1 else R
            err += (x - ins) ** 2
        if best is None or err < best[0]: best = (err, R, n)
_, R, n = best; info['photo_corner'] = dict(R=R, n=round(float(n), 2))
W, H, K, SS = 362, 424, 3, 4
yy, xx = (np.mgrid[0:H*K*SS, 0:W*K*SS] + .5) / (K * SS)
dx = np.maximum(0, R - np.minimum(xx, W - xx)) / R; dy = np.maximum(0, R - np.minimum(yy, H - yy)) / R
m = (dx ** n + dy ** n) <= 1
mk = Image.fromarray((m * 255).astype(np.uint8)).resize((W * K, H * K), Image.LANCZOS)
Image.merge('RGBA', [mk.point(lambda v: 255)] * 3 + [mk]).save(f'{O}/lm_mask.png')
json.dump(info, open(f'{O}/n_info5.json', 'w'))
print(info)
