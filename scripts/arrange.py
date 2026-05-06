#!/usr/bin/env python3
"""
六爻完整装卦引擎
实现：纳甲 → 八宫定宫 → 世应定位 → 六亲 → 六神 → 日空

用法：
  python cast.py | python arrange.py          # 管道模式
  python arrange.py 0 1 2 1 3 0               # 直接传入六爻值
  python arrange.py 0 1 2 1 3 0 --json        # 输出 JSON
"""

import sys, json
from datetime import date, datetime

# ─────────────────────────────────────────────────────────────────────────────
# 基础对照表
# ─────────────────────────────────────────────────────────────────────────────

STEMS    = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 八卦编码（初爻=bit0，二爻=bit1，三爻=bit2）
# 坤000=0, 震001=1, 坎010=2, 兑011=3, 艮100=4, 离101=5, 巽110=6, 乾111=7
TRIGRAM_NAMES = {0:'坤',1:'震',2:'坎',3:'兑',4:'艮',5:'离',6:'巽',7:'乾'}

# 64卦名：key = 上卦编码*8 + 下卦编码
_N = TRIGRAM_NAMES
HEXAGRAM_NAMES = {
    # 上乾(7)
    7*8+7:'乾为天',   7*8+3:'天泽履',   7*8+5:'天火同人', 7*8+1:'天雷无妄',
    7*8+6:'天风姤',   7*8+2:'天水讼',   7*8+4:'天山遁',   7*8+0:'天地否',
    # 上兑(3)
    3*8+7:'泽天夬',   3*8+3:'兑为泽',   3*8+5:'泽火革',   3*8+1:'泽雷随',
    3*8+6:'泽风大过', 3*8+2:'泽水困',   3*8+4:'泽山咸',   3*8+0:'泽地萃',
    # 上离(5)
    5*8+7:'火天大有', 5*8+3:'火泽睽',   5*8+5:'离为火',   5*8+1:'火雷噬嗑',
    5*8+6:'火风鼎',   5*8+2:'火水未济', 5*8+4:'火山旅',   5*8+0:'火地晋',
    # 上震(1)
    1*8+7:'雷天大壮', 1*8+3:'雷泽归妹', 1*8+5:'雷火丰',   1*8+1:'震为雷',
    1*8+6:'雷风恒',   1*8+2:'雷水解',   1*8+4:'雷山小过', 1*8+0:'雷地豫',
    # 上巽(6)
    6*8+7:'风天小畜', 6*8+3:'风泽中孚', 6*8+5:'风火家人', 6*8+1:'风雷益',
    6*8+6:'巽为风',   6*8+2:'风水涣',   6*8+4:'风山渐',   6*8+0:'风地观',
    # 上坎(2)
    2*8+7:'水天需',   2*8+3:'水泽节',   2*8+5:'水火既济', 2*8+1:'水雷屯',
    2*8+6:'水风井',   2*8+2:'坎为水',   2*8+4:'水山蹇',   2*8+0:'水地比',
    # 上艮(4)
    4*8+7:'山天大畜', 4*8+3:'山泽损',   4*8+5:'山火贲',   4*8+1:'山雷颐',
    4*8+6:'山风蛊',   4*8+2:'山水蒙',   4*8+4:'艮为山',   4*8+0:'山地剥',
    # 上坤(0)
    0*8+7:'地天泰',   0*8+3:'地泽临',   0*8+5:'地火明夷', 0*8+1:'地雷复',
    0*8+6:'地风升',   0*8+2:'地水师',   0*8+4:'地山谦',   0*8+0:'坤为地',
}

# 八宫五行
PALACE_WUXING = {
    '乾':'金','兑':'金','离':'火','震':'木','巽':'木','坎':'水','艮':'土','坤':'土'
}

