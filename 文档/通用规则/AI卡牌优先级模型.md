# 通用AI卡牌优先级模型

生效日期：2026-07-14

## 一、文件定位

本文件只迁移当前源代码中已经存在的AI卡牌排序与区域需求逻辑。

不新增新权重、情景标签、动态修正、新评分公式或新AI策略。

## 二、当前数据源

```text
data/ai_priorities.json
```

该文件只保存源 `card_priority()` 中已有数值，经当前卡表逐项核对后，将具体卡名等价替换为 `mechanic_id`。

## 三、当前源逻辑

当前源代码使用静态卡牌优先级，并结合等级进行二级排序：

```text
(level, ai_priority)
```

### 选择较高价值卡牌

```text
max(cards, key=(level, ai_priority))
```

用于单位牌、公开候选牌、弃牌堆合法候选和部分目标选择。

### 选择弃牌

```text
min(hand, key=(level, ai_priority))
```

即优先弃掉等级较低、同等级中优先级较低的卡牌。

## 四、区域需求公式

```text
area_need_score
= same_group_controlled_count × 10
+ (max_units_per_area - current_units)
```

- `same_group_controlled_count`：当前玩家已控制的同组区域数量；
- `max_units_per_area`：每个区域驻军上限；
- `current_units`：目标区域当前驻军数量。

## 五、社交回应概率

| AI模式 | 回应概率 |
|---|---:|
| pressure | 0.50 |
| human_like | 0.35 |

## 六、部署倾向

当前源实现中，以下局面倾向优先部署：

1. 当前没有控制区域；
2. 当前总驻军数量不高于已控制区域数量；
3. 已控制同组至少2个区域，且存在驻军少于2个的区域。

```text
if no_controlled_area:
    prefer_deploy
elif total_units <= controlled_area_count:
    prefer_deploy
elif near_group_win and weakly_defended_area_exists:
    prefer_deploy
```

## 七、静态优先级迁移

已按以下当前源逐项核对：

```text
规则/V1.3-基础卡表.md
规则/扩展包一-火云再起卡表.md
测试代码/qdp_sim/data.py
```

迁移字段：

```text
mechanic_id
ai_priority
```

未增加任何源表中不存在的标签、权重或动态修正。

## 八、系统边界

```text
AI卡牌优先级
≠ 技能强度评分
≠ 战斗方案评分
```

## 九、来源追溯

源文件与SHA：

```text
测试代码/qdp_sim/data.py
9f2a554bd0f5216c29d75b13ffa2dc94a42ab8d1

测试代码/qdp_sim/game.py
57f102edcd865122c67946fd2f4c35e65fc89123

规则/V1.3-基础卡表.md
0f394718ec91a4abfa4e5770e23e95f5fcfbd5ed

规则/扩展包一-火云再起卡表.md
330051118b4f9e38b72f640bd0826cc94ca81b30
```

迁移内容：静态优先级数值、排序用途、区域需求公式、社交回应概率和部署倾向。

排除内容：具体卡名、具体地名、具体产品输出文本和任何新增AI设计。
