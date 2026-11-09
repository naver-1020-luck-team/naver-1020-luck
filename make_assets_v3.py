# 시나리오 2 (네이버치링 1107) 화면에서 레이어를 만듭니다.
# 사용: python3 make_assets_v3.py <시나리오2 화면 폴더>
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1]
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
L = lambda n: Image.open(os.path.join(SRC, n + '.jpg')).convert('RGB')
A = lambda im: np.asarray(im).astype(float)
save = lambda arr, n, q=94: Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{O}/{n}', quality=q)

def harmonic_fill(img, mask, iters=2500):
    out = img.copy(); out[mask] = out[~mask].mean(0)
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4
        out[mask] = avg[mask]
    return out
def dilate(m, k): return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k))) > 0
def keyed(img, bg, box, thr=10, soft=30):
    x0, y0, x1, y1 = box; a = img[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    al = np.clip((np.abs(a - g).max(2) - thr) / soft, 0, 1)
    al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.4))).astype(float) / 255
    col = np.clip((a - (1 - al[..., None]) * g) / np.maximum(al[..., None], 1e-3), 0, 255)
    return Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA')
def boxmask(shape, boxes):
    m = np.zeros(shape[:2], bool)
    for x0, y0, x1, y1 in boxes: m[y0:y1, x0:x1] = True
    return m
def bell_fill(img, mask, sigma=220.0, cx=201.0):
    """행마다 '바탕색 + 가운데가 밝은 종 모양'으로 맞춰 마스크 영역을 채움 (좌우 대칭 그라데이션 배경용)"""
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
info = {}

# ── 1. 친구방 ─────────────
fr = A(L('친구방'))
save(fr[:104], 'n_fr_head.jpg'); save(fr[104:648], 'n_fr_top.jpg')
info['fr_row_top'] = 640           # 예전 모먼트 줄(fr_row)을 640에 두면 시안과 일치 (평균 차이 3/255)

# ── 2. 운세 순위 비교 (확인 후): 순위 바 패널 + 대화 A ─────────────
rk = A(L('운세 순위 비교_확인 후'))
save(rk[:292], 'n_rank_panel.jpg')
rowc = np.median(rk[:, 2:8], 1)
seg = rk[297:782]; rb = rowc[297:782][:, None, :]
al = np.clip((np.abs(seg - rb).max(2) - 5) / 16, 0, 1)
col = np.clip((seg - (1 - al[..., None]) * rb) / np.maximum(al[..., None], 1e-3), 0, 255)
Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA').save(f'{O}/n_chat_a.png')
info['chatA_h'] = 490

# ── 3. 운세 순위 비교 딤0 → 딤1 ─────────────
d0, d1 = A(L('운세 겹쳐보기_채팅-1')), A(L('운세 겹쳐보기_채팅'))   # -1 = 제목만, 무번호 = 1등 발표
T0 = (60, 324, 342, 424)
b0 = harmonic_fill(d0.copy(), boxmask(d0.shape, [T0]))
save(b0, 'n_rk_bg0.jpg', 95)
keyed(d0, b0, T0, thr=12, soft=30).save(f'{O}/n_rk_title.png')
EL = {'n_rk_fire': (230, 66, 292, 132), 'n_rk_gem': (32, 130, 100, 190), 'n_rk_leaf2': (326, 330, 390, 402),
      'n_rk_card': (70, 266, 330, 700)}
m1 = boxmask(d1.shape, list(EL.values()) + [(60, 140, 342, 245)])
b1 = harmonic_fill(d1.copy(), m1)
save(b1, 'n_rk_bg1.jpg', 95)
for n, box in EL.items(): keyed(d1, b1, box, thr=16, soft=30).save(f'{O}/{n}.png')
info['rk'] = {'title': T0, 'title_dy': 155 - 334, **EL}

# ── 4. 키링_2 ─────────────
k = A(L('키링_2'))
KB = (90, 270, 400, 680); TB = (14, 108, 330, 196); BB = (14, 780, 388, 846)
key_m = boxmask(k.shape, [KB]) & (np.abs(k - np.median(k[:, 2:6], 1)[:, None, :]).max(2) > 14)
key_m = dilate(key_m, 15)
bg = bell_fill(k, key_m | boxmask(k.shape, [TB, BB]))
bg = np.asarray(Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(float) * (key_m | boxmask(k.shape, [TB, BB]))[..., None] + k * (~(key_m | boxmask(k.shape, [TB, BB])))[..., None]
# 버튼 줄은 위아래 줄 사이를 세로로 이어서 채움 (배경은 세로 그라데이션)
y0b, y1b = BB[1] - 4, BB[3] + 4
for y in range(y0b, y1b):
    t = (y - y0b) / (y1b - y0b); bg[y] = k[y0b - 1] * (1 - t) + k[y1b] * t
save(bg, 'n_key_bg.jpg', 95)
keyed(k, bg, KB, thr=10, soft=30).save(f'{O}/n_key.png')
keyed(k, bg, TB, thr=20, soft=40).save(f'{O}/n_key_title.png')
keyed(k, bg, BB, thr=14, soft=30).save(f'{O}/n_key_btns.png')
info['key'] = {'KB': KB, 'TB': TB, 'BB': BB}
json.dump(info, open(f'{O}/n_info2.json', 'w'), indent=1)
print(json.dumps(info))