# 纳甲：各宫爻位地支（索引0=初爻，5=上爻）
PALACE_BRANCHES = {
    '乾': ['子','寅','辰','午','申','戌'],
    '兑': ['巳','未','酉','卯','丑','亥'],
    '离': ['巳','未','酉','亥','丑','卯'],
    '震': ['子','寅','辰','戌','申','午'],
    '巽': ['丑','卯','巳','酉','亥','丑'],
    '坎': ['寅','辰','午','子','戌','申'],
    '艮': ['辰','寅','子','申','午','辰'],
    '坤': ['未','巳','卯','丑','亥','酉'],
}

# 地支五行
BRANCH_WUXING = {
    '子':'水','亥':'水',
    '寅':'木','卯':'木',
    '巳':'火','午':'火',
    '申':'金','酉':'金',
    '辰':'土','戌':'土','丑':'土','未':'土',
}

# 五行相生（key 生 value）
SHENG = {'金':'水','水':'木','木':'火','火':'土','土':'金'}
# 五行相克（key 克 value）
KE    = {'金':'木','木':'土','土':'水','水':'火','火':'金'}

# 六神顺序
LIUSHEN = ['青龙','朱雀','勾陈','螣蛇','白虎','玄武']

# 日天干 → 六神起点索引（映射到 LIUSHEN 中的位置）
STEM_TO_SHEN_START = {0:0,1:0, 2:1,3:1, 4:2, 5:3, 6:4,7:4, 8:5,9:5}

# 月份 → 月支（建寅体系，粗略按公历月份）
MONTH_TO_BRANCH = {
    1:'丑',2:'寅',3:'卯',4:'辰',5:'巳',6:'午',
    7:'未',8:'申',9:'酉',10:'戌',11:'亥',12:'子'
}

# ─────────────────────────────────────────────────────────────────────────────
# 八宫卦位映射（算法生成）
# ─────────────────────────────────────────────────────────────────────────────

def _build_palace_map():
    """返回 {卦值(6-bit): (宫名, 宫内类型, 世爻位置1-6)} 完整字典。"""
    result = {}
    tname_to_code = {v: k for k, v in TRIGRAM_NAMES.items()}
    PALACE_ORDER = ['乾','兑','离','震','巽','坎','艮','坤']
    TYPES = ['纯卦','一世','二世','三世','四世','五世','游魂','归魂']
    WORLDS = [6, 1, 2, 3, 4, 5, 4, 3]

    for palace in PALACE_ORDER:
        p = tname_to_code[palace]
        pure = (p << 3) | p          # 两个相同卦构成纯卦

        seq = [pure]
        cur = pure
        for bit in range(5):         # 翻转 bit0→bit4 得到一世到五世
            cur ^= (1 << bit)
            seq.append(cur)

        wu_shi  = seq[5]
        you_hun = wu_shi ^ (1 << 3)  # 游魂：五世的四爻（bit3）再翻
        seq.append(you_hun)

        gui_hun = (you_hun & 0b111000) | p   # 归魂：游魂下卦换回本宫
        seq.append(gui_hun)

        for idx, hexval in enumerate(seq):
            result[hexval] = (palace, TYPES[idx], WORLDS[idx])

    return result

PALACE_MAP = _build_palace_map()

# ─────────────────────────────────────────────────────────────────────────────
# 六亲 / 日期 / 日空
# ─────────────────────────────────────────────────────────────────────────────

def get_liuqin(palace_wx, branch_wx):
    """根据宫位五行与爻支五行，返回六亲名称。"""
    if branch_wx == palace_wx:
        return '兄弟'
    if SHENG[branch_wx] == palace_wx:   # 生我者
        return '父母'
    if SHENG[palace_wx] == branch_wx:   # 我生者
        return '子孙'
    if KE[branch_wx] == palace_wx:      # 克我者
        return '官鬼'
    return '妻财'                        # 我克者


