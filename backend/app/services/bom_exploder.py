"""BOM 展开器 — 层级BOM树形展开与验证"""
from typing import List, Dict, Set, Optional
from collections import defaultdict


class BomExploder:
    """层级BOM树形展开工具"""

    def __init__(self, bom_lines: List[dict]):
        """
        Args:
            bom_lines: [{parent_code, child_code, quantity_per, level, scrap_rate, ...}, ...]
        """
        self.lines = bom_lines
        self._parent_to_children: Dict[str, List[dict]] = defaultdict(list)
        self._child_to_parents: Dict[str, List[str]] = defaultdict(list)

        for line in bom_lines:
            p = line.get("parent_code", "")
            c = line.get("child_code", "")
            if p and c:
                self._parent_to_children[p].append(line)
                self._child_to_parents[c].append(p)

    def get_children(self, parent_code: str) -> List[dict]:
        """获取某物料的所有子物料"""
        return self._parent_to_children.get(parent_code, [])

    def get_parents(self, child_code: str) -> List[str]:
        """获取某物料的所有父物料(用途反查)"""
        return self._child_to_parents.get(child_code, [])

    def get_top_level_items(self) -> List[str]:
        """获取所有顶层物料(没有父物料的)"""
        all_codes = set()
        for line in self.lines:
            p = line.get("parent_code", "")
            c = line.get("child_code", "")
            if p:
                all_codes.add(p)
            if c:
                all_codes.add(c)
        return [c for c in all_codes if c not in self._child_to_parents]

    def explode_to_tree(self, root_code: str, max_depth: int = 10) -> dict:
        """
        展开为嵌套树形结构

        Returns:
            {
                "code": "FG-001",
                "name": "成品A",
                "children": [
                    {"code": "SA-001", "name": "部件A1", "qty_per": 1, "children": [...]},
                    ...
                ]
            }
        """
        def _build(code, depth):
            if depth > max_depth:
                return None
            children = []
            for line in self._parent_to_children.get(code, []):
                child = {
                    "code": line.get("child_code", ""),
                    "name": line.get("child_name", ""),
                    "qty_per": line.get("quantity_per", 1),
                    "position": line.get("position", ""),
                    "is_substitute": line.get("is_substitute", False),
                    "scrap_rate": line.get("scrap_rate", 0),
                    "children": [],
                }
                sub = _build(line.get("child_code", ""), depth + 1)
                if sub:
                    child["children"] = sub.get("children", [])
                children.append(child)
            return {"code": code, "children": children}

        return _build(root_code, 0)

    def detect_cycle(self) -> Optional[List[str]]:
        """
        检测循环引用 (A→B→C→A)
        使用DFS三色标记法：0=未访问, 1=访问中, 2=已完成
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = defaultdict(int)
        path = []

        def dfs(code):
            color[code] = GRAY
            path.append(code)
            for line in self._parent_to_children.get(code, []):
                child = line.get("child_code", "")
                if color[child] == GRAY:
                    cycle_start = path.index(child)
                    return path[cycle_start:] + [child]
                if color[child] == WHITE:
                    result = dfs(child)
                    if result:
                        return result
            path.pop()
            color[code] = BLACK
            return None

        all_codes = set()
        for code in self.get_top_level_items():
            all_codes.add(code)
            result = dfs(code)
            if result:
                return result

        return None

    def get_single_level_where_used(self, item_code: str) -> List[str]:
        """单层用途反查：哪些物料直接使用了该物料"""
        return self._child_to_parents.get(item_code, [])

    def get_indented_bom(self, root_code: str, level: int = 0) -> List[dict]:
        """
        缩进式BOM(类似于SAP的CS12)
        返回值按缩进层级排列，适合表格显示
        """
        result = []

        def _traverse(code, level):
            for line in self._parent_to_children.get(code, []):
                child_code = line.get("child_code", "")
                result.append({
                    "level": level,
                    "parent_code": code,
                    "child_code": child_code,
                    "child_name": line.get("child_name", ""),
                    "quantity_per": line.get("quantity_per", 1),
                    "position": line.get("position", ""),
                })
                _traverse(child_code, level + 1)

        # 先加根节点
        result.append({
            "level": 0,
            "parent_code": "",
            "child_code": root_code,
            "child_name": "",
            "quantity_per": 1,
            "position": "",
        })
        _traverse(root_code, 1)
        return result
