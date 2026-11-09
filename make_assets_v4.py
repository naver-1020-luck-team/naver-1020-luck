# 시나리오 1 (네이버 1109) 수정 화면에서 바뀐 레이어만 다시 만듭니다.
# 사용: python3 make_assets_v4.py <1109 시나리오1 화면 폴더>
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1]
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
L = lambda n: Image.open(os.path.join(SRC, n + '.jpg')).convert('RGB')
A = lambda im: np.asarray(im).astype(float)
save = lambda arr, n, q=95: Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{O}/{n}', quality=q)

def feather(im, px=3):
    w, h = im.size; a = np.ones((h, w), np.float32)
    for i in range(px):
        v = (i + 1) / (px + 1)
        a[i, :] = np.minimum(a[i, :], v); a[h-1-i, :] = np.minimum(a[h-1-i, :], v)
        a[:, i] = np.minimum(a[:, i], v); a[:, w-1-i] = np.minimum(a[:, w-1-i], v)
    out = im.convert('RGBA'); out.putalpha(Image.fromarray((a * 255).astype(np.uint8))); return out
def crop(im, box, name, px=4): feather(im.crop(box), px).save(f'{O}/{name}.png')
def harmonic_fill(img, mask, iters=2500):
    out = img.copy(); out[mask] = out[~mask].mean(0)
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4
        out[mask] = avg[mask]
    return out
def dilate(m, k): return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k))) > 0
def boxmask(shape, boxes):
    m = np.zeros(shape[:2], bool)
    for x0, y0, x1, y1 in boxes: m[y0:y1, x0:x1] = True
    return m
def keyed(img, bg, box, thr=10, soft=30):
    x0, y0, x1, y1 = box; a = img[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    al = np.clip((np.abs(a - g).max(2) - thr) / soft, 0, 1)
    al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.4))).astype(float) / 255
    col = np.clip((a - (1 - al[..., None]) * g) / np.maximum(al[..., None], 1e-3), 0, 255)
    return Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA')
def bell_fill(img, mask, sigma=220.0, cx=201.0):
    out = img.copy(); xs = np.arange(img.shape[1]); g = np.exp(-((xs - cx) / sigma) ** 2)
    for y in range(img.shape[0]):
        if not mask[y].any(): continue
        ok = ~mask[y]
        if ok.sum() < 12: continue
        Aok = np.c_[np.ones(ok.sum()), g[ok]]
        for c in range(3):
            coef, *_ = np.linalg.lstsq(Aok, img[y, ok, c], rcond=None)
            out[y, mask[y], c] = (coef[0] + coef[1] * g)[mask[y]]
    return out
def squircle(w, h, n, K=3, SS=4):
    """초타원(스퀴클) 알파: |x/a|^n + |y/b|^n <= 1"""
    yy, xx = (np.mgrid[0:h*K*SS, 0:w*K*SS] + .5) / (K * SS)
    u = np.abs(xx - w / 2) / (w / 2); v = np.abs(yy - h / 2) / (h / 2)
    m = (u ** n + v ** n) <= 1
    return Image.fromarray((m * 255).astype(np.uint8)).resize((w * K, h * K), Image.LANCZOS)
info = {}

# ── 1. 오늘의운세 딤: 딤1 = '홈_기본-1'(문구 카드), 딤2 = '홈_기본'(열쇠 + 보러가기) ─────────────
d1, d2 = A(L('홈_기본-1')), A(L('홈_기본'))
save(d1, 'n_dim1.jpg')
BTN = (128, 578, 284, 634); XB = (330, 60, 386, 108)
CARD = dict(x=37, y=233, w=328, h=326, n=6.2)
# 열쇠: 카드 배경보다 붉은 채널이 확 밝은 부분 → 배경을 매끄럽게 채운 뒤 그 배경과의 차이로 분리
KB = (96, 284, 318, 508)
box = boxmask(d2.shape, [KB])
m = box & (d2[..., 0] - np.asarray(Image.fromarray(d2[..., 0].astype(np.uint8)).filter(ImageFilter.MedianFilter(31))).astype(float) > 18)
for it in range(3):
    hole = dilate(m, 7) & box
    bg = harmonic_fill(d2.copy(), hole, 1500)
    m = box & (np.abs(d2 - bg).max(2) > 16)
