# 1109 시안: 겹쳐보기 카드·채팅 장소 카드 모서리(스퀴클) 반영
# 사용: python3 make_assets_v4b.py <1109 시나리오1 화면 폴더>
import sys, os
import numpy as np
from PIL import Image, ImageFilter
from collections import deque

SRC = sys.argv[1]
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
L = lambda n: Image.open(os.path.join(SRC, n + '.jpg')).convert('RGB')
A = lambda im: np.asarray(im).astype(float)
save = lambda arr, n, q=95: Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{O}/{n}', quality=q)

def harmonic_fill(img, mask, iters=2500):
    out = img.copy(); out[mask] = out[~mask].mean(0)
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4
        out[mask] = avg[mask]
    return out
def keyed_alpha(a, g, thr, soft):
    al = np.clip((np.abs(a - g).max(2) - thr) / soft, 0, 1)
    return np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.4))).astype(float) / 255
def unmix(a, g, al): return np.clip((a - (1 - al[..., None]) * g) / np.maximum(al[..., None], 1e-3), 0, 255)
def keyed(img, bg, box, thr=10, soft=30):
    x0, y0, x1, y1 = box; a = img[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]; al = keyed_alpha(a, g, thr, soft)
    return Image.fromarray(np.dstack([unmix(a, g, al), al * 255]).astype(np.uint8), 'RGBA')
def largest(m):
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
    h, w = m.shape; out = np.zeros_like(m); q = deque()
    for x in range(w): q += [(0, x), (h-1, x)]
    for y in range(h): q += [(y, 0), (y, w-1)]
    while q:
        y, x = q.popleft()
        if 0 <= y < h and 0 <= x < w and not out[y, x] and not m[y, x]: out[y, x] = True; q += [(y+1, x), (y-1, x), (y, x+1), (y, x-1)]
    return ~out
def erode(m, k): return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(k))) > 0

def card_cut(src, bg, box, name, thr=24, soft=40):
    """카드 실제 윤곽을 그대로 따서 자름: 가장자리는 배경과의 차이로 부드럽게, 안쪽은 꽉 채움"""
    x0, y0, x1, y1 = box; a = src[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    al = keyed_alpha(a, g, thr, soft)
    core = erode(fill_holes(largest(al > .5)), 3)
    al = np.maximum(al, core) * fill_holes(largest(al > .08))   # 다른 조각(잡티)은 버림
    Image.fromarray(np.dstack([unmix(a, g, np.maximum(al, 1e-3)), al * 255]).astype(np.uint8), 'RGBA').save(f'{O}/{name}.png')

# ── 운세 겹쳐보기 딤1(묶음) / 딤2(카드 펼침) ─────────────
m1, m2 = A(L('운세 겹쳐보기_채팅-2')), A(L('운세 겹쳐보기_채팅-1'))
hole = np.zeros(m2.shape[:2], bool)
for (x0, y0, x1, y1) in [(30, 80, 380, 700), (60, 728, 345, 765), (14, 778, 388, 846)]: hole[y0:y1, x0:x1] = True
mbg = harmonic_fill(m2.copy(), hole, 2500)
save(mbg, 'n_mix_bg.jpg')
for name, box in [('n_mix_item', (30, 80, 272, 312)), ('n_mix_place', (160, 228, 400, 482)), ('n_mix_music', (70, 448, 300, 702))]:
    card_cut(m2, mbg, box, name)
card_cut(m1, mbg, (70, 320, 345, 680), 'n_mix_stack')
keyed(m1, mbg, (90, 140, 312, 285), thr=40, soft=40).save(f'{O}/n_mix_title.png')
keyed(m2, mbg, (80, 730, 322, 765), thr=40, soft=40).save(f'{O}/n_mix_caption.png')
keyed(m2, mbg, (14, 778, 204, 846), thr=14, soft=26).save(f'{O}/n_mix_ok.png')
keyed(m2, mbg, (204, 778, 388, 846), thr=14, soft=26).save(f'{O}/n_mix_share.png')

# ── 채팅 (확인 후): 새 메시지 띠 ─────────────
F = A(L('운세 겹쳐보기_채팅_확인 후')); rowf = F[:, 2:8].mean(1)
def strip(y0, y1, name):
    seg = F[y0:y1]; rb = rowf[y0:y1][:, None, :]
    al = np.clip((np.abs(seg - rb).max(2) - 5) / 16, 0, 1)
    Image.fromarray(np.dstack([unmix(seg, rb, al), al * 255]).astype(np.uint8), 'RGBA').save(f'{O}/{name}.png')
for i, (y0, y1) in enumerate([(696, 744), (744, 892), (892, 946), (950, 1016), (1018, 1082), (1082, 1138)]):
    strip(y0, y1, f'n_chat_new{i}')
print('ok')
