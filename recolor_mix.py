# 운세 겹쳐보기 연결 화면 색 바꾸기: 아이템 = 연두 → 하늘(시안), 플리 = 시안 → 분홍 (제목·강조 글자·기운 아이콘)
# 강조색 픽셀(색상 범위 안·채도 있는 것)만 HSV로 옮김 → 글자 테두리의 부드러운 경계·아이콘 그라디언트 결은 그대로
import numpy as np
from PIL import Image
def hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]; mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
    h = np.zeros_like(mx); nz = d > 1e-6
    i = nz & (mx == r); h[i] = ((g - b)[i] / d[i]) % 6
    i = nz & (mx == g) & (mx != r); h[i] = (b - r)[i] / d[i] + 2
    i = nz & (mx == b) & (mx != r) & (mx != g); h[i] = (r - g)[i] / d[i] + 4
    return h * 60, np.where(mx > 0, d / np.maximum(mx, 1e-6), 0), mx
def rgb(h, s, v):
    c = v * s; x = c * (1 - np.abs((h / 60) % 2 - 1)); m = v - c; z = np.zeros_like(h); k = (h // 60).astype(int) % 6
    out = np.stack([np.choose(k, [c, x, z, z, x, c]), np.choose(k, [x, c, c, x, z, z]), np.choose(k, [z, z, x, c, c, x])], -1)
    return out + m[..., None]
def recolor(path, src_h, dst_h, sfun, y_from=0):
    im = Image.open(path).convert('RGBA'); a = np.asarray(im).astype(float) / 255; c = a[..., :3]
    h, s, v = hsv(c); dh = (h - src_h + 180) % 360 - 180
    m = (np.abs(dh) < 22) & (s > .1); m[:y_from] = False
    nh = (dst_h + dh) % 360; ns = sfun(s)
    c2 = np.where(m[..., None], rgb(nh, ns, v), c)
    out = np.concatenate([c2, a[..., 3:]], -1); Image.fromarray((out * 255).round().astype(np.uint8)).save(path, optimize=True)
    print(path, int(m.sum()))
item = lambda s: np.minimum(1, s * 1.5)              # 연두(채도 .59) → 시안(.93)
pink = lambda s: .37 * np.sqrt(s / .93)              # 시안(.93) → 연분홍(.37)
for n in ['n_mxi_body', 'n_mxi_icons']: recolor(f'img/{n}.png', 78, 187, item)
recolor('img/n_mxi_hero.png', 78, 187, item, y_from=320)
for n in ['n_mxm_body', 'n_mxm_icons']: recolor(f'img/{n}.png', 187, 305, pink)
recolor('img/n_mxm_hero.png', 187, 305, pink, y_from=320)