def _date_to_gz(d):
    """返回 (天干索引, 地支索引, 六十甲子序) for 给定 date。"""
    REF = date(2000, 1, 1)   # 2000-01-01 = 甲子日，序号 0
    delta = (d - REF).days % 60
    return delta % 10, delta % 12, delta


def get_kongwang(gz_seq):
    """根据六十甲子序号，返回日空地支列表。"""
    xun = gz_seq // 10     # 旬索引 0-5
    b1  = (10 - 2 * xun) % 12
    b2  = (11 - 2 * xun) % 12
    return [BRANCHES[b1], BRANCHES[b2]]

# ─────────────────────────────────────────────────────────────────────────────
# 主装卦函数
# ─────────────────────────────────────────────────────────────────────────────

def arrange(line_values, dt=None):
    """
    Parameters
    ----------
    line_values : list[int]  6个元素，索引0=初爻，5=上爻
                  0=老阴  1=少阳  2=少阴  3=老阳
    dt          : datetime  起卦时间，默认 now()

    Returns
    -------
    dict  完整盘面数据
    """
    if dt is None:
        dt = datetime.now()
    d = dt.date() if hasattr(dt, 'date') else dt

    # ── 本卦 / 变卦 6-bit 整数 ──
    ben_bits  = 0
    bian_bits = 0
    for i, v in enumerate(line_values):
        yang    = v in (1, 3)
        dynamic = v in (0, 3)
        if yang:
            ben_bits  |= (1 << i)
        bian_yang = (not yang) if dynamic else yang
        if bian_yang:
            bian_bits |= (1 << i)

    if ben_bits not in PALACE_MAP:
        raise ValueError(f'装卦失败：找不到卦值 {bin(ben_bits)} 对应的宫位')

    palace, palace_type, shi_yao = PALACE_MAP[ben_bits]
    ying_yao = (shi_yao - 1 + 3) % 6 + 1   # 世应相差3位

    # ── 纳甲 / 六亲 ──
    branches   = PALACE_BRANCHES[palace]
    palace_wx  = PALACE_WUXING[palace]
    liuqin     = [get_liuqin(palace_wx, BRANCH_WUXING[b]) for b in branches]

    # ── 日期干支 / 日空 ──
    stem_idx, branch_idx, gz_seq = _date_to_gz(d)
    day_stem   = STEMS[stem_idx]
    day_branch = BRANCHES[branch_idx]
    month_branch = MONTH_TO_BRANCH[d.month]
    kongwang   = get_kongwang(gz_seq)

    # ── 六神 ──
    shen_start = STEM_TO_SHEN_START[stem_idx]
    liushen    = [LIUSHEN[(shen_start + i) % 6] for i in range(6)]

    # ── 卦名 ──
    ben_name  = HEXAGRAM_NAMES.get((ben_bits >> 3)*8 + (ben_bits & 7), '未知卦')
    has_dyn   = any(v in (0, 3) for v in line_values)
    bian_name = HEXAGRAM_NAMES.get((bian_bits >> 3)*8 + (bian_bits & 7)) if has_dyn else None

    # ── 各爻详情 ──
    SYMBOLS = ['──×──', '─────', '── ──', '────○']
    yao_info = []
    for i, v in enumerate(line_values):
        yang    = v in (1, 3)
        dynamic = v in (0, 3)
        yao_info.append({
            'position':   i + 1,
            'label':      ['初爻','二爻','三爻','四爻','五爻','上爻'][i],
            'value':      v,
            'type':       ['老阴','少阳','少阴','老阳'][v],
            'is_yang':    yang,
            'is_dynamic': dynamic,
            'symbol':     SYMBOLS[v],
            'branch':     branches[i],
            'branch_wx':  BRANCH_WUXING[branches[i]],
            'liuqin':     liuqin[i],
            'liushen':    liushen[i],
            'is_shi':     (i + 1) == shi_yao,
            'is_ying':    (i + 1) == ying_yao,
            'in_kongwang': branches[i] in kongwang,
        })

    return {
        'datetime':     dt.strftime('%Y年%m月%d日 %H:%M'),
        'day_stem':     day_stem,
        'day_branch':   day_branch,
        'day_ganzhi':   f'{day_stem}{day_branch}',
        'month_branch': month_branch,
        'kongwang':     kongwang,
        'ben_gua':      ben_name,
        'bian_gua':     bian_name,
        'palace':       palace,
        'palace_type':  palace_type,
        'palace_wx':    palace_wx,
        'shi_yao':      shi_yao,
        'ying_yao':     ying_yao,
        'dynamic_count': sum(1 for v in line_values if v in (0, 3)),
        'yao_info':     yao_info,   # 索引0=初爻
    }

