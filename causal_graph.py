"""
causal_graph.py – Causal Graph Generator for RealityShift
=========================================================
Transforms a CounterfactualAnalysis reasoning payload into:
  1. D3 / React Flow / Vis.js compatible nodes and edges (JSON).
  2. Ready-to-render Mermaid.js markdown syntax.
  3. Graphviz DOT format string.
"""

from __future__ import annotations

import re
from typing import List, Set
from schemas import (
    CounterfactualAnalysis,
    CausalGraph,
    GraphNode,
    GraphEdge,
    GraphNodeType,
)

ENTITY_COLORS = {
    "added": "#22c55e",       # Green
    "removed": "#ef4444",     # Red
    "altered": "#3b82f6",     # Blue
    "moved": "#f59e0b",       # Amber
    "occluded": "#8b5cf6",    # Purple
    "inferred": "#64748b",    # Slate
}

CONSEQUENCE_COLORS = {
    "high": "#dc2626",        # Red
    "medium": "#f97316",      # Orange
    "low": "#0ea5e9",         # Sky blue
}


def _clean_mermaid_id(raw_id: str) -> str:
    """Sanitize node ID for valid Mermaid syntax."""
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", raw_id.strip())
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    return cleaned


def _clean_mermaid_label(raw_label: str) -> str:
    """Sanitize label string for safe Mermaid quotation."""
    return raw_label.replace('"', "'").replace("\n", " ").strip()


