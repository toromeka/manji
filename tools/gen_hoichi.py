# 耳無芳一の話（小泉八雲・戸川明三訳、青空文庫 図書カード42927）→ .manjiz 用の章ファイルを生成
import re, json, os
D='/workspace/manji_engine/samples/hoichi_src/'
t=open('/tmp/hoichi.txt').read()
secs=[s.strip() for s in re.split(r'\n\s*\n\s*\n+',t) if s.strip()]
SPK=['侍','侍','芳一','芳一','侍','老女','芳一','老女','老女','住職','芳一','下男','下男','下男','芳一','住職','住職','侍','侍','侍','侍','侍','住職','住職','住職','住職']
CAST={"芳一":{"color":"#e8d8a8","pos":"left"},"侍":{"color":"#ff5a5a","pos":"right"},"老女":{"color":"#c8a0ff","pos":"right"},"住職":{"color":"#8fd0ff","pos":"right"},"下男":{"color":"#b8c8a0","pos":"right"}}
CH=[([0,1,2],"壇ノ浦の怨霊","drone","dusk"),([3],"夏の夜の訪問者","horror","night"),([4,5],"七夜の約束","mystery","night"),([6],"雨の墓地","horror","horror"),([7,8],"般若心経","drone","black"),([9,10],"耳無芳一","wa_solemn","dawn")]
qi=[0]
def chunks(s,lim):
    # 文の切れ目（。！？…）で分け、なお長ければ「、」「――」で分ける。本文は一字も変えない
    parts=re.findall(r'.*?(?:[。！？]|……|$)',s); parts=[p for p in parts if p]
    out=[]
    for p in parts:
        while len(p)>lim:
            cut=-1
            for m in re.finditer(r'、|――',p):
                if m.end()<=lim: cut=m.end()
            if cut<lim*0.35: cut=lim
            out.append(p[:cut]); p=p[cut:]
        out.append(p)
    # 短すぎる断片は前とつなぐ
    res=[]
    for p in out:
        if res and len(res[-1])+len(p)<=lim and (len(p)<12 or len(res[-1])<12): res[-1]+=p
        else: res.append(p)
    return [r for r in res if r]
