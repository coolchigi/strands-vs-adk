import math, os
from PIL import Image, ImageDraw, ImageFont
SS = 4
OUT = 1.5
W,H=900*SS,450*SS
BG = (58, 24, 58); DIM = (140, 100, 136); LINE = (104, 54, 104); WHITE = (250, 238, 248); MUTED = (200, 168, 196)
STRANDS = (255, 168, 38); ADK = (96, 158, 255)
def font(s,b=False): return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf",s*SS)
F_T,F_N,F_L,F_TAG=font(21,True),font(11,True),font(13,True),font(11,True)
def mix(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def text_c(d,xy,s,f,fill):
    x,y=xy; bb=d.textbbox((0,0),s,font=f)
    d.text((x-(bb[2]-bb[0])/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),s,font=f,fill=fill)
def pw(d,label): bb=d.textbbox((0,0),label,font=F_N); return bb[2]-bb[0]+20*SS

def layout(d,labels,left,right):
    """place pills so gaps between them are equal, given real text widths"""
    ws=[pw(d,l) for l in labels]
    gap=(right-left-sum(ws))/(len(ws)-1)
    xs=[]; x=left
    for w in ws:
        xs.append(x+w/2); x+=w+gap
    return xs,ws

def pill(d,cx,cy,label,hot,col,w):
    d.rounded_rectangle([cx-w/2,cy-15*SS,cx+w/2,cy+15*SS],radius=7*SS,
                        fill=col if hot else BG,outline=col if hot else DIM,width=2*SS)
    text_c(d,(cx,cy),label,F_N,BG if hot else WHITE)

def arrow(d,x0,x1,y,col,dashed=False):
    if dashed:
        p=x0
        while p<x1-9*SS:
            q=min(p+6*SS,x1-9*SS); d.line([p,y,q,y],fill=col,width=2*SS); p=q+5*SS
    else:
        d.line([x0,y,x1-9*SS,y],fill=col,width=2*SS)
    d.polygon([(x1,y),(x1-9*SS,y-4*SS),(x1-9*SS,y+4*SS)],fill=col)

def row(d,y,col,head,labels,n_required,caption,t):
    track=y+30*SS
    text_c(d,(W//2,y-46*SS),head,F_L,col)
    xs,ws=layout(d,labels,150*SS,760*SS)
    for i in range(len(xs)-1):
        opt = i+1 >= n_required
        arrow(d,xs[i]+ws[i]/2+8*SS, xs[i+1]-ws[i+1]/2-4*SS, y,
              mix(BG,MUTED,0.45) if opt else LINE, dashed=opt)
    # pulse only crosses the required span
    stop = xs[n_required-1]
    path0 = xs[0]
    px = path0 + (stop-path0)*max(0.0,min(1.0,t))
    for i,l in enumerate(labels):
        opt = i >= n_required
        hot = (not opt) and abs(px-xs[i])<ws[i]/2+14*SS
        if opt:
            d.rounded_rectangle([xs[i]-ws[i]/2,y-15*SS,xs[i]+ws[i]/2,y+15*SS],radius=7*SS,
                                fill=BG,outline=mix(BG,MUTED,0.4),width=1*SS)
            text_c(d,(xs[i],y),l,F_N,mix(BG,MUTED,0.75))
        else:
            pill(d,xs[i],y,l,hot,col,ws[i])
    for j in range(9,0,-1):
        tt=max(0.0,min(1.0,t-j*0.012)); tx=path0+(stop-path0)*tt
        a=(1-j/9)**2; r=(2+3.2*a)*SS
        d.ellipse([tx-r,track-r,tx+r,track+r],fill=mix(BG,col,a*0.85))
    d.ellipse([px-6*SS,track-6*SS,px+6*SS,track+6*SS],fill=col)
    text_c(d,(W//2,track+26*SS),caption,F_TAG,MUTED)

FR=48; frames=[]
for k in range(FR):
    t=(k/FR)*1.3
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    text_c(d,(W//2,32*SS),"Where does a write land?",F_T,WHITE)
    row(d,142*SS,STRANDS,'STRANDS   agent.state.set("topic", ...)',
        ["agent.state","SessionManager","storage"],1,
        "straight onto the Agent. Persistence is opt in.",t)
    d.line([(90*SS,256*SS),(810*SS,256*SS)],fill=LINE,width=1*SS)
    row(d,352*SS,ADK,'ADK   output_key="research"',
        ["Event.state_delta","Runner","SessionService","session.state"],4,
        "through the event system, every time.",t)
    img=img.resize((int(900*OUT),int(450*OUT)),Image.LANCZOS)
    frames.append(img.convert("P",palette=Image.ADAPTIVE,colors=64))
out=os.path.join(os.path.dirname(__file__),"where-state-lands.gif")
frames[0].save(out,save_all=True,append_images=frames[1:],duration=93,loop=0,optimize=True,disposal=2)
print(out,os.path.getsize(out)//1024,"KB")
