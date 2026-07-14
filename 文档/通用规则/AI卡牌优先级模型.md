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

## 二、通用数据字段

每个机制身份可提供以下AI字段：

```text
ai_base_priority
card_kind
level
effect_id
situational_tags
```

禁止以具体卡名作为权重键。

推荐标签：

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
```

## 三、基础优先级

`ai_base_priority` 是一个独立的整数排序值。

它只表达AI在普通局面下对卡牌的保留和使用倾向，不代表技能理论强度。

推荐范围：

```text
0–100
```

基础排序原则：

1. 能直接影响胜利进度的机制优先。
2. 能处理任意等级目标的机制高于低等级限制机制。
3. 形成所有权变化的机制高于单纯返回手牌。
4. 立即额外行动高于普通信息收益。
5. 取消和保护等反制机制根据当前合法目标动态修正。
6. 纯信息机制通常低于直接场面与资源机制。

## 四、手牌保留与弃牌

源模型使用二级排序：

```text
(level, ai_base_priority)
```

### 弃牌选择

```text
discard_candidate
= min(hand, key=(level, ai_base_priority))
```

即优先弃掉：

1. 等级较低的单位；
2. 同等级中AI优先级较低的卡；
3. 没有当前合法目标的效果牌。

通用化后建议增加合法性修正：

```text
discard_score
= level_weight
+ ai_base_priority
+ current_legality_bonus
+ win_relevance_bonus
+ defensive_need_bonus
```

弃牌选择最低分。

### 最佳单位选择

```text
best_unit
= max(unit_cards, key=(level, ai_base_priority))
```

用于额外部署、普通部署和牌库顶选择。

## 五、区域需求评分

源模型的区域需求公式：

```text
area_need_score
= same_group_controlled_count × 10
+ (max_units_per_area - current_units)
```

含义：

- 已控制同组区域越多，继续向该组部署的价值越高；
- 当前区域空位越多，部署空间越充足。

通用模型保留该基线，并允许后续增加：

```text
+ immediate_win_bonus
+ block_opponent_bonus
+ protection_bonus
- exposure_risk
```

当前迁移基线仍以原公式为准，新增项属于后续引擎开发范围。

## 六、目标选择

### 单位目标

当机制要求优先处理高价值单位时：

```text
target_value
= level
+ ai_base_priority / priority_scale
```

源模型常用排序：

```text
max(targets, key=(level, ai_base_priority))
```

当机制不要求最优目标时，可在合法目标中随机选择，以保留普通玩家的不完全最优行为。

### 区域目标

保护己方区域时，源模型优先：

```text
同组控制数量
→ 区域驻军总等级
```

通用排序：

```text
max(own_areas, key=(same_group_controlled_count, total_unit_level))
```

攻击或去除敌方单位时，应先过滤受保护区域和非法目标。

## 七、牌库顶与弃牌堆选择

从多个公开候选中选择一张时，源模型使用：

```text
max(candidates, key=(level, ai_base_priority))
```

从弃牌堆回收指定等级卡牌时：

```text
max(legal_candidates, key=ai_base_priority)
```

其余牌按规则放回指定位置，不因AI选择改变规则流程。

## 八、社交回应概率

源模型使用两档概率：

| AI模式 | 回应概率 |
|---|---:|
| pressure | 0.50 |
| human_like | 0.35 |

通用说明：

- 该概率只用于需要另一玩家回应的效果；
- 不表示所有效果牌使用概率；
- AI不得查看隐藏信息后再决定是否回应；
- 后续可通过实体测试校准，但迁移基线应保留。

## 九、部署前与进攻前判断

源模型在以下情况倾向先部署：

1. 当前没有控制区域；
2. 总驻军数量不高于已控制区域数量；
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

## 十、与技能强度评分的关系

`ai_base_priority` 可以参考技能强度评分，但不能直接等于技能强度评分。

原因：

- 理论强度高的卡可能当前没有合法目标；
- 取消效果在没有可响应效果时价值为零；
- 低强度部署牌可能在立即获胜区域中价值最高；
- 手牌结构和防守需求会改变保留价值。

因此：

```text
AI优先级
= 基础机制优先级
+ 当前合法性
+ 胜利相关性
+ 防守需求
+ 手牌结构
```

## 十一、迁移状态

已迁移：

- 独立优先级字段概念；
- `(level, priority)`二级排序；
- 弃最低、选最高的行为；
- 区域需求公式；
- 社交回应概率；
- 部署前判断逻辑。

尚未迁移完成：

- 每个 `mechanic_id` 的正式 `ai_base_priority` 数据；
- 情景标签的完整权重；
- 与自动目标生成器的接口；
- 新引擎中的参数校准。

上述未完成项属于后续数据迁移和引擎开发，不得用具体卡名权重表直接替代。

## 十二、来源追溯

原仓库：`anxiannet/qiangdipan`

主要源文件：

```text
测试代码/qdp_sim/data.py
测试代码/qdp_sim/game.py
```

原文件SHA：

```text
9f2a554bd0f5216c29d75b13ffa2dc94a42ab8d1
57f102edcd865122c67946fd2f4c35e65fc89123
```

抽取内容：

- 静态优先级排序用途；
- 等级与优先级二级排序；
- 区域需求评分；
- 社交回应概率；
- 部署和目标选择逻辑。

排除内容：

- 具体卡名权重表；
- 具体地名和分组名；
- 具体效果分支；
- 具体产品输出文本。
