# 六爻占卜 Skill

适用于所有支持 Skill 的客户端的六爻占卜插件。自动掷硬币、完整装卦、四步解卦，给出专业断语。

## 功能

- **自动掷卦**：模拟三枚硬币法，随机生成六爻卦象
- **完整装卦**：纳甲、世应、六亲、六神、日空，一步全部算出
- **四步解卦**：找用神 → 日月生克 → 找世爻 → 找动爻，逻辑清晰
- **渐进式知识库**：核心规则内置，深度参考按需读取，不撑爆上下文
- **可移植**：独立 `.skill` 包，无外部依赖

## 触发方式

在 Claude Cowork 中说任意一句：

> "占一卦"、"帮我问问"、"六爻测 XXX"、"起一卦"、"掷卦"、  
> "测一下财运/感情/事业/考试/健康/合同/买房"

## 文件结构

```
liuyao-skill/
├── SKILL.md                  # 主技能文件（工作流 + 内联规则表）
├── scripts/
│   ├── cast.py               # 掷硬币脚本（输出 JSON）
│   └── arrange.py            # 装卦引擎（纳甲/世应/六亲/六神/日空）
└── references/               # 按需读取的深度参考
    ├── yongshen.md           # 六亲象意 + 特殊用神处理
    ├── liushen.md            # 六神详细象意 + 六神×六亲速查表
    ├── dongyao.md            # 动爻变化五种规则 + 地支进退表
    └── yingqi.md             # 应期推算：12 种方法
```

## 安装

1. 下载 [liuyao-skill.skill](https://github.com/username-dxy/liuyao-skill/releases)（或 clone 本仓库后自行打包）
2. 在支持 Claude Skill 的客户端中安装 `.skill` 文件

### 自行打包

```bash
git clone https://github.com/username-dxy/liuyao-skill.git
cd liuyao-skill
python3 -c "
import zipfile, os
with zipfile.ZipFile('../liuyao-skill.skill', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        for f in files:
            if '.git' not in root:
                p = os.path.join(root, f)
                zf.write(p, os.path.join('liuyao-skill', p[2:]))
"
```

## 解卦逻辑

```
占问 → 掷六爻 → 装卦（盘面）
  ↓
找用神（按占问类型取对应六亲）
  ↓
日月对用神生克（最高优先级）
  ↓         └─ 日月双克 → 直接断凶，止步
找世爻（占者自身与用神的关系）
  ↓
找动爻（变量，定吉凶强弱）
  ↓
断语：总结论 + 分析链 + 注意事项
```

## 装卦算法说明

`arrange.py` 使用八宫位移算法自动识别卦宫，无需手查表：

- **八宫**：乾兑离震巽坎艮坤，每宫 8 卦（纯卦 + 一世至五世 + 游魂 + 归魂）
- **纳甲**：八宫各爻固定地支，对应五行
- **六亲**：宫位五行与各爻五行的生克同关系
- **六神**：青龙朱雀勾陈螣蛇白虎玄武，从初爻起，起始位由日干决定
- **日空**：根据干支纪日旬数计算空亡两支

## 适用占问类型

| 占问 | 用神 |
|------|------|
| 财运、求财、投资 | 妻财爻 |
| 事业、求职、升迁 | 官鬼爻 |
| 感情（女测男）| 官鬼爻 |
| 感情（男测女）| 妻财爻 |
| 考试、合同、房产 | 父母爻 |
| 健康、出行、子女 | 子孙爻 |

