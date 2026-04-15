from dataclasses import dataclass

from typing import List


@dataclass
class Node:
    node_id: str
    description: str = None
    type: str = None
    status: str = None
    how: list[str] = None


class NodeGraph:
    nodes: dict[str, Node] = dict()

    @classmethod
    def load_from_disk(self, vault_path: str) -> "NodeGraph": ...

    def get_node(self, node_id: str) -> Node: ...
    def get_why_tree(self, node_id: str) -> List[(Node, int, int)]: ...
    def get_how_tree(self, node_id: str) -> List[(Node, int, int)]: ...
