# 1110 오늘의 운세(딤1 → 딤2 → 운세 화면) 새 시안 반영 · 고화질 버전
# 글자·버튼·닫기 버튼은 이미지에서 지우고 실제 글꼴(Pretendard · ZEN SERIF)과 SVG로 다시 그려서
# 어떤 해상도에서도 선명하게 보이도록 합니다. 이미지에는 카드·빛·열쇠처럼 글자가 아닌 것만 남겨요.
# 사용: python3 make_assets_v7.py <시안 폴더>   (오늘의운세_화면 · 홈_기본-1 · 홈_기본 .jpg)
import sys, os
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1]
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
L = lambda n: np.asarray(Image.open(os.path.join(SRC, n + '.jpg')).convert('RGB')).astype(float)
save = lambda arr, n, q=96: Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{O}/{n}', quality=q, subsampling=0)

def harmonic_fill(img, mask, iters=2500):
    # 시작값: 가로·세로로 가장 가까운 바깥 색을 선형으로 이은 평균 (넓은 구멍도 빨리, 얼룩 없이 수렴)
    def interp(a, m):
        out = a.copy(); idx = np.arange(a.shape[1])
        for y in np.nonzero(m.any(1))[0]:
            ok = ~m[y]
            if ok.sum() < 2: continue
            for c in range(3): out[y, m[y], c] = np.interp(idx[m[y]], idx[ok], a[y, ok, c])
        return out
    out = (interp(img, mask) + interp(img.transpose(1, 0, 2), mask.T).transpose(1, 0, 2)) / 2
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4
        out[mask] = avg[mask]
    return out
def dilate(m, k): return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k))) > 0
def boxmask(shape, boxes):
    m = np.zeros(shape[:2], bool)
    for x0, y0, x1, y1 in boxes: m[y0:y1, x0:x1] = True
    return m
def textmask(img, boxes, thr=28, k=5):
    """상자 안에서 주변(큰 중앙값)보다 확 밝거나 어두운 글자 픽셀만 → 흐린 배경은 최대한 남김"""
    g = img.mean(2); med = np.asarray(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.MedianFilter(21))).astype(float)
    m = boxmask(img.shape, boxes) & (np.abs(g - med) > thr)
    return dilate(m, k) & boxmask(img.shape, boxes)
def keyed(img, bg, box, thr=10, soft=30):
    x0, y0, x1, y1 = box; a = img[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    al = np.clip((np.abs(a - g).max(2) - thr) / soft, 0, 1)
    al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.4))).astype(float) / 255
    col = np.clip((a - (1 - al[..., None]) * g) / np.maximum(al[..., None], 1e-3), 0, 255)
    return Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA')

# 닫기·하트 버튼은 이미지에 그대로 두고, 같은 자리에 SVG 버튼을 덮어 선명하게 (지우면 테두리 자국이 남음)

# ── 1. 오늘의운세_화면: 날짜·제목·문구·칩·버튼 지운 바탕 ─────────────
f = L('오늘의운세_화면')
m = boxmask(f.shape, [(100, 116, 302, 142), (70, 150, 332, 212), (60, 580, 342, 612), (40, 622, 362, 670)])
m |= boxmask(f.shape, [(100, 692, 302, 740), (96, 741, 306, 788)])   # 칩 3개 (CSS로 다시 그림)
save(harmonic_fill(f, m, 4000), 'n_fortune.jpg')

# ── 2. 딤1: 카드 속 날짜·문구 지움 (흐린 열쇠는 남김) ─────────────
d1, d2 = L('홈_기본-1'), L('홈_기본')
m1 = textmask(d1, [(130, 306, 272, 328), (100, 362, 300, 446)])
d1c = harmonic_fill(d1, m1, 3000)
save(d1c, 'n_dim1.jpg')

# ── 3. 딤2: 열쇠 분리 + 열쇠·보러가기 지운 카드 바탕 ─────────────
BTN = (126, 572, 276, 632)
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
keyed(d2, bg, kb, thr=8, soft=26).save(f'{O}/n_dim_key.png'); print('dim_key box', kb)
clean = bg.copy()
clean[BTN[1]:BTN[3], BTN[0]:BTN[2]] = d1c[BTN[1]:BTN[3], BTN[0]:BTN[2]]   # 버튼 자리 = 딤1의 같은 자리
save(clean, 'n_dim2.jpg')
print('ok')
