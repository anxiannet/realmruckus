# 通用AI卡牌优先级模型

版本：GEN-AI-PRIORITY-001  
生效日期：2026-07-14

## 一、文件定位

本文件定义AI在非战斗决策中的卡牌优先级模型，用于：

- 选择保留哪张牌；
- 选择弃掉哪张牌；
- 选择额外部署哪张单位牌；
- 从弃牌堆或牌库顶选择哪张牌；
- 选择效果目标；
- 在多个合法区域中选择部署目的地。

本模型不等同于技能理论强度评分，也不等同于战斗方案评分。

## 二、当前数据源

```text
data/ai_priorities.json
```

该文件是当前每个 `mechanic_id` 的：

- `ai_base_priority`
- `situational_tags`
- 动态局面修正

的唯一数据来源。

禁止以具体卡名作为权重键。

## 三、通用数据字段

```text
mechanic_id
ai_base_priority
situational_tags
```

当前常用标签包括：

```text
DRAW
DISCARD
RETURN
DEFEAT
TAKE_CONTROL
EXTRA_DEPLOY
IMMEDIATE_ATTACK
CANCEL
PROTECT
RECOVER
INFORMATION
AREA_RESET
WIN_PROGRESS
RESOURCE_SWING
ACTION_ECONOMY
```

## 四、基础优先级

`ai_base_priority` 是独立整数排序值，当前范围为0–100。

它表达AI在普通局面下对卡牌的保留和使用倾向，不代表技能理论强度。

基础排序原则：

1. 能直接影响胜利进度的机制优先。
2. 能处理任意等级目标的机制高于低等级限制机制。
3. 形成所有权变化的机制高于单纯返回手牌。
4. 立即额外行动高于普通信息收益。
5. 取消和保护等反制机制根据当前合法目标动态修正。
6. 纯信息机制通常低于直接场面与资源机制。

## 五、手牌保留与弃牌

基础二级排序：

```text
(level, ai_base_priority)
```

### 弃牌选择

```text
discard_candidate
= min(hand, key=(level, ai_base_priority))
```

动态弃牌评分：

```text
discard_score
= level_weight
+ ai_base_priority
+ current_legality_bonus
+ win_relevance_bonus
+ defensive_need_bonus
```

弃牌时选择最低分。

### 最佳单位选择

```text
best_unit
= max(unit_cards, key=(level, ai_base_priority))
```

用于额外部署、普通部署和牌库顶选择。

## 六、当前动态修正

当前数据源定义：

```text
无合法目标：-1000
可立即获胜：+200
可阻止对手立即获胜：+100
当前防守不足且该牌可补强：+30
手牌超限弃牌压力：-10
组合条件满足：+20
组合条件未满足：-20
```

动态修正只改变当前局面的AI决策，不改变卡牌的理论技能强度评分。

## 七、区域需求评分

当前公式：

```text
area_need_score
= same_group_controlled_count × 10
+ (max_units_per_area - current_units)
```

含义：

- 已控制同组区域越多，继续向该组部署的价值越高；
- 当前区域空位越多，部署空间越充足。

## 八、目标选择

### 单位目标

优先处理高价值单位时：

```text
target_value
= level
+ ai_base_priority / priority_scale
```

常用排序：

```text
max(targets, key=(level, ai_base_priority))
```

机制要求随机目标时，必须在合法目标中随机选择，不得使用隐藏信息优化。

### 区域目标

保护己方区域时：

```text
max(own_areas, key=(same_group_controlled_count, total_unit_level))
```

攻击或移除敌方单位时，必须先过滤受保护区域和非法目标。

## 九、牌库顶与弃牌堆选择

公开候选选择：

```text
max(candidates, key=(level, ai_base_priority))
```

指定等级弃牌堆回收：

```text
max(legal_candidates, key=ai_base_priority)
```

## 十、社交回应概率

| AI模式 | 回应概率 |
|---|---:|
| pressure | 0.50 |
| human_like | 0.35 |

- 只用于需要另一玩家回应的效果；
- AI不得查看隐藏信息后再决定是否回应。

## 十一、部署前与进攻前判断

以下情况倾向先部署：

1. 当前没有控制区域；
2. 总驻军数量不高于已控制区域数量；
3. 已控制同组至少2个区域，且存在驻军少于2个的区域。

```text
if no_controlled_area:
    prefer_deploy
elif total_units <= controlled_area_count:
    prefer_deploy
elif near_group_win and weakly_defended_area_exists:
    prefer_deploy
```

## 十二、与技能强度评分的关系

```text
AI优先级
= 基础机制优先级
+ 当前合法性
+ 胜利相关性
+ 防守需求
+ 手牌结构
```

`ai_base_priority` 可以参考技能强度，但不能直接等于技能强度评分。

## 十三、当前完成状态

已完成：

- 全部标准版与扩展包 `mechanic_id` 的基础优先级；
- 全部机制的情景标签；
- 当前动态修正表；
- 区域需求、手牌排序、目标选择和社交回应规则。

尚需后续验证：

- 使用当前正式测试结果校准优先级；
- 与后续完整通用引擎的接口验证。

## 十四、来源追溯

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

抽取内容：

- 当前静态优先级顺序；
- 等级与优先级二级排序；
- 区域需求评分；
- 社交回应概率；
- 部署和目标选择逻辑。

排除内容：

- 具体卡名；
- 具体地名和分组名；
- 具体产品输出文本；
- 被当前版本替代的参数。