hole = dilate(m, 9) & box
bg = harmonic_fill(d2.copy(), hole, 3000)
k = keyed(d2, bg, KB, thr=8, soft=26)
ka = np.asarray(k.getchannel('A')); ys, xs = np.nonzero(ka > 8)
kb = (KB[0] + xs.min() - 2, KB[1] + ys.min() - 2, KB[0] + xs.max() + 3, KB[1] + ys.max() + 3)
k = keyed(d2, bg, kb, thr=8, soft=26); k.save(f'{O}/n_dim_key.png'); info['dim_key'] = kb
clean = bg.copy()
clean[BTN[1]:BTN[3], BTN[0]:BTN[2]] = d1[BTN[1]:BTN[3], BTN[0]:BTN[2]]
save(clean, 'n_dim2.jpg')
keyed(d2, d1, BTN, thr=14, soft=24).save(f'{O}/n_dim_btn.png')
keyed(d2, d1, XB, thr=6, soft=18).save(f'{O}/n_dim_x.png')
# 빛 레이어는 카드 안쪽만: 시안의 밝은 테두리(약 7px)는 덮지 않도록 안으로 들이고 경계를 부드럽게
mk = Image.new('L', (CARD['w'] * 3, CARD['h'] * 3), 0); mk.paste(squircle(CARD['w'] - 16, CARD['h'] - 16, CARD['n']), (24, 24))
mk = mk.filter(ImageFilter.GaussianBlur(9))
Image.merge('RGBA', [mk.point(lambda v: 255)] * 3 + [mk]).save(f'{O}/n_dim_mask.png'); info['dim_card'] = CARD

# ── 2. 오늘의운세_화면 ─────────────
save(A(L('오늘의운세_화면')), 'n_fortune.jpg')

# ── 3. 홈: 바탕 + Lucky Item 카드 배경(글자·버튼 지움) ─────────────
home = L('홈_기본-2'); H = A(home); save(H, 'n_home.jpg')
Hm = H.copy(); hb = np.median(Hm[740:770, 150:250].reshape(-1, 3), 0); Hm[395:, :] = hb; save(Hm, 'n_home_base.jpg')
CC = (67, 423, 335, 690)
cc = H[CC[1]:CC[3], CC[0]:CC[2]].copy()
txt = boxmask(cc.shape, [(24, 26, 230, 104), (188, 186, 252, 252)])   # 제목·부제, 화살표 버튼
outside = np.asarray(squircle(CC[2]-CC[0], CC[3]-CC[1], 5.15, K=1)) < 250   # 카드 밖(옆 카드·바탕)은 채움 재료로 쓰지 않음
cc = harmonic_fill(cc, txt | dilate(outside, 5), 5000)
cc = np.asarray(Image.fromarray(np.clip(cc, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))).astype(float)
ccim = Image.fromarray(np.clip(cc, 0, 255).astype(np.uint8)).resize(((CC[2]-CC[0]) * 3, (CC[3]-CC[1]) * 3), Image.BICUBIC)
ccim = ccim.filter(ImageFilter.GaussianBlur(1.2))
sqa = Image.new('L', ccim.size, 0); sqa.paste(squircle(CC[2]-CC[0]-2, CC[3]-CC[1]-2, 5.15), (3, 3)); ccim.putalpha(sqa)
ccim.save(f'{O}/n_cc_item.png')
sq = squircle(268, 267, 5.15, K=1, SS=8); Image.merge('RGBA', [sq.point(lambda v: 255)] * 3 + [sq]).save(f'{O}/n_cc_mask.png')
g = A(home.convert('L'))
ttl = g[440:500, 90:260] < 60; rows = np.nonzero(ttl.sum(1) > 2)[0]
info['home_title_rows'] = [int(rows.min() + 440), int(rows.max() + 440)]

