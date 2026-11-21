#!/usr/bin/env python3
"""maak_maanbol.py — zet een maanfoto om in een interactieve 3D-bol (één HTML-bestand).

Gebruik:
    python3 maak_maanbol.py maan.tif                 -> maan_bol.html
    python3 maak_maanbol.py maan.tif -o mijnbol.html
    python3 maak_maanbol.py maan.tif --drempel 30    (als de randdetectie niet goed gaat)
    python3 maak_maanbol.py maan.tif --cirkel 266 659 315   (middelpunt x y en straal zelf opgeven)

Wat het doet (er wordt geen data toegevoegd):
 1. Zoekt de maanschijf: fit een cirkel op de verlichte rand (de terminator wordt genegeerd).
 2. Rekent elke pixel van de schijf terug naar lengte/breedte op een bol
    (orthografische projectie: X=(x-cx)/r, Y=-(y-cy)/r, Z=sqrt(1-X²-Y²)).
 3. Maakt daar een kaart van (equirectangulair, 2048x1024). De achterkant krijgt een raster = geen data.
 4. Stopt die kaart in een HTML-pagina die per pixel een straal door de bol rekent (ray casting).

Let op: het script neemt aan dat de VERLICHTE rand aan de RECHTERKANT zit (wassende maan, rechtop
gedraaid). Zit hij links, gebruik dan --links.
Vereist: pip install opencv-python numpy
"""
import argparse, base64, sys
import cv2, numpy as np

