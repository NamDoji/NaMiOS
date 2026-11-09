from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
base = (ROOT / 'NaMiOS_Sen_Viet_Symbol.svg').read_text()
inner = base.split('<!-- Geometry')[1].split('</svg>')[0]
inner = '<!-- Geometry' + inner

def symbol_at(x, y, size):
    return f'<g transform="translate({x} {y}) scale({size/512})">{inner}</g>'

def svg(name, width, height, body):
    (ROOT / name).write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>''')

def wordmark(x, y, dark=False, size=116):
    primary = '#F8F5EE' if dark else '#182E3B'
    return f'''<text x="{x}" y="{y}" font-family="DejaVu Sans, sans-serif" font-size="{size}" font-weight="bold" letter-spacing="-5" fill="{primary}">NaMi<tspan fill="#C93643">OS</tspan></text>'''

svg('NaMiOS_Logo_Horizontal_Light.svg', 1100, 330,
    symbol_at(28, -62, 430) + wordmark(468, 210, size=112))
svg('NaMiOS_Logo_Horizontal_Dark.svg', 1100, 330,
    '<rect width="1100" height="330" fill="#122A3A"/>' + symbol_at(28, -62, 430) + wordmark(468, 210, True, 112))
svg('NaMiOS_App_Icon.svg', 512, 512,
    '<rect x="8" y="8" width="496" height="496" rx="108" fill="#122A3A"/>' + symbol_at(12, 8, 488))

# True one-color version: complete silhouette and stroke, usable on embossing and monochrome print.
mono = inner
for color in ('#AB2430','#CF3540','#E56365','#F2C66D','#92212E','#BC8A43'):
    mono = mono.replace(color, '#182E3B')
svg('NaMiOS_Symbol_One_Color.svg',512,512,mono)

preview = f'''
<rect width="1600" height="1120" fill="#F5F2EB"/>
<text x="80" y="85" font-family="DejaVu Sans" font-size="40" font-weight="bold" fill="#182E3B">NaMiOS / SEN VIỆT</text>
<text x="80" y="125" font-family="DejaVu Sans" font-size="20" fill="#586B74">Hệ nhận diện đề xuất · Bản thiết kế lại v2.0 · 09/11/2026</text>
<rect x="70" y="160" width="1460" height="350" rx="36" fill="#FFFFFF"/>
{symbol_at(115, 140, 420)}
{wordmark(575, 355, size=128)}
<text x="580" y="408" font-family="DejaVu Sans" font-size="23" fill="#52646B">Nét sen Việt, mở tương lai.</text>
<rect x="70" y="540" width="1460" height="350" rx="36" fill="#122A3A"/>
{symbol_at(115, 520, 420)}
{wordmark(575, 735, True, 128)}
<text x="580" y="788" font-family="DejaVu Sans" font-size="23" fill="#C9D3D6">Phiên bản nền tối</text>
<text x="80" y="960" font-family="DejaVu Sans" font-size="27" font-weight="bold" fill="#182E3B">Ứng dụng hệ điều hành</text>
<rect x="470" y="920" width="140" height="140" rx="31" fill="#122A3A"/>
{symbol_at(470, 920, 140)}
<rect x="640" y="944" width="92" height="92" rx="21" fill="#122A3A"/>
{symbol_at(640, 944, 92)}
<rect x="760" y="962" width="56" height="56" rx="13" fill="#122A3A"/>
{symbol_at(760, 962, 56)}
<text x="1000" y="980" font-family="DejaVu Sans" font-size="18" fill="#586B74">Đỏ son · Vàng ấm · Mực đêm</text>
<rect x="1000" y="1002" width="78" height="48" rx="12" fill="#C93643"/>
<rect x="1088" y="1002" width="78" height="48" rx="12" fill="#F2C66D"/>
<rect x="1176" y="1002" width="78" height="48" rx="12" fill="#122A3A"/>
'''
svg('NaMiOS_Logo_Preview.svg',1600,1120,preview)
print('Generated SVG lockups and preview')
