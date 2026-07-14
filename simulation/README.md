# 通用模拟器

规则版本：V1.3  
更新时间：2026-07-14

## 当前状态

本目录用于建立完全由 `mechanic_id`、`effect_id` 和JSON卡表驱动的通用模拟器。

当前已经完成：

- 通用卡牌实例模型，支持单位牌与效果牌
- 基础战斗结算
- 战斗单位顺序与防守目标方案枚举
- 区域回流
- 即时胜利检查
- 最终计分
- 标准版与扩展包JSON卡表
- JSON数量与结构校验
- 部署与进攻合法性判断
- 回合阶段状态机
- 完整回合执行器骨架
- 抽牌、行动、效果、回流、胜利、手牌上限和下一玩家编排
- 效果执行注册框架
- 所有独立效果处理
- 替代击败、额外部署和立即进攻编排
- 取消效果基础响应窗口
- 区域保护持续到所属玩家下回合开始
- 公共牌库耗尽后的完整一轮无进展结算
- 基础单元测试和CI文件

当前尚未完成：

- 效果目标自动选择
- 多层或多响应者响应链
- 更完整的费用与非法目标预检查
- human_like策略
- stress_attack策略
- 批量运行入口
- 2、3、4人自动对局
- 批量3000局运行器
- 历史基线复现

当前 `GameEngine` 已可以执行由外部明确提供动作与效果目标的规则流程，但还不能自行选择动作完成自动对局。

在AI策略、批量运行器和基线复现完成前，不得将本目录输出称为正式平衡测试结果。

## 当前代码入口

```text
engine/models.py
engine/factory.py
engine/combat.py
engine/actions.py
engine/turns.py
engine/effects.py
engine/game.py
```

效果执行使用：

```text
CardDefinition.effect_id
EffectContext
execute_effect()
GameEngine.resolve_card_effect()
```

不得使用具体卡名分发效果。

## 目标批量入口

```text
python -m simulation.run \
  --deck core \
  --players 2 \
  --area-groups 3 \
  --center-size 2 \
  --ai human_like \
  --games 3000 \
  --seed 20260714 \
  --json
```

## 数据来源

```text
data/core_set.json
data/expansion_1.json
```
