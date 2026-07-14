# Realm Ruckus / Universal Territory Card Engine

This repository is now the primary repository for the shared game mechanics, rules, mathematical models, simulation code and validation baselines used by multiple product expressions.

Current expressions:

```text
《夕妖：抢地盘》
Realm Ruckus
```

## Repository structure

The repository root is the website and code root.

```text
/
├── README.md
├── index.html
├── assets/
├── engine/
├── simulation/
├── tests/
└── 文档/
    ├── README.md
    ├── 当前项目进度.md
    ├── 通用规则/
    │   ├── README.md
    │   ├── 核心机制.md
    │   ├── 规则状态机.md
    │   ├── 标准组件模型.md
    │   ├── 通用标准版卡表.md
    │   ├── 通用扩展包卡表.md
    │   ├── 双人模式参数.md
    │   ├── 数学与平衡模型.md
    │   ├── 测试与验证规范.md
    │   ├── 历史测试基线.md
    │   └── 迁移来源记录.md
    └── Realm Ruckus专属文档
```

## Authority

The universal rules layer in `文档/通用规则/` is the authoritative source for:

- core mechanics;
- standard and expansion mechanism tables;
- turn and combat flow;
- mathematical models;
- simulation and regression standards;
- historical test baselines.

Product expressions may replace names, language, artwork, UI, packaging and card-code prefixes. They must not maintain parallel copies of the shared mechanics.

Legacy expression repository:

```text
https://github.com/anxiannet/qiangdipan
```

That repository remains the production repository for the 《夕妖：抢地盘》 expression, but no longer owns the universal mechanics layer.
