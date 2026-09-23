import math, os
from PIL import Image, ImageDraw, ImageFont

SS = 4
OUT = 1.5
W,H = 900*SS,592*SS
BG = (58, 24, 58); DIM = (140, 100, 136); LINE = (104, 54, 104); WHITE = (250, 238, 248); MUTED = (200, 168, 196)
STRANDS = (255, 168, 38); ADK = (96, 158, 255)
def font(s,b=False): return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf",s*SS)
F_T,F_N,F_L,F_TAG=font(21,True),font(12,True),font(13,True),font(11,True)
def mix(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def text_c(d,xy,s,f,fill):
    x,y=xy; bb=d.textbbox((0,0),s,font=f)
    d.text((x-(bb[2]-bb[0])/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),s,font=f,fill=fill)

NODES=["Researcher","Curriculum","Teacher","Feedback"]
XS=[172*SS,364*SS,556*SS,742*SS]
TRACK=30*SS
# Feedback sends work back to any of the three, and picks which one needs another pass
TARGETS=[0,1,2]
DEPTH=[86*SS,64*SS,42*SS]

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
    d.rounded_rectangle([cx-w/2-11*SS,cy-h/2-8*SS,cx+w/2+11*SS,cy+h/2+8*SS],radius=7*SS,
                        fill=col if hot else BG,outline=col if hot else DIM,width=2*SS)
    text_c(d,(cx,cy),label,F_N,BG if hot else WHITE)

def dashed_box(d,box,col,dash=7*SS,gap=6*SS,w=2*SS,r=16*SS):
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
    text_c(d,(W//2,y-48*SS),name,F_L,col)
    for i in range(3):
        d.line([XS[i]+56*SS,y,XS[i+1]-56*SS,y],fill=LINE,width=2*SS)
        d.polygon([(XS[i+1]-56*SS,y),(XS[i+1]-64*SS,y-4*SS),(XS[i+1]-64*SS,y+4*SS)],fill=LINE)
    if outside:
        dashed_box(d,(XS[0]-84*SS,y-28*SS,XS[3]+84*SS,ty+12*SS),mix(BG,col,0.45))
        text_c(d,(XS[0]-12*SS,y-41*SS),"Workflow graph",F_TAG,mix(BG,col,0.7))
    # all three return paths, the active one lit
    for k,tgt in enumerate(TARGETS):
        ap=arc(XS[3],XS[tgt],ty,DEPTH[k]*ds)
        live = (k==which)
        d.line(ap,fill=col if live else mix(BG,col,0.22),width=(2 if live else 1)*SS)
        ex,ey=ap[-1]; qx,qy=ap[-4]
        ang=math.atan2(ey-qy,ex-qx); L,Wd=10*SS,4.5*SS
        d.polygon([(ex,ey),
                   (ex-L*math.cos(ang)+Wd*math.sin(ang),ey-L*math.sin(ang)-Wd*math.cos(ang)),
                   (ex-L*math.cos(ang)-Wd*math.sin(ang),ey-L*math.sin(ang)+Wd*math.cos(ang))],
                  fill=col if live else mix(BG,col,0.3))
    path=lap_path(y,which,ds)
    px,py=walk(path,local)
    for i,n in enumerate(NODES):
        pill(d,XS[i],y,n,abs(px-XS[i])<40*SS and abs(py-ty)<10*SS,col)
    for j in range(9,0,-1):
        tx,tyy=walk(path,local-j*0.012); a=(1-j/9)**2; r=(2+3.2*a)*SS
        d.ellipse([tx-r,tyy-r,tx+r,tyy+r],fill=mix(BG,col,a*0.85))
    d.ellipse([px-6*SS,py-6*SS,px+6*SS,py+6*SS],fill=col)
    cap = "every edge lives in the graph" if not outside else "every edge lives outside it"
    text_c(d,(W//2, ty+DEPTH[0]*ds+22*SS), cap, F_TAG, col)

FR=45; frames=[]
for k in range(FR):
    t=k/FR
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    text_c(d,(W//2,30*SS),"Feedback reviews all three. Where do the",F_T,WHITE)
    text_c(d,(W//2,56*SS),"revision paths live?",F_T,WHITE)
    panel(d,160*SS,STRANDS,"STRANDS",t,False)
    d.line([(90*SS,322*SS),(810*SS,322*SS)],fill=LINE,width=1*SS)
    panel(d,410*SS,ADK,"ADK",t,True)
    img=img.resize((int(900*OUT),int(592*OUT)),Image.LANCZOS)
    frames.append(img.convert("P",palette=Image.ADAPTIVE,colors=64))
out=os.path.join(os.path.dirname(__file__),"revision-loop.gif")
frames[0].save(out,save_all=True,append_images=frames[1:],duration=115,loop=0,optimize=True,disposal=2)
print(out,os.path.getsize(out)//1024,"KB")
