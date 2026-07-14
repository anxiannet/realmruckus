# 通用模拟器

规则版本：V1.3  
更新时间：2026-07-14

## 当前状态

本目录用于建立完全由 `mechanic_id`、`effect_id` 和JSON卡表驱动的通用模拟器。

当前已经完成：

- 通用数据模型
- 基础战斗结算
- 区域回流
- 即时胜利检查
- 最终计分
- 标准版与扩展包JSON卡表
- JSON数量与结构校验
- 部署与进攻合法性判断
- 回合阶段状态机
- 效果执行注册框架
- 抽牌、弃牌、击败、返回、获得单位、区域保护等基础效果处理
- 基础单元测试和CI

当前尚未完成：

- 全部效果ID执行器
- 效果目标自动选择
- 完整回合执行器
- human_like策略
- stress_attack策略
- 批量3000局运行器
- 历史基线复现

在上述内容完成前，不得将本目录输出称为正式平衡测试结果。

## 当前代码入口

```text
engine/actions.py
engine/turns.py
engine/effects.py
```

效果执行使用：

```text
CardDefinition.effect_id
EffectContext
execute_effect()
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
