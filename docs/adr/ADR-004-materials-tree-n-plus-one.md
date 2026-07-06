# ADR-004: `/api/materials/tree` N+1 查询优化

## Status
Accepted

## Context
物料的层级树（产品→模块→零件）是 BOM 管理页面的核心数据展示。原实现在 `material_tree` 端点中使用嵌套循环逐条查询数据库：

```
products = db.query(产品).all()                          # 1 次
for product in products:
    proj_bom = db.query(BOM头).first()                   # +N 次
    module_lines = db.query(BOM行).all()                  # +N 次
    for module in module_lines:
        mod = db.query(物料).first()                      # +N×M 次
        mod_bom = db.query(BOM头).first()                 # +N×M 次
        part_lines = db.query(BOM行).all()                # +N×M 次
        for part in part_lines:
            part = db.query(物料).first()                 # +N×M×K 次
```

典型数据下（6 个产品 × 5 个模块 × 15 个零件），总查询次数约 **300 次**，其中绝大部分是重复查询。

## Decision
改用"批量加载 + 内存组装"策略：

1. `SELECT * FROM material_master WHERE is_active=1` — 1 次查询，加载所有物料
2. `SELECT * FROM bom_header ORDER BY id DESC` — 1 次查询，加载所有 BOM 头
3. `SELECT * FROM bom_line ORDER BY sort_order` — 1 次查询，加载所有 BOM 行
4. Python 内存中组装树结构——用 `dict` 索引代替逐条查询

## Consequences
**更容易：**
- 接口响应时间从 O(N×M×K) 降为 O(1) 数据库往返 + O(数据量) 内存操作
- 查询次数从约 300 次降到 4 次
- 数据库连接池压力显著降低

**更困难：**
- 内存中需缓存全部启动物料和 BOM 数据（数据量较小，百级规模下约数十 KB）
- 组装逻辑比原嵌套循环稍复杂（但代码行数相近）
