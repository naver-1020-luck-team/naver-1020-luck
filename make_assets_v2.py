# 시나리오 1 (네이버치링 1107) 디자인 화면에서 프로토타입용 레이어를 만듭니다.
# 사용: python3 make_assets_v2.py <시나리오1 화면 폴더>
import sys, os
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1]
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
os.makedirs(O, exist_ok=True)
L = lambda n: Image.open(os.path.join(SRC, n + '.jpg')).convert('RGB')
A = lambda im: np.asarray(im).astype(float)
save = lambda arr, n, q=93: Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{O}/{n}', quality=q)

def feather(im, px=3):
    w, h = im.size; a = np.ones((h, w), np.float32)
    for i in range(px):
        v = (i + 1) / (px + 1)
        a[i, :] = np.minimum(a[i, :], v); a[h-1-i, :] = np.minimum(a[h-1-i, :], v)
        a[:, i] = np.minimum(a[:, i], v); a[:, w-1-i] = np.minimum(a[:, w-1-i], v)
    out = im.convert('RGBA'); out.putalpha(Image.fromarray((a * 255).astype(np.uint8))); return out

def crop(im, box, name, px=3):
    feather(im.crop(box), px).save(f'{O}/{name}.png')

def harmonic_fill(img, mask, iters=1500):
    out = img.copy(); out[mask] = out[~mask].mean(0)
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4
        out[mask] = avg[mask]
    return out

def keyed(img_arr, bg_arr, box, thr=10, soft=30):
    x0, y0, x1, y1 = box
    a = img_arr[y0:y1, x0:x1]; g = bg_arr[y0:y1, x0:x1]
    al = np.clip((np.abs(a - g).max(2) - thr) / soft, 0, 1)
    al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.4))).astype(float) / 255
    col = np.clip((a - (1 - al[..., None]) * g) / np.maximum(al[..., None], 1e-3), 0, 255)
    return Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA')

def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    cr = lambda o, a, b: (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1], float)

def rrect_alpha(W, H, cx, cy, hw, hh, th, r, K=1, SS=4):
    """회전된 둥근 사각형 알파 (좌표는 원본 픽셀, 결과는 K배)"""
    yy, xx = (np.mgrid[0:H*K*SS, 0:W*K*SS] + .5) / (K * SS)
    c, s = np.cos(th), np.sin(th)
    u = (xx - cx) * c + (yy - cy) * s; v = -(xx - cx) * s + (yy - cy) * c
    dx = np.maximum(np.abs(u) - (hw - r), 0); dy = np.maximum(np.abs(v) - (hh - r), 0)
    inside = (np.hypot(dx, dy) <= r) & (np.abs(u) <= hw) & (np.abs(v) <= hh)
    return np.asarray(Image.fromarray((inside * 255).astype(np.uint8)).resize((W * K, H * K), Image.LANCZOS)).astype(float) / 255

def card_piece(img_arr, box, mask_fn, radius=.22, name=None, K=1):
    """box 안에서 mask_fn으로 고른 픽셀의 최소 회전 사각형을 찾아 둥근 사각형 모양으로 잘라냄"""
    x0, y0, x1, y1 = box; a = img_arr[y0:y1, x0:x1]; m = mask_fn(a)
    ys, xs = np.nonzero(m); P = hull(np.c_[xs + .5, ys + .5]); best = None
    for k in range(len(P)):
        e = P[(k+1) % len(P)] - P[k]; th = np.arctan2(e[1], e[0])
        R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]]); Q = P @ R.T
        lo, hi = Q.min(0), Q.max(0); area = np.prod(hi - lo)
        if best is None or area < best[0]: best = (area, th, lo, hi)
    _, th, lo, hi = best
    c = (lo + hi) / 2; hw, hh = (hi - lo) / 2 + .5
    cx, cy = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]) @ c
    al = rrect_alpha(x1 - x0, y1 - y0, cx, cy, hw, hh, th, radius * 2 * min(hw, hh), K=K)
    rgb = Image.fromarray(a.astype(np.uint8)).resize(((x1-x0)*K, (y1-y0)*K), Image.LANCZOS)
    rgb.putalpha(Image.fromarray((al * 255).astype(np.uint8)))
    if name: rgb.save(f'{O}/{name}.png')
    return dict(cx=cx + x0, cy=cy + y0, hw=hw, hh=hh, deg=float(np.degrees(th)))