# ─────────────────────────────────────────────────────────────────────────────
# 格式化输出
# ─────────────────────────────────────────────────────────────────────────────

def format_panbao(r):
    W = 56
    sep  = '━' * W
    thin = '─' * W
    lines = [sep]

    # 标题行
    kw = '、'.join(r['kongwang'])
    lines.append(f"  起卦时间：{r['datetime']}")
    lines.append(f"  日柱：{r['day_ganzhi']}  月支：{r['month_branch']}  日空：{kw}")
    lines.append(thin)

    # 卦名行
    pt = r['palace_type']
    pn = r['palace']
    si = r['shi_yao']
    yi = r['ying_yao']
    lines.append(f"  本卦：{r['ben_gua']}（{pn}宫·{pt}  世{si}爻·应{yi}爻）")
    if r['bian_gua']:
        lines.append(f"  变卦：{r['bian_gua']}")
    if r['dynamic_count'] > 3:
        lines.append(f"  ⚠ 动爻{r['dynamic_count']}个，卦象混沌，建议重起")
    lines.append(sep)

    # 表头
    lines.append(f"  {'六神':<4}{'爻位':<4}{'六亲':<4}{'卦象':<8}{'地支':<5}{'备注'}")
    lines.append(thin)

    # 爻位行：从上爻到初爻（上→下显示）
    for yao in reversed(r['yao_info']):
        marker = ''
        if yao['is_shi']:   marker = '◀ 世'
        elif yao['is_ying']: marker = '◀ 应'

        extra = []
        if yao['is_dynamic']:    extra.append('动')
        if yao['in_kongwang']:   extra.append('空')
        note = marker + ('  [' + '·'.join(extra) + ']' if extra else '')

        wx = yao['branch_wx']
        lines.append(
            f"  {yao['liushen']:<4}{yao['label']:<4}{yao['liuqin']:<4}"
            f"{yao['symbol']:<9}{yao['branch']}{wx}  {note}"
        )

    lines.append(sep)
    return '\n'.join(lines)

# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    line_values = None
    dt = datetime.now()

    # 模式一：命令行参数（优先）
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) >= 6:
        try:
            line_values = [int(x) for x in args[:6]]
        except ValueError:
            pass

    # 模式二：管道（来自 cast.py）
    if line_values is None:
        import select
        has_stdin = not sys.stdin.isatty() or (
            sys.platform != 'win32' and
            select.select([sys.stdin], [], [], 0.0)[0]
        )
        if has_stdin:
            try:
                raw = json.load(sys.stdin)
                line_values = [l['value'] for l in raw['lines']]
                try:
                    dt = datetime.strptime(raw['datetime'], '%Y年%m月%d日 %H:%M')
                except Exception:
                    pass
            except Exception:
                pass

    if line_values is None or len(line_values) != 6:
        print("用法: python arrange.py <爻1> <爻2> <爻3> <爻4> <爻5> <爻6> [--json]")
        print("  或: python cast.py | python arrange.py")
        print("爻值: 0=老阴  1=少阳  2=少阴  3=老阳")
        sys.exit(1)

    result = arrange(line_values, dt)

    if '--json' in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_panbao(result))
