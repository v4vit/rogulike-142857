import random

# 精确模拟：带射程的沿路机枪防守 + 太阳能经济
# 地图：道路 row19 col4..39；可建区 row18 / row20
# 玩家策略：太阳能 2/s 产能；能量够了就在上下两排建机枪，形成沿路火力带
random.seed(42)
CELL=24
ROAD_Y=19*CELL+CELL/2          # 道路中心 y = 468
BASE_EDGE_X=(2+2)*CELL         # 基地右缘 x = 96
GUN_DMG=14; GUN_CD=0.5         # DPS 28
GUN_RANGE=3*CELL               # 72
SOLAR_RATE=2.0; SOLAR_COST=40; GUN_COST=60
MAX_ENERGY=400; START_ENERGY=200
BASE_HP=400
MON={'red':{'w':1,'sp':1.0},'green':{'w':3,'sp':0.6},'blue':{'w':2,'sp':1.5},'yellow':{'w':2,'sp':1.0}}
KEYS=list(MON)
def rk():
    tot=sum(MON[k]['w'] for k in KEYS); r=random.random()*tot
    for k in KEYS:
        r-=MON[k]['w']
        if r<=0: return k
    return 'red'
def wb(n): return 8+3*n
def whp(n): return 15+3*n
def wsp(n): return 1+0.02*n

def run(maxwaves=60):
    energy=START_ENERGY
    solars=0; guns=[]   # guns: list of col on row18 or row20 (塔心位置)
    gun_cols=[]  # 记录火力带位置
    wave=1; base_hp=BASE_HP; kills=0
    active=[]   # {k, x(px, center), hp, tobase(px edge reached)}
    # 布局策略：每隔2格在上下排交替建枪，先建够一段
    def add_gun(col,row):
        nonlocal energy
        if energy<GUN_COST: return False
        energy-=GUN_COST
        guns.append({'x':col*CELL+CELL/2,'y':row*CELL+CELL/2,'cd':0,'range':GUN_RANGE})
        return True
    # 太阳能格子也有限：上限按需要
    def add_solar():
        nonlocal energy, solars
        if energy<SOLAR_COST or solars>=12: return False
        energy-=SOLAR_COST; solars+=1; return True

    # 开局：1太阳能 + 尽量建枪
    add_solar()
    for c in range(6,39,2):     # 沿路从右往左每隔2格
        if not add_gun(c,18): break
        if not add_gun(c,20): break

    t=0.0; dt=0.1
    spawnq=[]; qi=0; spawn_timer=0; acc=0
    def start_wave(n):
        nonlocal spawnq, qi, acc
        b=wb(n); q=[]; a=0
        while a<b:
            k=rk(); a+=MON[k]['w']; q.append(k)
        spawnq=q; qi=0; acc=0

    start_wave(wave)
    while not (base_hp<=0) and wave<=maxwaves:
        t+=dt
        energy=min(MAX_ENERGY, energy+solars*SOLAR_RATE*dt)
        # 经济策略：能量富余时补太阳能/扩火力带
        if energy>=GUN_COST*2:
            # 在已有火力带右侧再延伸(靠基地侧加密) 简化：若能量多就加枪到火力带
            if len(guns)<18:
                # 找一个空位
                c=4+(len(guns)%35)
                row=20 if len(guns)%2 else 18
                add_gun(c,row)
        if solars<10 and energy>60:
            add_solar()

        # 出怪
        spawn_timer+=dt
        if spawn_timer>=1.1 and qi<len(spawnq):
            spawn_timer-=1.1
            k=spawnq[qi]; qi+=1
            hp=whp(wave)
            active.append({'k':k,'x':39*CELL+CELL/2,'hp':hp,'edge':False})
        # 移动+受击
        sp_mul=wsp(wave)
        alive=[]
        for m in active:
            sp=MON[m['k']]['sp']*sp_mul*CELL*0.5   # px/s
            m['x']-=sp*dt
            # 受击：所有在射程内且该枪冷却好的枪攻击
            for g in guns:
                if m['x']<=BASE_EDGE_X: continue   # 到达基地不再被枪打(可选)
                dx=m['x']-g['x']; dy=ROAD_Y-g['y']
                if dx*dx+dy*dy<=g['range']*g['range']:
                    m['hp']-=GUN_DMG*dt*(1/GUN_CD)
            if m['x']-MON[m['k']]['sp']*3/CELL <= BASE_EDGE_X/CELL*0.5:  # 接近基地
                pass
            if m['x']<=BASE_EDGE_X+CELL*0.5:
                m['edge']=True
            if m['hp']<=0:
                kills+=1; continue
            if m['edge']:
                base_hp-=10*dt
            alive.append(m)
        active=alive

        # 下一波
        if qi>=len(spawnq):
            fw=sum(MON[m['k']]['w'] for m in active if not m['edge'])
            if fw<=wb(wave)*0.5:
                wave+=1; start_wave(wave)
    return wave, kills, base_hp, solars, len(guns)

w,k,hp,s,g=run()
print(f"到达第{w}波  击杀{k}  基地血{hp:.0f}  太阳能{s}  机枪{g}")