info = {}

# ── 1. 오늘의운세 딤1 → 딤2 (카드 윤곽 동일) ─────────────
d1, d2 = L('홈_기본'), L('홈_기본-1'); D1, D2 = A(d1), A(d2)
save(D1, 'n_dim1.jpg', 95)
BTN = (128, 582, 274, 640); XB = (330, 60, 386, 108)
clean = D2.copy(); clean[BTN[1]:BTN[3], BTN[0]:BTN[2]] = D1[BTN[1]:BTN[3], BTN[0]:BTN[2]]
clean[XB[1]:XB[3], XB[0]:XB[2]] = D1[XB[1]:XB[3], XB[0]:XB[2]]
save(clean, 'n_dim2.jpg', 95)
keyed(D2, D1, BTN, thr=14, soft=24).save(f'{O}/n_dim_btn.png')
keyed(D2, D1, XB, thr=6, soft=18).save(f'{O}/n_dim_x.png')

# ── 2. 오늘의운세_화면 ─────────────
save(A(L('오늘의운세_화면')), 'n_fortune.jpg', 95)

# ── 3. 홈 ─────────────
home = L('홈_기본-2'); save(A(home), 'n_home.jpg', 95)

# ── 4. Lucky 상세 3종 + Mapo ─────────────
for key, n in [('item', 'Lucky Item'), ('place', 'Lucky Place'), ('music', 'Lucky Music')]:
    im = L(n)
    for part, box in {'head': (0, 0, 402, 112), 'hero': (0, 112, 402, 505), 'body': (20, 505, 382, 570),
                      'icons': (20, 605, 382, 745), 'btn': (14, 778, 388, 850), 'bar': (120, 850, 282, 874)}.items():
        crop(im, box, f'n_{key}_{part}', 4)
im = L('운세겹쳐보기_오늘의 행운 장소 연결')
for part, box in {'head': (0, 0, 402, 112), 'hero': (0, 80, 402, 485), 'body': (20, 485, 382, 540),
                  'icons': (20, 610, 382, 720), 'ok': (14, 776, 204, 846), 'share': (204, 776, 388, 846), 'bar': (120, 850, 282, 874)}.items():
    crop(im, box, f'n_mapo_{part}', 4)