def generate_causal_graph(analysis: CounterfactualAnalysis) -> CausalGraph:
    """
    Constructs an interactive and visual causal graph from a CounterfactualAnalysis model.

    Args:
        analysis: Validated CounterfactualAnalysis instance.

    Returns:
        A fully-populated CausalGraph instance with nodes, edges, and Mermaid syntax.
    """
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    seen_node_ids: Set[str] = set()

    # 1. Process explicit Entity Changes
    for entity in analysis.entity_changes:
        status_str = (
            entity.change_type.value
            if hasattr(entity.change_type, "value")
            else str(entity.change_type)
        )
        color = ENTITY_COLORS.get(status_str.lower(), "#64748b")
        node = GraphNode(
            id=entity.entity_id,
            label=entity.entity_label or entity.entity_id.replace("_", " ").title(),
            node_type=GraphNodeType.ENTITY,
            status=status_str,
            color=color,
            metadata={
                "description_in_a": entity.description_in_a,
                "description_in_b": entity.description_in_b,
                "spatial_context": entity.spatial_context,
            },
        )
        nodes.append(node)
        seen_node_ids.add(entity.entity_id)

    # 2. Process Consequences
    for c in analysis.consequences:
        sev_str = (
            c.severity.value
            if hasattr(c.severity, "value")
            else str(c.severity)
        )
        color = CONSEQUENCE_COLORS.get(sev_str.lower(), "#0ea5e9")
        node = GraphNode(
            id=c.consequence_id,
            label=c.title or c.consequence_id.replace("_", " ").title(),
            node_type=GraphNodeType.CONSEQUENCE,
            status=sev_str,
            color=color,
            metadata={
                "description": c.description,
                "confidence": c.confidence,
                "mitigation_suggestion": c.mitigation_suggestion,
            },
        )
        nodes.append(node)
        seen_node_ids.add(c.consequence_id)

    # 3. Process Relationship Changes (Entity <-> Entity)
    for rel in analysis.relationship_changes:
        status_str = (
            rel.status.value
            if hasattr(rel.status, "value")
            else str(rel.status)
        )

        if status_str.lower() == "broken":
            edge_color = "#ef4444"
            edge_style = "dashed"
        elif status_str.lower() == "formed":
            edge_color = "#22c55e"
            edge_style = "solid"
        else:  # strained
            edge_color = "#f59e0b"
            edge_style = "dotted"

        # Ensure source & target entities exist in node list
        for e_id in (rel.from_entity_id, rel.to_entity_id):
            if e_id not in seen_node_ids:
                nodes.append(
                    GraphNode(
                        id=e_id,
                        label=e_id.replace("_", " ").title(),
                        node_type=GraphNodeType.ENTITY,
                        status="inferred",
                        color=ENTITY_COLORS["inferred"],
                        metadata={"inferred": True},
                    )
                )
                seen_node_ids.add(e_id)

        edges.append(
            GraphEdge(
                source=rel.from_entity_id,
                target=rel.to_entity_id,
                label=f"{rel.relationship_type} ({status_str})",
                status=status_str,
                style=edge_style,
                color=edge_color,
            )
        )

    # 4. Process Consequence Triggers (Entity -> Consequence)
    for c in analysis.consequences:
        for affected_id in c.affected_entity_ids:
            if affected_id not in seen_node_ids:
                nodes.append(
                    GraphNode(
                        id=affected_id,
                        label=affected_id.replace("_", " ").title(),
                        node_type=GraphNodeType.ENTITY,
                        status="inferred",
                        color=ENTITY_COLORS["inferred"],
                        metadata={"inferred": True},
                    )
                )
                seen_node_ids.add(affected_id)

            edges.append(
                GraphEdge(
                    source=affected_id,
                    target=c.consequence_id,
                    label="triggers",
                    status="causes",
                    style="solid",
                    color="#6366f1",  # Indigo
                )
            )

    # 5. Generate Mermaid syntax (100% compliant with Mermaid 10.x)
    mermaid_lines = [
        "graph TD",
        '    subgraph Entities ["Entities & Observed Changes"]',
    ]

    for n in nodes:
        if n.node_type == GraphNodeType.ENTITY:
            m_id = _clean_mermaid_id(n.id)
            label = _clean_mermaid_label(n.label)
            mermaid_lines.append(f'        {m_id}["{label} ({n.status})"]')

    mermaid_lines.append("    end")
    mermaid_lines.append("")
    mermaid_lines.append('    subgraph Consequences ["Inferred Downstream Consequences"]')

    for n in nodes:
        if n.node_type == GraphNodeType.CONSEQUENCE:
            m_id = _clean_mermaid_id(n.id)
            label = _clean_mermaid_label(n.label)
            conf = n.metadata.get("confidence")
            conf_str = f" [Conf: {int(conf * 100)}%]" if isinstance(conf, (int, float)) else ""
            mermaid_lines.append(f'        {m_id}["{label}{conf_str}"]')

    mermaid_lines.append("    end")
    mermaid_lines.append("")
    mermaid_lines.append("    %% Causal Connections & Relationships")

    for e in edges:
        s_id = _clean_mermaid_id(e.source)
        t_id = _clean_mermaid_id(e.target)
        label = _clean_mermaid_label(e.label).replace("|", "/")

        if e.status.lower() == "broken":
            mermaid_lines.append(f"    {s_id} -.->|{label}| {t_id}")
        elif e.status.lower() == "causes":
            mermaid_lines.append(f"    {s_id} ==>|{label}| {t_id}")
        else:  # formed, strained
            mermaid_lines.append(f"    {s_id} -->|{label}| {t_id}")

    mermaid_lines.append("")
    mermaid_lines.append("    %% Universal Node Styling")
    for n in nodes:
        m_id = _clean_mermaid_id(n.id)
        text_color = "#ffffff" if n.node_type == GraphNodeType.CONSEQUENCE or n.status in ["removed", "occluded", "altered"] else "#0f172a"
        mermaid_lines.append(f"    style {m_id} fill:{n.color},stroke:#cbd5e1,stroke-width:1.5px,color:{text_color}")

    mermaid_str = "\n".join(mermaid_lines)

    # 6. Topological Summary
    entity_count = sum(1 for n in nodes if n.node_type == GraphNodeType.ENTITY)
    consequence_count = sum(1 for n in nodes if n.node_type == GraphNodeType.CONSEQUENCE)
    broken_count = sum(1 for e in edges if e.status.lower() == "broken")
    formed_count = sum(1 for e in edges if e.status.lower() == "formed")

    summary_str = (
        f"Causal graph topology: {entity_count} entities, {consequence_count} consequences, "
        f"{broken_count} broken relationship(s), and {formed_count} formed relationship(s)."
    )

    return CausalGraph(
        nodes=nodes,
        edges=edges,
        mermaid=mermaid_str,
        summary=summary_str,
    )
