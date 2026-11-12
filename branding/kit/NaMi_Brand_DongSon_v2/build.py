from pathlib import Path
import math,fitz
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent; A=R/'assets';A.mkdir(exist_ok=True)
C={'navy':'#092D4F','gold':'#D4A34A','teal':'#278F8D','ivory':'#FFF9EF','white':'#FFFFFF'}
def point(rad,ang,cx=128,cy=128):
 a=math.radians(ang);return (cx+rad*math.cos(a),cy+rad*math.sin(a))
def arc(rad,start,end):
 x1,y1=point(rad,start); x2,y2=point(rad,end);large=1 if (end-start)%360>180 else 0
 return f'M{x1:.2f} {y1:.2f} A{rad} {rad} 0 {large} 1 {x2:.2f} {y2:.2f}'
def star(n,outer,inner):
 pts=[]
 for i in range(n*2):
  radius=outer if i%2==0 else inner
  pts.append(point(radius,-90+i*180/n))
 return ' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)
def symbol(mono=False,small=False):
 navy=C['navy'];gold=C['gold'];teal=C['teal']
 if mono: gold=navy;teal=navy
 if small:
  return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
<circle cx="128" cy="128" r="104" fill="none" stroke="{navy}" stroke-width="22"/>
<polygon points="{star(8,62,26)}" fill="{gold}"/>
<circle cx="128" cy="128" r="12" fill="{C['ivory'] if not mono else C['white']}"/>
</svg>'''
 dots="".join(f'<circle cx="{point(79,-90+i*30)[0]:.2f}" cy="{point(79,-90+i*30)[1]:.2f}" r="2.3"/>' for i in range(12))
 return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="NaMiOS — mặt trời trống Đông Sơn cách tân">
<!-- Vòng nhịp gợi mặt trống; mặt trời 12 tia là hình học cách tân, không phục dựng hiện vật cụ thể. -->
<path d="{arc(104,-137,128)}" fill="none" stroke="{navy}" stroke-width="19" stroke-linecap="round"/>
<path d="{arc(104,145,225)}" fill="none" stroke="{teal}" stroke-width="19" stroke-linecap="round"/>
<g fill="{gold}" opacity=".86">{dots}</g>
<polygon points="{star(12,60,26)}" fill="{gold}"/>
<circle cx="128" cy="128" r="14" fill="{navy}"/>
</svg>'''
(A/'namios-symbol.svg').write_text(symbol())
(A/'namios-symbol-small.svg').write_text(symbol(small=True))
(A/'namios-symbol-mono.svg').write_text(symbol(mono=True))
# Inverse version retains geometry with brighter rings for dark surfaces.
dark=symbol().replace(C['navy'],'#F4F1E9').replace(C['gold'],'#E5BA69').replace(C['teal'],'#6BC2BC').replace(C['ivory'],C['navy'])
(A/'namios-symbol-dark.svg').write_text(dark)
for variant in ['namios-symbol','namios-symbol-small','namios-symbol-mono','namios-symbol-dark']:
 with fitz.open(A/f'{variant}.svg') as doc:
  for size in ([48,64,128,256,512,1024] if variant=='namios-symbol' else [16,24,32,256] if variant=='namios-symbol-small' else [32,256]):
   doc[0].get_pixmap(matrix=fitz.Matrix(size/256,size/256),alpha=True).save(A/f'{variant}-{size}.png')
# The user-facing 16/24/32 assets use the purpose-drawn simplified geometry.
for size in [16,24,32]:
 (A/f'namios-symbol-{size}.png').write_bytes((A/f'namios-symbol-small-{size}.png').read_bytes())
# App tile is separate from master symbol, with safe spacing; usable by launcher/install UI.
app=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><rect x="5" y="5" width="246" height="246" rx="56" fill="{C['navy']}"/><g transform="translate(31 31) scale(.758)">{symbol().split('>',1)[1].rsplit('</svg>',1)[0]}</g></svg>'''
# A full-color master on ivory plate reads cleaner than tiny inversion.
app=app.replace('fill="#092D4F"/><g', 'fill="#FFF9EF"/><g')
(A/'namios-app-icon.svg').write_text(app)
with fitz.open(A/'namios-app-icon.svg') as doc:
 for size in [32,64,128,256,512]:doc[0].get_pixmap(matrix=fitz.Matrix(size/256,size/256),alpha=True).save(A/f'namios-app-icon-{size}.png')
# Editable typography; renderers without Noto Sans must substitute a licensed font.
lock=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 220"><g transform="translate(13 10) scale(.76)">{symbol().split('>',1)[1].rsplit('</svg>',1)[0]}</g><text x="235" y="137" font-family="Noto Sans,DejaVu Sans,sans-serif" font-weight="650" font-size="100" letter-spacing="-4" fill="{C['navy']}">NaMiOS</text><text x="241" y="177" font-family="Noto Sans,DejaVu Sans,sans-serif" font-weight="400" font-size="22" letter-spacing="3" fill="{C['teal']}">CÔNG NGHỆ CỦA NGƯỜI VIỆT</text></svg>'''
(A/'namios-lockup.svg').write_text(lock)
with fitz.open(A/'namios-lockup.svg') as doc:doc[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=True).save(A/'namios-lockup.png')
# Comparison canvas and presentation of key usage scales.
W,H=1600,940;im=Image.new('RGB',(W,H),'#F4F0E8');d=ImageDraw.Draw(im)
try:
 title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',42)
 body=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
except OSError:title=body=ImageFont.load_default()
d.text((70,48),'NaMiOS  /  Đông Sơn đương đại',font=title,fill=C['navy'])
d.text((73,110),'Biểu tượng mặt trời 12 tia · nhịp vòng trống · hai sắc chủ đạo',font=body,fill='#45616C')
d.rounded_rectangle((48,175,1552,668),radius=36,fill='#FFFDF9')
main=Image.open(A/'namios-symbol-512.png').convert('RGBA');im.paste(main,(140,195),main)
d.rounded_rectangle((780,205,1460,610),radius=40,fill=C['navy'])
darklogo=Image.open(A/'namios-symbol-dark-256.png').convert('RGBA').resize((300,300));im.paste(darklogo,(970,252),darklogo)
d.text((185,685),'Nền sáng',font=body,fill=C['navy']);d.text((1070,685),'Nền tối',font=body,fill=C['navy'])
for j,s in enumerate([16,24,32,48,64,128]):
 k=3+j*80;y=790
 ico=Image.open(A/f'namios-symbol-{s}.png').convert('RGBA').resize((max(32,s),max(32,s)))
 im.paste(ico,(k+80,y+40-(max(32,s)-32)//2),ico)
 d.text((k+80,y+165),str(s)+' px',font=body,fill=C['navy'])
im.save(A/'brand-preview.png')
print('built logo v2')
