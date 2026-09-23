import math, os
from PIL import Image, ImageDraw, ImageFont

W,H = 900,592
BG = (58, 24, 58); DIM = (140, 100, 136); LINE = (104, 54, 104); WHITE = (250, 238, 248); MUTED = (200, 168, 196)
STRANDS = (255, 168, 38); ADK = (96, 158, 255)
def font(s,b=False): return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf",s)
F_T,F_N,F_L,F_TAG=font(21,True),font(12,True),font(13,True),font(11,True)
def mix(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def text_c(d,xy,s,f,fill):
    x,y=xy; bb=d.textbbox((0,0),s,font=f)
    d.text((x-(bb[2]-bb[0])/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),s,font=f,fill=fill)

NODES=["Researcher","Curriculum","Teacher","Feedback"]
XS=[172,364,556,742]
TRACK=30
# Feedback sends work back to any of the three, and picks which one needs another pass
TARGETS=[0,1,2]
DEPTH=[86,64,42]

def arc(x_from,x_to,y,depth,n=52):
    cx,rx=(x_from+x_to)/2,(x_from-x_to)/2
    return [(cx+rx*math.cos(math.pi*i/n), y+depth*math.sin(math.pi*i/n)) for i in range(n+1)]

def lap_path(y,which,dscale):
    ty=y+TRACK
    tgt=TARGETS[which]
    fwd=[(x,ty) for x in XS[tgt:]]
    return fwd+arc(XS[3],XS[tgt],ty,DEPTH[which]*dscale)

def walk(path,t):
    seg=[math.dist(path[i],path[i+1]) for i in range(len(path)-1)]
    tot=sum(seg); want=max(0.0,min(1.0,t))*tot; acc=0
    for i,s in enumerate(seg):
        if acc+s>=want:
            f=(want-acc)/s if s else 0
            return (path[i][0]+(path[i+1][0]-path[i][0])*f, path[i][1]+(path[i+1][1]-path[i][1])*f)
        acc+=s
    return path[-1]

def pill(d,cx,cy,label,hot,col):
    bb=d.textbbox((0,0),label,font=F_N); w,h=bb[2]-bb[0],bb[3]-bb[1]
    d.rounded_rectangle([cx-w/2-11,cy-h/2-8,cx+w/2+11,cy+h/2+8],radius=7,
                        fill=col if hot else BG,outline=col if hot else DIM,width=2)
    text_c(d,(cx,cy),label,F_N,BG if hot else WHITE)

def dashed_box(d,box,col,dash=7,gap=6,w=2,r=16):
    x0,y0,x1,y1=box
    def run(a,b,fixed,horiz):
        p=a
        while p<b:
            q=min(p+dash,b)
            d.line([p,fixed,q,fixed] if horiz else [fixed,p,fixed,q],fill=col,width=w)
            p=q+gap
    run(x0+r,x1-r,y0,True); run(x0+r,x1-r,y1,True)
    run(y0+r,y1-r,x0,False); run(y0+r,y1-r,x1,False)

def panel(d,y,col,name,t,outside):
    ds = 1.0 if outside else 0.72
    ty=y+TRACK
    which=int(t*len(TARGETS))%len(TARGETS)
    local=(t*len(TARGETS))%1.0
    text_c(d,(W//2,y-48),name,F_L,col)
    for i in range(3):
        d.line([XS[i]+56,y,XS[i+1]-56,y],fill=LINE,width=2)
        d.polygon([(XS[i+1]-56,y),(XS[i+1]-64,y-4),(XS[i+1]-64,y+4)],fill=LINE)
    if outside:
        dashed_box(d,(XS[0]-84,y-28,XS[3]+84,ty+12),mix(BG,col,0.45))
        text_c(d,(XS[0]-12,y-41),"Workflow graph",F_TAG,mix(BG,col,0.7))
    # all three return paths, the active one lit
    for k,tgt in enumerate(TARGETS):
        ap=arc(XS[3],XS[tgt],ty,DEPTH[k]*ds)
        live = (k==which)
        d.line(ap,fill=col if live else mix(BG,col,0.22),width=2 if live else 1)
        ex,ey=ap[-1]; qx,qy=ap[-4]
        ang=math.atan2(ey-qy,ex-qx); L,Wd=10,4.5
        d.polygon([(ex,ey),
                   (ex-L*math.cos(ang)+Wd*math.sin(ang),ey-L*math.sin(ang)-Wd*math.cos(ang)),
                   (ex-L*math.cos(ang)-Wd*math.sin(ang),ey-L*math.sin(ang)+Wd*math.cos(ang))],
                  fill=col if live else mix(BG,col,0.3))
    path=lap_path(y,which,ds)
    px,py=walk(path,local)
    for i,n in enumerate(NODES):
        pill(d,XS[i],y,n,abs(px-XS[i])<40 and abs(py-ty)<10,col)
    for j in range(9,0,-1):
        tx,tyy=walk(path,local-j*0.012); a=(1-j/9)**2; r=2+3.2*a
        d.ellipse([tx-r,tyy-r,tx+r,tyy+r],fill=mix(BG,col,a*0.85))
    d.ellipse([px-6,py-6,px+6,py+6],fill=col)
    cap = "every edge lives in the graph" if not outside else "every edge lives outside it"
    text_c(d,(W//2, ty+DEPTH[0]*ds+22), cap, F_TAG, col)

FR=72; frames=[]
for k in range(FR):
    t=k/FR
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    text_c(d,(W//2,30),"Feedback reviews all three. Where do the",F_T,WHITE)
    text_c(d,(W//2,56),"revision paths live?",F_T,WHITE)
    panel(d,160,STRANDS,"STRANDS",t,False)
    d.line([(90,322),(810,322)],fill=LINE,width=1)
    panel(d,410,ADK,"ADK",t,True)
    frames.append(img.convert("P",palette=Image.ADAPTIVE,colors=64))
out=os.path.join(os.path.dirname(__file__),"revision-loop.gif")
frames[0].save(out,save_all=True,append_images=frames[1:],duration=72,loop=0,optimize=True,disposal=2)
print(out,os.path.getsize(out)//1024,"KB")
