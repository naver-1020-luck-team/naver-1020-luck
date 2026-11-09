# 1109 운세 겹쳐보기 → 오늘의 행운 아이템 / 플리 연결 화면 (장소 연결과 같은 틀)
# 사용: python3 make_assets_v6.py <시안 폴더>
import sys, os
import numpy as np
from PIL import Image
SRC = sys.argv[1]
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
def crop(im, box, name, px=4):
    c = im.crop(box); w, h = c.size; a = np.ones((h, w), np.float32)
    for i in range(px):
        v = (i + 1) / (px + 1)
        a[i, :] = np.minimum(a[i, :], v); a[h-1-i, :] = np.minimum(a[h-1-i, :], v)
        a[:, i] = np.minimum(a[:, i], v); a[:, w-1-i] = np.minimum(a[:, w-1-i], v)
    c = c.convert('RGBA'); c.putalpha(Image.fromarray((a * 255).astype(np.uint8))); c.save(f'{O}/{name}.png')
for key, n in [('mxi', '운세겹쳐보기_오늘의 행운 아이템 연결'), ('mxm', '운세겹쳐보기_오늘의 행운 플리 연결')]:
    im = Image.open(os.path.join(SRC, n + '.jpg')).convert('RGB')
    for part, b in {'head': (0, 0, 402, 112), 'hero': (0, 112, 402, 505), 'body': (20, 505, 382, 570),
                    'icons': (14, 605, 388, 745), 'ok': (14, 776, 202, 846), 'share': (202, 776, 388, 846), 'bar': (120, 850, 282, 874)}.items():
        crop(im, b, f'n_{key}_{part}')
print('ok')