# ── 4. Lucky 상세 3종 + 마포 (아이콘이 타일 위로, 뒤로가기 원형 버튼) ─────────────
for key, n in [('item', 'Lucky Item'), ('place', 'Lucky Place'), ('music', 'Lucky Music')]:
    im = L(n)
    for part, b in {'head': (0, 0, 402, 112), 'hero': (0, 112, 402, 505), 'body': (20, 505, 382, 570),
                    'icons': (14, 605, 388, 745), 'btn': (14, 778, 388, 850), 'bar': (120, 850, 282, 874)}.items():
        crop(im, b, f'n_{key}_{part}')
im = L('운세겹쳐보기_오늘의 행운 장소 연결')
for part, b in {'head': (0, 0, 402, 112), 'hero': (0, 112, 402, 505), 'body': (20, 505, 382, 570),
                'icons': (14, 605, 388, 745), 'ok': (14, 776, 202, 846), 'share': (202, 776, 388, 846), 'bar': (120, 850, 282, 874)}.items():
    crop(im, b, f'n_mapo_{part}')

# ── 5. 결과 (오늘의 행운 담기) ─────────────
res = L('오늘의 행운 담기'); R = A(res)
save(R, 'n_result.jpg')
for part, b in {'title': (14, 135, 388, 220), 'trio': (0, 245, 402, 470), 'sub': (60, 505, 342, 580),
                'tiles': (14, 620, 388, 745), 'btn': (14, 778, 388, 846)}.items():
    crop(res, b, f'n_res_{part}')

# ── 6. 키링_2: '버튼x' 화면이 그대로 버튼 아래 배경 ─────────────
k2, kx = A(L('키링_2')), A(L('키링_2_버튼x'))
KR = (60, 262, 402, 770); TB = (14, 108, 330, 196); BB = (14, 778, 388, 848)
rowbg = np.median(kx[:, 2:6], 1)
key_m = boxmask(kx.shape, [KR]) & (np.abs(kx - rowbg[:, None, :]).max(2) > 12)
key_m = dilate(key_m, 15); tm = boxmask(kx.shape, [TB])
hole = key_m | tm | boxmask(kx.shape, [(40, 640, 380, 770)])   # 열쇠 그림자까지
# 배경 = 아래 가운데(201, 950)를 중심으로 한 원형 빛. 열쇠 밖 픽셀로 반지름별 색을 구해 채움 (오차 0.5/255)
yy, xx = np.mgrid[0:874, 0:402]; r = np.hypot(xx - 201, yy - 950); kn = ~hole; rb = np.round(r[kn]).astype(int)
full = np.zeros_like(kx)
for c in range(3):
    cnt = np.bincount(rb, minlength=1400); f = np.bincount(rb, kx[kn][:, c], minlength=1400) / np.maximum(cnt, 1)
    idx = np.nonzero(cnt)[0]; f = np.interp(np.arange(len(f)), idx, f[idx]); f = np.convolve(f, np.ones(5) / 5, 'same')
    full[..., c] = np.interp(r, np.arange(len(f)), f)
w = np.asarray(Image.fromarray((dilate(hole, 13) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(float)[..., None] / 255
w = np.maximum(w, hole[..., None])
bg = w * full + (1 - w) * kx
save(bg, 'n_key_bg.jpg')
keyed(kx, bg, KR, thr=10, soft=30).save(f'{O}/n_key.png')
keyed(kx, bg, TB, thr=20, soft=40).save(f'{O}/n_key_title.png')
keyed(k2, kx, BB, thr=10, soft=26).save(f'{O}/n_key_btns.png')
info['key'] = {'KR': KR, 'TB': TB, 'BB': BB}

json.dump(info, open(f'{O}/n_info4.json', 'w'), indent=1, default=int)
print(json.dumps(info, default=int))