TEMPLATE = '<!DOCTYPE html>\n<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>Maan op een bol — virtuele projector</title>\n<style>\n:root{color-scheme:dark}\nbody{margin:0;background:#07080b;color:#d9dde4;font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}\n.wrap{max-width:980px;margin:0 auto;padding:20px;display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px}\n@media(max-width:820px){.wrap{grid-template-columns:1fr}}\nh1{font-size:20px;margin:0 0 4px;font-weight:600}\n.sub{color:#8b93a1;margin:0 0 16px;font-size:14px}\ncanvas{width:100%;aspect-ratio:1;background:#000;border-radius:10px;cursor:grab;touch-action:none;display:block}\ncanvas:active{cursor:grabbing}\n.panel{background:#11141a;border:1px solid #1f242d;border-radius:10px;padding:16px}\nlabel{display:block;font-size:13px;color:#9aa3b2;margin-top:12px}\ninput[type=range]{width:100%}\n.val{float:right;color:#d9dde4;font-variant-numeric:tabular-nums}\n.btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}\nbutton{background:#1b2029;color:#d9dde4;border:1px solid #2a313c;border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;cursor:pointer}\nbutton:hover{background:#252b36}\n.note{font-size:13px;color:#8b93a1;margin-top:16px}\n.note b{color:#c9ced8;font-weight:600}\n.sw{display:inline-block;width:10px;height:10px;background:#1a1e26;border:1px solid #323a48;vertical-align:middle;margin-right:4px}\n</style></head><body>\n<div class="wrap">\n<div>\n<h1>Je maanfoto op een bol</h1>\n<p class="sub">Sleep om om de maan heen te bewegen — net als met de projector.</p>\n<canvas id="c" width="640" height="640"></canvas>\n</div>\n<div class="panel">\n<label>Lengte (links–rechts) <span class="val" id="yv"></span><input id="yaw" type="range" min="-180" max="180" step="1" value="0"></label>\n<label>Breedte (boven–onder) <span class="val" id="pv"></span><input id="pitch" type="range" min="-90" max="90" step="1" value="0"></label>\n<label>Afstand <span class="val" id="dv"></span><input id="dist" type="range" min="1.3" max="12" step="0.05" value="4"></label>\n<div class="btns">\n<button data-p="0,0,4">Vanaf de aarde</button>\n<button data-p="60,0,4">60° opzij</button>\n<button data-p="90,0,4">Van opzij (90°)</button>\n<button data-p="0,80,4">Boven de noordpool</button>\n<button data-p="-35,-20,1.6">Laag overvliegen</button>\n<button id="spin">Draaien ▶</button>\n</div>\n<p class="note"><b>Wat je ziet</b> is alleen je eigen foto, teruggerekend op een bol. Er is niets toegevoegd.</p>\n<p class="note"><b>Schaduwen bewegen niet mee:</b> het licht zit "in" de foto geschilderd, precies zoals bij de projector.</p>\n<p class="note"><b>Uitgesmeerd bij de rand:</b> daar zag je camera het oppervlak heel schuin, dus heel weinig pixels per kilometer. Van opzij wordt dat zichtbaar.</p>\n<p class="note"><span class="sw"></span><b>Raster</b> = achterkant van de maan: geen data, want die zie je vanaf de aarde nooit.</p>\n</div>\n</div>\n<script>\nconst TEX="data:image/jpeg;base64,__B64__";\nconst cv=document.getElementById(\'c\'),ctx=cv.getContext(\'2d\');\nconst N=cv.width,img=ctx.createImageData(N,N),px=img.data;\nconst yaw=document.getElementById(\'yaw\'),pitch=document.getElementById(\'pitch\'),dist=document.getElementById(\'dist\');\nlet T=null,TW=0,TH=0,spinning=false;\nconst im=new Image();im.onload=()=>{const o=document.createElement(\'canvas\');o.width=TW=im.width;o.height=TH=im.height;const oc=o.getContext(\'2d\');oc.drawImage(im,0,0);T=oc.getImageData(0,0,TW,TH).data;draw()};im.src=TEX;\nfunction draw(){\n if(!T)return;\n const a=+yaw.value*Math.PI/180,b=-pitch.value*Math.PI/180,D=+dist.value;\n document.getElementById(\'yv\').textContent=yaw.value+\'°\';document.getElementById(\'pv\').textContent=pitch.value+\'°\';document.getElementById(\'dv\').textContent=(+D).toFixed(1)+\' R\';\n // field of view so the moon fills ~80% of frame at any distance\n const half=Math.asin(1/D)/0.8,t=Math.tan(half);\n const ca=Math.cos(a),sa=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b);\n let k=0;\n for(let j=0;j<N;j++){const v=(1-2*(j+.5)/N)*t;\n  for(let i=0;i<N;i++,k+=4){const u=(2*(i+.5)/N-1)*t;\n   // ray from (0,0,D) dir (u,v,-1)\n   const n=Math.sqrt(u*u+v*v+1),dx=u/n,dy=v/n,dz=-1/n;\n   const B=D*dz,C=D*D-1,disc=B*B-C;\n   if(disc<0){px[k]=px[k+1]=px[k+2]=0;px[k+3]=255;continue}\n   const s=-B-Math.sqrt(disc);let X=s*dx,Y=s*dy,Z=D+s*dz;\n   // view -> moon frame: undo pitch (about X) then yaw (about Y)\n   let Y2=Y*cb-Z*sb,Z2=Y*sb+Z*cb;Y=Y2;Z=Z2;\n   let X2=X*ca+Z*sa;Z2=-X*sa+Z*ca;X=X2;Z=Z2;\n   const lon=Math.atan2(X,Z),lat=Math.asin(Math.max(-1,Math.min(1,Y)));\n   let tx=((lon+Math.PI)/(2*Math.PI)*TW)|0,ty=((Math.PI/2-lat)/Math.PI*TH)|0;\n   if(tx>=TW)tx=TW-1;if(ty>=TH)ty=TH-1;const q=(ty*TW+tx)*4;\n   px[k]=T[q];px[k+1]=T[q+1];px[k+2]=T[q+2];px[k+3]=255}}\n ctx.putImageData(img,0,0)}\n[yaw,pitch,dist].forEach(e=>e.addEventListener(\'input\',draw));\nlet drag=null;\ncv.addEventListener(\'pointerdown\',e=>{drag={x:e.clientX,y:e.clientY,a:+yaw.value,b:+pitch.value};cv.setPointerCapture(e.pointerId)});\ncv.addEventListener(\'pointermove\',e=>{if(!drag)return;const f=180/cv.clientWidth;\n let na=drag.a-(e.clientX-drag.x)*f;na=((na+180)%360+360)%360-180;yaw.value=Math.round(na);\n pitch.value=Math.max(-90,Math.min(90,Math.round(drag.b+(e.clientY-drag.y)*f)));draw()});\ncv.addEventListener(\'pointerup\',()=>drag=null);\ncv.addEventListener(\'wheel\',e=>{e.preventDefault();dist.value=Math.max(1.3,Math.min(12,+dist.value*(e.deltaY>0?1.08:1/1.08)));draw()},{passive:false});\ndocument.querySelectorAll(\'button[data-p]\').forEach(bt=>bt.onclick=()=>{const[p,q,r]=bt.dataset.p.split(\',\');yaw.value=p;pitch.value=q;dist.value=r;draw()});\nconst sp=document.getElementById(\'spin\');\nsp.onclick=()=>{spinning=!spinning;sp.textContent=spinning?\'Stop ■\':\'Draaien ▶\';if(spinning)loop()};\nfunction loop(){if(!spinning)return;let v=+yaw.value+1;if(v>180)v-=360;yaw.value=v;draw();requestAnimationFrame(loop)}\n</script></body></html>'

