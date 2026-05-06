#!/usr/bin/env python3
"""
六爻掷硬币模拟器
三枚硬币法：0=字(阴)，1=花(阳)

三枚之和映射：
  0 → 老阴  (三字，动爻，阴变阳)
  1 → 少阳  (两字一花，静爻，阳)
  2 → 少阴  (一字两花，静爻，阴)
  3 → 老阳  (三花，动爻，阳变阴)

用法：
  python cast.py
  python cast.py | python arrange.py
"""
import random
import json
from datetime import datetime


TYPE_NAMES = ['老阴', '少阳', '少阴', '老阳']
SYMBOLS    = ['──×──', '─────', '── ──', '────○']
IS_YANG    = [False, True, False, True]
IS_DYNAMIC = [True, False, False, True]


def toss_line():
    coins = [random.randint(0, 1) for _ in range(3)]
    value = sum(coins)
    return {
        'coins': coins,
        'value': value,
        'type': TYPE_NAMES[value],
        'symbol': SYMBOLS[value],
        'is_yang': IS_YANG[value],
        'is_dynamic': IS_DYNAMIC[value],
    }


def cast_hexagram():
    lines = []
    for pos in range(1, 7):          # 初爻(1) → 上爻(6)
        line = toss_line()
        line['position'] = pos
        line['label'] = ['初爻','二爻','三爻','四爻','五爻','上爻'][pos - 1]
        lines.append(line)
    return lines


if __name__ == '__main__':
    dt = datetime.now()
    lines = cast_hexagram()

    # 预览（写到 stderr，不影响管道）
    import sys
    print("[ 掷卦结果 ]", file=sys.stderr)
    for ln in reversed(lines):
        dyn = ' ← 动爻' if ln['is_dynamic'] else ''
        print(f"  {ln['label']}  {ln['symbol']}  {ln['type']}{dyn}", file=sys.stderr)
    dynamic_count = sum(1 for l in lines if l['is_dynamic'])
    if dynamic_count > 3:
        print(f"\n⚠  动爻数量为 {dynamic_count}，超过3个，建议重新起卦。", file=sys.stderr)
    print("", file=sys.stderr)

    result = {
        'datetime': dt.strftime('%Y年%m月%d日 %H:%M'),
        'lines': lines,
    }
    print(json.dumps(result, ensure_ascii=False))
