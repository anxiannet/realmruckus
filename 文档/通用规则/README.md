# 通用规则层

规则版本：V1.3  
更新时间：2026-07-14

## 文件定位

本目录只保存从当前源项目等价迁移出的通用机制、规则、卡表、评分方法、测试结果和生产流程。

迁移阶段禁止：

- 设计新规则；
- 分配新权重；
- 增加新参数；
- 建立源项目不存在的校准体系；
- 开发或改进新引擎；
- 迁移具体卡名、角色、世界观、品牌卡号和具体资产。

## 当前数据

机制卡表：

```text
data/core_set.json
data/expansion_1.json
```

已核对的AI静态优先级：

```text
data/ai_priorities.json
```

当前测试结果的等价结构化副本：

```text
data/baselines/current_formal.json
data/baselines/current_dual_modes.json
```

## 文件列表

```text
通用内容迁移范围.md
通用内容迁移清单.md
数据唯一来源规范.md
当前版本基线.md
核心机制.md
规则状态机.md
标准组件模型.md
通用标准版卡表.md
通用扩展包卡表.md
双人模式参数.md
数学与平衡模型.md
技能强度评分系统.md
AI卡牌优先级模型.md
战斗方案评分模型.md
测试与验证规范.md
当前测试基线.md
通用生产与审核流程.md
迁移来源记录.md
```

## 读取顺序

1. `通用内容迁移范围.md`
2. `通用内容迁移清单.md`
3. `数据唯一来源规范.md`
4. `当前版本基线.md`
5. `核心机制.md`
6. `规则状态机.md`
7. `标准组件模型.md`
8. `data/core_set.json`
9. `data/expansion_1.json`
10. `data/ai_priorities.json`
11. `通用标准版卡表.md`
12. `通用扩展包卡表.md`
13. `双人模式参数.md`
14. `数学与平衡模型.md`
15. `技能强度评分系统.md`
16. `AI卡牌优先级模型.md`
17. `战斗方案评分模型.md`
18. `测试与验证规范.md`
19. `data/baselines/current_formal.json`
20. `data/baselines/current_dual_modes.json`
21. `当前测试基线.md`
22. `通用生产与审核流程.md`
23. `迁移来源记录.md`

## 维护原则

- 只做等价迁移和来源核对。
- 只保留当前最新有效内容。
- 无法直接追溯到源文件的内容不得写入正式通用层。
- 具体表达不得成为通用规则来源。
- 迁移完成后，改进和开发工作在新项目阶段另行执行。