# ── 5. 촬영 화면: 뷰파인더 비우고 사진만 따로 ─────────────
cam = L('오늘 행운 담기'); C = A(cam)
bgc = np.median(C[120:130, 5:30].reshape(-1, 3), 0)
VB = (16, 200, 388, 652)
vf = C[VB[1]:VB[3], VB[0]:VB[2]]
ins = np.abs(vf - bgc).max(2) > 14
info['cam_bg'] = bgc.tolist()
# 뷰파인더 윤곽: 깨끗한 오른쪽 가장자리 프로필로 둥근 사각형 맞춤
rows = [y for y in range(ins.shape[0]) if ins[y].sum() > 30]
TOP, BOT = rows[0], rows[-1] + 1
right = np.array([np.nonzero(ins[y])[0].max() + 1 for y in rows]); left = np.array([np.nonzero(ins[y])[0].min() for y in rows])
R_, L_ = np.median(right[len(rows)//2-40:len(rows)//2+40]), np.median(left[len(rows)//2-40:len(rows)//2+40])
CX = (L_ + R_) / 2; HW = (R_ - L_) / 2; HH = (BOT - TOP) / 2; CY = (TOP + BOT) / 2
best = None
for r in range(20, 120):
    ds = np.array([min(y - TOP, BOT - 1 - y) for y in rows]); sel = ds < r
    pred = (HW - r) + np.sqrt(np.clip(r * r - (r - ds[sel] - .5) ** 2, 0, None))
    err = np.mean((pred - (right[sel] - CX)) ** 2)
    if best is None or err < best[0]: best = (err, r)
VR = best[1]
info['viewfinder'] = dict(x=VB[0] + CX - HW, y=VB[1] + TOP, w=2 * HW, h=2 * HH, r=VR)
al = rrect_alpha(VB[2]-VB[0], VB[3]-VB[1], CX, CY, HW, HH, 0, VR, K=3)
mk = Image.new('RGBA', al.shape[::-1], (0, 0, 0, 0)); mk.putalpha(Image.fromarray((al * 255).astype(np.uint8))); mk.save(f'{O}/n_cam_mask.png')
# 사진: 둥근 모서리 밖(배경색)은 가장자리 색으로 채움
photo = vf.copy(); known = ins.copy()
for _ in range(40):
    acc = np.zeros_like(photo); cnt = np.zeros(known.shape)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        acc += np.roll(np.roll(photo * known[..., None], dy, 0), dx, 1); cnt += np.roll(np.roll(known, dy, 0), dx, 1)
    g = ~known & (cnt > 0); photo[g] = acc[g] / cnt[g, None]; known |= g
# '1x' 칩 지우기 (사진 위 칩은 따로 올림)
CHIP = (178, 588, 224, 634); cx0, cy0 = CHIP[0] - VB[0], CHIP[1] - VB[1]
hole = np.zeros(photo.shape[:2], bool); hole[cy0:cy0 + 46, cx0:cx0 + 46] = True
photo = harmonic_fill(photo, hole, 600)
save(photo, 'n_cam_photo.jpg', 93)
base = C.copy(); base[VB[1]:VB[3], VB[0]:VB[2]] = bgc
save(base, 'n_cam_base.jpg', 93)
chip = cam.crop(CHIP).convert('RGBA'); yy, xx = np.mgrid[0:46, 0:46]; d = np.hypot(yy - 22.5, xx - 22.5)
chip.putalpha(Image.fromarray(np.clip((21 - d) * 255, 0, 255).astype(np.uint8))); chip.save(f'{O}/n_cam_chip.png')

# ── 6. 참 (버튼수정) : 행마다 왼쪽 끝 색 = 배경 ─────────────
ch = L('오늘 행운 담기_참_버튼수정'); H = A(ch); rowbg = H[:, 4:12].mean(1)
CB = (110, 320, 300, 610); seg = H[CB[1]:CB[3], CB[0]:CB[2]]; rb = rowbg[CB[1]:CB[3]][:, None, :]
alc = np.clip((np.abs(seg - rb).max(2) - 6) / 36, 0, 1)
colc = np.clip((seg - (1 - alc[..., None]) * rb) / np.maximum(alc[..., None], 1e-3), 0, 255)
Image.fromarray(np.dstack([colc, alc * 255]).astype(np.uint8), 'RGBA').save(f'{O}/n_charm.png')
cl = H.copy(); cl[CB[1]:CB[3], CB[0]:CB[2]] = rb
save(cl, 'n_charm_bg.jpg', 95)
crop(ch, (14, 778, 388, 846), 'n_charm_btn', 4)
w = alc / alc.sum(); yy, xx = np.mgrid[0:alc.shape[0], 0:alc.shape[1]]
info['charm'] = dict(box=CB, com=[float((w * xx).sum() + CB[0]), float((w * yy).sum() + CB[1])])

# ── 7. 결과 (오늘의 행운 담기) ─────────────
res = L('오늘의 행운 담기'); R = A(res)
save(R, 'n_result.jpg', 95)
for part, box in {'title': (14, 135, 388, 220), 'trio': (0, 245, 402, 470), 'sub': (60, 505, 342, 580),
                  'tiles': (14, 620, 388, 745), 'btn': (14, 778, 388, 846)}.items():
    crop(res, box, f'n_res_{part}', 4)
rbg = R.copy()
for box in [(14, 135, 388, 220), (0, 245, 402, 470), (60, 505, 342, 580), (14, 620, 388, 745), (14, 778, 388, 846)]:
    rbg[box[1]:box[3], box[0]:box[2]] = np.median(R[300:310, 0:2].reshape(-1, 3), 0) if False else rbg[box[1]:box[3], box[0]:box[2]]
save(R[:, :, :], 'n_result_bg.jpg', 95)

# ── 8. 채팅 (운세 겹쳐보기) ─────────────
chat = L('운세 겹쳐보기_채팅'); CH = A(chat)
full = L('운세 겹쳐보기_채팅_확인 후'); F = A(full)
print('chat top same as full?', np.abs(CH[:690] - F[:690]).mean().round(2))
# 고정 배경: 채팅 화면에서 메시지를 지운 것 (행마다 왼쪽 끝 색)
rowc = CH[:, 2:8].mean(1)
msgs = np.abs(CH - rowc[:, None, :]).max(2) > 10
msgs[:190] = False; msgs[762:] = False
msgs = np.asarray(Image.fromarray((msgs * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
bgf = CH.copy(); bgf[msgs] = np.broadcast_to(rowc[:, None, :], CH.shape)[msgs]
bgf = np.asarray(Image.fromarray(bgf.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0))).astype(float)
save(bgf, 'n_chat_bg.jpg', 95)
save(F[:190], 'n_chat_head.jpg', 95)
Image.fromarray(CH[760:].astype(np.uint8)).save(f'{O}/n_chat_input.jpg', quality=95)
# 메시지 띠(대화 + 겹쳐보기 버블): 긴 시안에서 배경을 빼서 투명하게
rowf = F[:, 2:8].mean(1)
def strip(y0, y1, name):
    seg = F[y0:y1]; rb = rowf[y0:y1][:, None, :]
    al = np.clip((np.abs(seg - rb).max(2) - 5) / 16, 0, 1)
    col = np.clip((seg - (1 - al[..., None]) * rb) / np.maximum(al[..., None], 1e-3), 0, 255)
    Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA').save(f'{O}/{name}.png')
seg = CH[190:690]; rb = rowc[190:690][:, None, :]
al = np.clip((np.abs(seg - rb).max(2) - 5) / 16, 0, 1)
col = np.clip((seg - (1 - al[..., None]) * rb) / np.maximum(al[..., None], 1e-3), 0, 255)
Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA').save(f'{O}/n_chat_msgs.png')   # 화살표가 있는 '확인 전' 시안에서
NEW = [(696, 744), (744, 892), (892, 946), (950, 1016), (1018, 1082), (1082, 1138)]
for i, (y0, y1) in enumerate(NEW): strip(y0, y1, f'n_chat_new{i}')
info['chat_new'] = NEW

# ── 9. 운세 겹쳐보기 딤1(물음표) → 딤2(카드 펼침) ─────────────
m1, m2 = A(L('운세 겹쳐보기_채팅-2')), A(L('운세 겹쳐보기_채팅-1'))
hole = np.zeros(m2.shape[:2], bool)
for (x0, y0, x1, y1) in [(830, 0, 0, 0)][:0]: pass
# 딤2 요소 영역을 비워 배경을 만듦 (흐린 배경이라 주변에서 매끄럽게 채움)
for (x0, y0, x1, y1) in [(30, 80, 380, 700), (60, 728, 345, 765), (14, 778, 388, 846)]:
    hole[y0:y1, x0:x1] = True
mbg = harmonic_fill(m2.copy(), hole, 2500)
save(mbg, 'n_mix_bg.jpg', 95)
for name, src, box in [('n_mix_title', m1, (90, 140, 312, 285)), ('n_mix_stack', m1, (70, 320, 345, 680)),
                       ('n_mix_caption', m2, (80, 730, 322, 765)), ('n_mix_ok', m2, (14, 778, 204, 846)), ('n_mix_share', m2, (204, 778, 388, 846))]:
    keyed(src, mbg, box, thr=14, soft=26).save(f'{O}/{name}.png')
bright = lambda a: (a.mean(2) - np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(25))).astype(float).mean(2) > 22) | ((a.max(2) - a.min(2)) > 90)
for name, box in [('n_mix_item', (36, 80, 270, 315)), ('n_mix_place', (230, 230, 400, 480)), ('n_mix_music', (70, 450, 300, 700))]:
    info[name] = card_piece(m2, box, lambda a: np.abs(a - mbg[box[1]:box[3], box[0]:box[2]]).max(2) > 40, radius=.14, name=name)
    info[name]['box'] = box
info['stack_box'] = (70, 320, 345, 680)

import json
json.dump(info, open(f'{O}/n_info.json', 'w'), indent=1, default=float)
print(json.dumps(info, indent=1, default=float)[:2500])

# ═════════ 보정: 카드·묶음·참을 밝기 기준으로 정확히 ═════════
def largest(m):
    from collections import deque
    h, w = m.shape; lab = np.zeros((h, w), np.int32); best = (0, 0); n = 0
    for y0 in range(h):
        for x0 in np.nonzero(m[y0] & (lab[y0] == 0))[0]:
            n += 1; q = deque([(y0, x0)]); lab[y0, x0] = n; c = 0
            while q:
                y, x = q.popleft(); c += 1
                for yy, xx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
                    if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not lab[yy, xx]: lab[yy, xx] = n; q.append((yy, xx))
            if c > best[0]: best = (c, n)
    return lab == best[1]
def fill_holes(m):
    from collections import deque
    h, w = m.shape; out = np.zeros_like(m); q = deque()
    for x in range(w): q += [(0, x), (h-1, x)]
    for y in range(h): q += [(y, 0), (y, w-1)]
    while q:
        y, x = q.popleft()
        if 0 <= y < h and 0 <= x < w and not out[y, x] and not m[y, x]: out[y, x] = True; q += [(y+1, x), (y-1, x), (y, x+1), (y, x-1)]
    return ~out
for name, box in [('n_mix_item', (30, 80, 272, 312)), ('n_mix_place', (160, 228, 400, 482)), ('n_mix_music', (70, 448, 300, 702))]:
    info[name] = card_piece(m2, box, lambda a: np.asarray(Image.fromarray((largest(a.mean(2) > 105) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))) > 0, radius=.11, name=name); info[name]['box'] = box
def shape_piece(src, box, name, thr):
    x0, y0, x1, y1 = box; a = src[y0:y1, x0:x1]
    m = fill_holes(largest(a.mean(2) > thr))
    al = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.7))).astype(float)
    Image.fromarray(np.dstack([a, al]).astype(np.uint8), 'RGBA').save(f'{O}/{name}.png')
