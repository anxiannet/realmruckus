# 通用AI卡牌优先级模型

生效日期：2026-07-14

## 一、文件定位

本文件只迁移当前源代码中已经存在的AI卡牌排序与区域需求逻辑。

不新增：

- 新权重；
- 情景标签；
- 动态修正；
- 新评分公式；
- 新AI策略。

## 二、当前源逻辑

当前源代码使用静态卡牌优先级，并结合等级进行二级排序。

通用表达：

```text
(level, ai_priority)
```

### 选择较高价值卡牌

```text
max(cards, key=(level, ai_priority))
```

用于当前源实现中的：

- 单位牌选择；
- 公开候选牌选择；
- 弃牌堆合法候选选择；
- 部分目标选择。

### 选择弃牌

```text
min(hand, key=(level, ai_priority))
```

即优先弃掉等级较低、同等级中优先级较低的卡牌。

## 三、区域需求公式

当前源公式：

```text
area_need_score
= same_group_controlled_count × 10
+ (max_units_per_area - current_units)
```

其中：

- `same_group_controlled_count`：当前玩家已控制的同组区域数量；
- `max_units_per_area`：每个区域驻军上限；
- `current_units`：目标区域当前驻军数量。

该公式只用于比较当前区域需求，不评价技能理论强度。

## 四、社交回应概率

当前源实现：

| AI模式 | 回应概率 |
|---|---:|
| pressure | 0.50 |
| human_like | 0.35 |

该概率只用于需要其他玩家回应的效果。

## 五、部署倾向

当前源实现中，以下局面倾向优先部署：

1. 当前没有控制区域；
2. 当前总驻军数量不高于已控制区域数量；
3. 已控制同组至少2个区域，且存在驻军少于2个的区域。

通用表达：

```text
if no_controlled_area:
    prefer_deploy
elif total_units <= controlled_area_count:
    prefer_deploy
elif near_group_win and weakly_defended_area_exists:
    prefer_deploy
```

## 六、静态优先级迁移状态

源代码中的静态优先级以具体卡名为键。

迁移到通用层时，必须先建立经过核对的：

```text
具体卡名
→ mechanic_id
```

一一映射，然后才能把原数值等价转写为：

```text
mechanic_id
ai_priority
```

在该映射逐项核对完成前，不建立新的通用优先级数据文件，也不自行分配数值。

## 七、系统边界

```text
AI卡牌优先级
≠ 技能强度评分
≠ 战斗方案评分
```

本文件只迁移源AI当前已经存在的排序逻辑。

## 八、来源追溯

当前源文件：

```text
测试代码/qdp_sim/data.py
测试代码/qdp_sim/game.py
```

源文件SHA：

```text
9f2a554bd0f5216c29d75b13ffa2dc94a42ab8d1
57f102edcd865122c67946fd2f4c35e65fc89123
```

迁移内容：

- 静态优先级的用途；
- 等级与优先级二级排序；
- 区域需求公式；
- 社交回应概率；
- 当前部署倾向。

未迁移内容：

- 具体卡名；
- 未核对的 `mechanic_id` 对应关系；
- 任何新权重或新修正。