def build(ci,secids,title,bgm,sky,last):
    ev=[]; prev=[0]
    def add(e,gap=None):
        e["wait"]=gap if gap is not None else int(prev[0]*70+900); ev.append(e)
        prev[0]=len(e.get("text","")) if e["type"] in("narr","say") else 0
    sk={"sky":sky} if sky!="black" else {"sky":"black"}
    add({"type":"fx","fx":"fade","to":1,"dur":0},0)
    add({"type":"fx","fx":"bg","bg":"floor" if ci in(1,4) else "sea" if ci==0 else "hills","stars":ci!=4,"dim":0.35,**sk},0)
    add({"type":"fx","fx":"tint","preset":"horror" if ci in(3,4) else "night" if ci!=5 else "cold","amount":0.7},0)
    add({"type":"fx","fx":"weather","kind":"rain" if ci==3 else "fog","amount":1.2 if ci==3 else 0.6},0)
    add({"type":"fx","fx":"bgm","preset":bgm},0)
    add({"type":"fx","fx":"fadein","dur":2200},200)
    add({"type":"caption","text":"第%s話　%s"%("一二三四五六"[ci],title),"dur":3400},400)
    if ci==0: add({"type":"se","text":"ゴォーン……","se":"kane","pos":"top","dur":2600},300)
    biwa=False
    for si in secids:
        for para in [p.strip('　 ') for p in secs[si].split('\n') if p.strip()]:
            segs=re.split(r'(『[^』]*』)',para)
            for sg in segs:
                if not sg: continue
                if sg.startswith('『'):
                    who=SPK[qi[0]]; qi[0]+=1; body=sg[1:-1]
                    cs=chunks(body,64)
                    for k,c in enumerate(cs):
                        e={"type":"say","who":who,"text":c,"dur":int(len(c)*95+1800)}
                        if who=='侍' and ci in(1,4): e["eff"]="shake" if '！' in c or c=='芳一' else "none"
                        if who=='侍' and ci==4: e["size"]=26
                        add(e)
                        if who=='侍' and ci==4 and k==0 and c.startswith('芳一'):
                            add({"type":"fx","fx":"shake","power":8,"dur":500},300); add({"type":"fx","fx":"flash","color":"#400000","strength":0.5,"dur":300},0)
                else:
                    for c in chunks(sg.strip('　 '),96):
                        if not c.strip(): continue
                        add({"type":"narr","text":c})
                        if '跫音' in c or '足踏み' in c: add({"type":"se","text":"ザッ……ザッ……","se":"steps","pos":"seR","dur":2400},400)
                        if ('琵琶' in c) and not biwa: biwa=True; add({"type":"se","text":"ベン……ベベン","se":"biwa","pos":"seL","dur":2400},300)
                        if '鬼火' in c or '霊火' in c:
                            add({"type":"fx","fx":"flash","color":"#3050ff","strength":0.35,"dur":600},200)
                            add({"type":"fx","fx":"spot","x":0.5,"y":0.5,"r":0.35,"dim":0.6,"dur":3000},0)
                        if '苦悶の声' in c or '哭き悲し' in c: add({"type":"fx","fx":"wave","amp":6,"freq":3,"speed":2,"dur":4000},200)
                        if '引きちぎられた' in c:
                            add({"type":"fx","fx":"flash","color":"#ff0000","strength":0.8,"dur":250},0)
                            add({"type":"fx","fx":"shake","power":18,"dur":900},0)
                            add({"type":"impact","text":"――！","size":90,"color":"#ffdddd","stroke":"#400000","se":"impact","dur":1500,"pos":{"x":0.5,"y":0.45}},200)
                        if '提灯' in c and ci==3: add({"type":"fx","fx":"lightning","x":0.7},400)
                        if '血' in c: add({"type":"fx","fx":"tint","add":"#300000","amount":0.6,"dur":1500},0)
    add({"type":"fx","fx":"fadeout","dur":2500},2500)
    d={"manji":"1.0","title":title,"author":"小泉八雲（戸川明三 訳）","source":"青空文庫　小泉八雲「耳無芳一の話」戸川明三訳（図書カード42927）",
       "settings":{"charMs":70,"endText":"— 完 —" if last else "— つづく —","endHold":3000},"events":ev}
    fn="chapters/%02d.manji"%(ci+1)
    json.dump(d,open(D+fn,'w'),ensure_ascii=False,indent=1)
    return {"file":fn,"title":title}
chs=[build(i,*c,last=(i==len(CH)-1)) for i,c in enumerate(CH)]
assert qi[0]==len(SPK)
man={"manji_archive":"1.0","title":"耳無芳一の話","author":"小泉八雲（戸川明三 訳）","unit":"話",
 "description":"壇ノ浦に沈んだ平家の怨霊に招かれ、夜ごと琵琶を語る盲目の法師・芳一。住職は芳一の身体じゅうに経文を書くが……。本文は青空文庫の戸川明三訳をそのまま使用（全6話）。",
 "source":"青空文庫　小泉八雲「耳無芳一の話」戸川明三訳（図書カード42927、底本：「小泉八雲全集第八卷家庭版」第一書房 1937年、入力：京都大学電子テクスト研究会入力班、校正：京都大学電子テクスト研究会校正班（大久保ゆう））",
 "cast":CAST,"chapters":chs}
json.dump(man,open(D+'manifest.json','w'),ensure_ascii=False,indent=1)
# 検証：本文がすべて使われているか
used=''.join(e['text'] for c in chs for e in json.load(open(D+c['file']))['events'] if e['type'] in('narr','say'))
src=re.sub(r'[『』\s　]','',t); u=re.sub(r'[\s　]','',used)
print('verbatim', src==u, len(src), len(u))