shape_piece(m1, (70, 320, 345, 680), 'n_mix_stack', 95)
keyed(m1, mbg, (90, 140, 312, 285), thr=40, soft=40).save(f'{O}/n_mix_title.png')
keyed(m2, mbg, (80, 730, 322, 765), thr=40, soft=40).save(f'{O}/n_mix_caption.png')

# 참: 참 자리를 주변 배경으로 매끄럽게 채운 뒤 그 배경과의 차이로 분리
seg_m = np.abs(H - rowbg[:, None, :]).max(2) > 9; box_m = np.zeros_like(seg_m); box_m[CB[1]:CB[3], CB[0]:CB[2]] = True
cm = seg_m & box_m; cm = np.asarray(Image.fromarray((cm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(31))) > 0
cbg = harmonic_fill(H.copy(), cm, 3000)
save(cbg, 'n_charm_bg.jpg', 95)
keyed(H, cbg, CB, thr=6, soft=30).save(f'{O}/n_charm.png')
json.dump(info, open(f'{O}/n_info.json', 'w'), indent=1, default=float)
print({k: info[k] for k in ['n_mix_item', 'n_mix_place', 'n_mix_music']})

# 참 배경: 화면은 좌우 대칭 그라데이션 → 참이 없는 깨끗한 반쪽을 거울로 복사
cm2 = (np.abs(H - rowbg[:, None, :]).max(2) > 9) & box_m
cm2 = np.asarray(Image.fromarray((cm2 * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21))) > 0
mir = H[:, ::-1]; cmm = cm2[:, ::-1]
cb2 = H.copy(); use = cm2 & ~cmm; cb2[use] = mir[use]
rest = cm2 & cmm
cb2 = harmonic_fill(cb2, rest, 3000) if rest.any() else cb2
save(cb2, 'n_charm_bg.jpg', 95)
keyed(H, cb2, CB, thr=6, soft=30).save(f'{O}/n_charm.png')
print('charm overlap both halves px', int(rest.sum()))

# 참 배경 (최종): 각 행 = 바탕색 + 가운데가 밝은 종 모양. 참이 없는 좌우 픽셀로 행마다 맞춤
xs = np.arange(402); cx0 = 201.0
cb3 = H.copy(); y0b, y1b = CB[1] - 30, CB[3] + 30
for y in range(y0b, y1b):
    row = H[y]; ok = ~cm2[y] & (np.abs(xs - cx0) < 200)
    if ok.sum() < 20: continue
    # 폭(시그마)은 화면 아래 글로우에서 추정 → 고정 220
    g = np.exp(-((xs - cx0) / 220.0) ** 2)
    Aok = np.c_[np.ones(ok.sum()), g[ok]]
    for c in range(3):
        coef, *_ = np.linalg.lstsq(Aok, row[ok, c], rcond=None)
        fit = coef[0] + coef[1] * g
        cb3[y, cm2[y], c] = fit[cm2[y]]
cb3 = np.asarray(Image.fromarray(np.clip(cb3, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0))).astype(float)
# 경계 이음 부드럽게
edge = np.asarray(Image.fromarray((cm2 * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(float)[..., None] / 255
sm = np.asarray(Image.fromarray(np.clip(cb3, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(float)
cb3 = sm * edge + H * (1 - edge) * (~cm2[..., None]) + sm * (1 - edge) * cm2[..., None]
save(cb3, 'n_charm_bg.jpg', 95)
keyed(H, cb3, CB, thr=6, soft=30).save(f'{O}/n_charm.png')

# ═════════ 홈 캐러셀: 'Lucky Item/Place/Music' 제목 글자 (검정, 투명 배경, 4배) ═════════
def dark_text(img4, box4):
    x0, y0, x1, y1 = box4; g = np.asarray(img4.convert('L')).astype(float)[y0:y1, x0:x1]
    bg = np.asarray(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(6))).astype(float)
    al = np.clip((bg - g - 8) / np.maximum(bg - 25, 40), 0, 1)
    return al
K4 = 4
home4 = home.resize((402 * K4, 874 * K4), Image.LANCZOS)
al = dark_text(home4, (92 * K4, 455 * K4, 252 * K4, 496 * K4))
def save_text(al, name):
    ys, xs = np.nonzero(al > .05); al = al[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.new('RGBA', al.shape[::-1], (17, 17, 17, 0)); im.putalpha(Image.fromarray((al * 255).astype(np.uint8))); im.save(f'{O}/{name}.png')
    return al.shape
info['t_item'] = save_text(al, 'n_t_item')
m2im = L('운세 겹쳐보기_채팅-1').resize((402 * K4, 871 * K4), Image.LANCZOS)
for key in ['place', 'music']:
    g = info[f'n_mix_{key}']; cx, cy = g['cx'] * K4, g['cy'] * K4
    rot = m2im.rotate(g['deg'] - (90 if abs(g['deg']) > 60 else 0), resample=Image.BICUBIC, center=(cx, cy))
    hw, hh = (min(g['hw'], g['hh']) - 12) * K4, (max(g['hw'], g['hh']) - 14) * K4
    box = (int(cx - hw), int(cy - hh), int(cx + hw), int(cy + hh))
    rot.crop(box).save(f'/tmp/claude-0/-home-user/9d59a793-33e1-5177-8643-e671eb009d46/scratchpad/rot_{key}.png')
    a = dark_text(rot, box)
    rows = np.nonzero((a > .3).sum(1) > 3)[0]; runs = []; s = rows[0]; p = rows[0]
    for r in rows[1:]:
        if r - p > 10 * K4 // 4: runs.append((s, p + 1)); s = r
        p = r
    runs.append((s, p + 1))
    runs = [r for r in runs if r[1] - r[0] > 20]
    print(key, 'text lines', runs)
    lines = [a[y0:y1] for y0, y1 in runs[:2]]
    lines = [l[:, np.nonzero(l.max(0) > .05)[0].min():np.nonzero(l.max(0) > .05)[0].max() + 1] for l in lines]
    np.save(f'{O}/_{key}_l1.npy', lines[0]); np.save(f'{O}/_{key}_l2.npy', lines[1])
json.dump(info, open(f'{O}/n_info.json', 'w'), indent=1, default=float)

# ═════════ 홈·결과 바탕 (움직이는 요소 자리를 비움) ═════════
Hm = A(home).copy(); hb = np.median(Hm[740:770, 150:250].reshape(-1, 3), 0)
Hm[395:, :] = hb; save(Hm, 'n_home_base.jpg', 95)
Rr = A(res).copy(); rb0 = np.median(Rr[600:612, 0:12].reshape(-1, 3), 0)
print('result bg', rb0, Rr[60, 5], Rr[800, 5])
for box in [(14, 135, 388, 220), (0, 245, 402, 470), (60, 505, 342, 580), (14, 620, 388, 745), (14, 778, 388, 846)]:
    Rr[box[1]:box[3], box[0]:box[2]] = rb0
save(Rr, 'n_result_base.jpg', 95)

# 'Lucky Place' / 'Lucky Music': 'Lucky'는 홈의 제목 그대로, 두 번째 단어는 겹쳐보기 카드에서 가져와 대문자 높이·기준선을 맞춤
item_a = np.asarray(Image.open(f'{O}/n_t_item.png').getchannel('A')).astype(float) / 255
lucky, itemw = item_a[:, :328], item_a[:, 356:]
r = np.nonzero(itemw.max(1) > .3)[0]; cap_top, base_ = r.min(), r.max() + 1; capH = base_ - cap_top
for key in ['place', 'music']:
    l2 = np.load(f'{O}/_{key}_l2.npy'); l2 = np.where(l2 < .12, 0, l2)
    rr = np.nonzero(l2.max(1) > .3)[0]; l2 = l2[rr.min():rr.max() + 1]
    w2 = np.asarray(Image.fromarray((l2 * 255).astype(np.uint8)).resize((max(1, round(l2.shape[1] * capH / l2.shape[0])), capH), Image.LANCZOS)).astype(float) / 255
    cv = np.zeros((item_a.shape[0], 356 + w2.shape[1])); cv[:, :328] = lucky; cv[cap_top:base_, 356:] = w2
    im = Image.new('RGBA', cv.shape[::-1], (17, 17, 17, 0)); im.putalpha(Image.fromarray((np.clip(cv, 0, 1) * 255).astype(np.uint8))); im.save(f'{O}/n_t_{key}.png')