def fit_circle(p):
    A = np.c_[2*p[:, 0], 2*p[:, 1], np.ones(len(p))]
    b = (p**2).sum(1)
    x = np.linalg.lstsq(A, b, rcond=None)[0]
    return x[0], x[1], np.sqrt(x[2] + x[0]**2 + x[1]**2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("foto"); ap.add_argument("-o", "--uit", default="maan_bol.html")
    ap.add_argument("--drempel", type=float, default=40, help="helderheidsdrempel 0-255 voor de maanschijf")
    ap.add_argument("--links", action="store_true", help="verlichte rand zit links")
    ap.add_argument("--cirkel", nargs=3, type=float, metavar=("CX", "CY", "R"))
    a = ap.parse_args()

    img = cv2.imread(a.foto, cv2.IMREAD_UNCHANGED)
    if img is None: sys.exit("Kan foto niet lezen: " + a.foto)
    img = img.astype(np.float32)
    if img.ndim == 3: img = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
    g = (img - img.min()) / max(img.max() - img.min(), 1e-6) * 255

    if a.cirkel:
        cx, cy, r = a.cirkel
    else:
        m = (cv2.GaussianBlur(g, (0, 0), 2) > a.drempel).astype(np.uint8)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
        cx, cy, r = fit_circle(c)
        for _ in range(3):  # alleen de verlichte rand gebruiken
            sel = c[c[:, 0] < cx + 0.1*r] if a.links else c[c[:, 0] > cx - 0.1*r]
            cx, cy, r = fit_circle(sel)
    print(f"Maanschijf: middelpunt ({cx:.1f}, {cy:.1f}), straal {r:.1f} px")
    chk = cv2.cvtColor(g.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    cv2.circle(chk, (int(cx), int(cy)), int(r), (0, 0, 255), 1)
    cv2.imwrite("controle_cirkel.png", chk)
    print("Controleer controle_cirkel.png: de rode cirkel moet precies op de verlichte rand liggen.")

    W, H = 2048, 1024
    lon = (np.arange(W) + .5) / W * 2*np.pi - np.pi
    lat = np.pi/2 - (np.arange(H) + .5) / H * np.pi
    LO, LA = np.meshgrid(lon, lat)
    X = np.cos(LA)*np.sin(LO); Y = np.sin(LA); Z = np.cos(LA)*np.cos(LO)
    tex = cv2.remap(g.astype(np.float32), (cx + r*X).astype(np.float32), (cy - r*Y).astype(np.float32),
                    cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    out = np.dstack([tex]*3)
    far = Z <= 0
    nod = np.zeros((H, W, 3), np.float32); nod[:] = (38, 30, 26)
    dl, db = np.degrees(LO) + 180, np.degrees(LA) + 90
    grid = (np.abs(dl % 15 - 7.5) > 7.0) | (np.abs(db % 15 - 7.5) > 7.0)
    nod[grid] = (70, 58, 50)
    out[far] = nod[far]
    ok, buf = cv2.imencode(".jpg", np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    html = TEMPLATE.replace("__B64__", base64.b64encode(buf).decode())
    open(a.uit, "w", encoding="utf-8").write(html)
    print("Klaar:", a.uit, "- open het in je browser.")

if __name__ == "__main__":
    main()
