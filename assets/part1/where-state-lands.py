import math, os
from PIL import Image, ImageDraw, ImageFont
W,H=900,450
BG=(13,17,23); DIM=(70,80,94); LINE=(38,45,57); WHITE=(226,233,242); MUTED=(128,140,158)
STRANDS=(255,153,0); ADK=(66,133,244)
def font(s,b=False): return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc",s,index=1 if b else 0)
F_T,F_N,F_L,F_TAG=font(21,True),font(11,True),font(13,True),font(11,True)
def mix(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def text_c(d,xy,s,f,fill):
    x,y=xy; bb=d.textbbox((0,0),s,font=f)
    d.text((x-(bb[2]-bb[0])/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),s,font=f,fill=fill)
def pw(d,label): bb=d.textbbox((0,0),label,font=F_N); return bb[2]-bb[0]+20

def layout(d,labels,left,right):
    """place pills so gaps between them are equal, given real text widths"""
    ws=[pw(d,l) for l in labels]
    gap=(right-left-sum(ws))/(len(ws)-1)
    xs=[]; x=left
    for w in ws:
        xs.append(x+w/2); x+=w+gap
    return xs,ws

def pill(d,cx,cy,label,hot,col,w):
    d.rounded_rectangle([cx-w/2,cy-15,cx+w/2,cy+15],radius=7,
                        fill=col if hot else BG,outline=col if hot else DIM,width=2)
    text_c(d,(cx,cy),label,F_N,BG if hot else WHITE)

def arrow(d,x0,x1,y,col,dashed=False):
    if dashed:
        p=x0
        while p<x1-9:
            q=min(p+6,x1-9); d.line([p,y,q,y],fill=col,width=2); p=q+5
    else:
        d.line([x0,y,x1-9,y],fill=col,width=2)
    d.polygon([(x1,y),(x1-9,y-4),(x1-9,y+4)],fill=col)

def row(d,y,col,head,labels,n_required,caption,t):
    track=y+30
    text_c(d,(W//2,y-46),head,F_L,col)
    xs,ws=layout(d,labels,150,760)
    for i in range(len(xs)-1):
        opt = i+1 >= n_required
        arrow(d,xs[i]+ws[i]/2+8, xs[i+1]-ws[i+1]/2-4, y,
              mix(BG,MUTED,0.45) if opt else LINE, dashed=opt)
    # pulse only crosses the required span
    stop = xs[n_required-1]
    path0 = xs[0]
    px = path0 + (stop-path0)*max(0.0,min(1.0,t))
    for i,l in enumerate(labels):
        opt = i >= n_required
        hot = (not opt) and abs(px-xs[i])<ws[i]/2+14
        if opt:
            d.rounded_rectangle([xs[i]-ws[i]/2,y-15,xs[i]+ws[i]/2,y+15],radius=7,
                                fill=BG,outline=mix(BG,MUTED,0.4),width=1)
            text_c(d,(xs[i],y),l,F_N,mix(BG,MUTED,0.75))
        else:
            pill(d,xs[i],y,l,hot,col,ws[i])
    for j in range(9,0,-1):
        tt=max(0.0,min(1.0,t-j*0.012)); tx=path0+(stop-path0)*tt
        a=(1-j/9)**2; r=2+3.2*a
        d.ellipse([tx-r,track-r,tx+r,track+r],fill=mix(BG,col,a*0.85))
    d.ellipse([px-6,track-6,px+6,track+6],fill=col)
    text_c(d,(W//2,track+26),caption,F_TAG,MUTED)

FR=72; frames=[]
for k in range(FR):
    t=(k/FR)*1.3
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    text_c(d,(W//2,32),"Where does a write land?",F_T,WHITE)
    row(d,142,STRANDS,'STRANDS   agent.state.set("topic", ...)',
        ["agent.state","SessionManager","storage"],1,
        "straight onto the Agent. Persistence is opt in.",t)
    d.line([(90,256),(810,256)],fill=LINE,width=1)
    row(d,352,ADK,'ADK   output_key="research"',
        ["Event.state_delta","Runner","SessionService","session.state"],4,
        "through the event system, every time.",t)
    frames.append(img.convert("P",palette=Image.ADAPTIVE,colors=96))
out=os.path.join(os.path.dirname(__file__),"where-state-lands.gif")
frames[0].save(out,save_all=True,append_images=frames[1:],duration=62,loop=0,optimize=True,disposal=2)
print(out,os.path.getsize(out)//1024,"KB")
