# 이 페이지에 쓰인 글자만 뽑아 작은 woff2로 만듭니다.
# 사용: python3 make_fonts.py <Pretendard 경로> [ZEN SERIF 파일]
#  - Pretendard 경로: pretendard 패키지 폴더(dist/web/static/woff2) 또는 Pretendard-*.otf 가 있는 폴더(예: ~/Library/Fonts)
#  - ZEN SERIF 파일: ZEN-SERIF-TTF-Regular.ttf (운세 화면 제목 'Today’s Lucky' 서체). 생략하면 ~/Library/Fonts 에서 찾음
import re, sys, os
from fontTools import subset
pkg = os.path.expanduser(sys.argv[1])
zen = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else '~/Library/Fonts/ZEN-SERIF-TTF-Regular.ttf')
d = os.path.dirname(os.path.abspath(__file__))
src = open(f'{d}/src.html', encoding='utf-8').read()
text = re.sub(r'data:[^"\')]+', '', src)
chars = set(text) | set('0123456789:~!?.,ㅋㅎㅠㄱ ')
chars = ''.join(sorted(c for c in chars if c >= ' '))
def make(path, out):
    opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']; opts.name_IDs = ['*']
    f = subset.load_font(path, opts)
    s = subset.Subsetter(opts); s.populate(text=chars); s.subset(f)
    subset.save_font(f, f'{d}/fonts/{out}.woff2', opts)
    print(out, os.path.getsize(f'{d}/fonts/{out}.woff2') // 1024, 'KB')
for w in ['Regular', 'Medium', 'SemiBold', 'Bold']:
    p = f'{pkg}/dist/web/static/woff2/Pretendard-{w}.woff2'
    if not os.path.exists(p): p = f'{pkg}/Pretendard-{w}.otf'
    make(p, f'pretendard-{w.lower()}')
make(zen, 'zen-serif')
