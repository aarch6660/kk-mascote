"""Organiza os renders de inspeção (Pillow, sem alterar a pose)."""
from PIL import Image,ImageDraw,ImageFont
import pathlib,json
HERE=pathlib.Path(__file__).resolve().parent
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
items=json.loads((HERE/'exportados/manifesto.json').read_text())
for group in range((len(items)+6)//7):
 part=items[group*7:group*7+7];sheet=Image.new('RGB',(4*256,len(part)*280),(14,19,25));draw=ImageDraw.Draw(sheet)
 for row,item in enumerate(part):
  for k in range(4):
   p=HERE/'previa'/item['name']/f'{k:02}.png'
   if p.exists():sheet.paste(Image.open(p).convert('RGB').resize((256,256)),(k*256,row*280+24))
  draw.text((10,row*280+3),f"{item['name']} | {item['source']} | {item['length']:.2f}s",font=font,fill='white')
 sheet.save(HERE/'previa'/f'prancha_{group+1:02}.jpg',quality=90)
