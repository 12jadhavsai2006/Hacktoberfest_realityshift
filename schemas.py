"""
schemas.py – RealityShift Pydantic Output Schemas
==================================================
Defines the strict structured-output contract that Gemma 4 must conform to
when analysing the counterfactual delta between two reality states.

These models are used in two places:
  1. As the `response_schema` enforced by the Gemini API (structured output).
  2. As FastAPI response models for automatic OpenAPI documentation.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ChangeType(str, Enum):
    """The nature of a change applied to a single entity."""
    REMOVED   = "removed"    # Entity that existed in A is absent in B
    ADDED     = "added"      # Entity that is new in B, absent in A
    MOVED     = "moved"      # Entity changed its spatial position
    ALTERED   = "altered"    # Entity's state, appearance or properties changed
    OCCLUDED  = "occluded"   # Entity is hidden / partially visible in B


class RelationshipStatus(str, Enum):
    """Whether a relationship between two entities was broken or formed."""
    BROKEN   = "broken"    # A connection that existed in A no longer exists in B
    FORMED   = "formed"    # A new connection in B that did not exist in A
    STRAINED = "strained"  # Still exists but weakened or degraded


class Severity(str, Enum):
    """The downstream impact severity of a consequence."""
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# ---------------------------------------------------------------------------
# Core Schema Models
# ---------------------------------------------------------------------------

class EntityChange(BaseModel):
    """
    Represents a single entity (object, person, element) that has changed
    between Reality-State A and Reality-State B.
    """

    entity_id: str = Field(
        ...,
        description=(
            "A short, unique identifier for this entity derived from its "
            "visual properties (e.g. 'red_traffic_light', 'bridge_left_support')."
        ),
    )
    entity_label: str = Field(
        ...,
        description="Human-readable name for the entity (e.g. 'Left Bridge Support Column').",
    )
    change_type: ChangeType = Field(
        ...,
        description="The primary type of change observed for this entity.",
    )
    description_in_a: Optional[str] = Field(
        default=None,
        description=(
            "Brief description of how this entity appeared in Image A. "
            "Null if the entity was not present in A."
        ),
    )
    description_in_b: Optional[str] = Field(
        default=None,
        description=(
            "Brief description of how this entity appears in Image B. "
            "Null if the entity was removed."
        ),
    )
    spatial_context: Optional[str] = Field(
        default=None,
        description=(
            "Where in the scene the entity is located "
            "(e.g. 'upper-left quadrant', 'foreground center')."
        ),
    )


class RelationshipChange(BaseModel):
    """
    Captures a directional dependency or interaction between two entities
    that was disrupted or newly formed as a result of the delta.
    """

    from_entity_id: str = Field(
        ...,
        description="The entity_id of the source / causal entity in the relationship.",
    )
    to_entity_id: str = Field(
        ...,
        description="The entity_id of the target / dependent entity in the relationship.",
    )
    relationship_type: str = Field(
        ...,
        description=(
            "The nature of the relationship "
            "(e.g. 'supports', 'occludes', 'powers', 'stabilises', 'connects')."
        ),
    )
    status: RelationshipStatus = Field(
        ...,
        description=(
            "Whether this relationship was broken, formed, or strained by the change."
        ),
    )
    explanation: str = Field(
        default="",
        description=(
            "One or two sentences explaining why this relationship changed "
            "and what the immediate physical or logical implication is."
        ),
    )


class Consequence(BaseModel):
    """
    An inferred downstream effect that results from the entity changes
    and broken/formed relationships. May be physical, social, operational, etc.
    """

    consequence_id: str = Field(
        ...,
        description=(
            "Short snake_case identifier for this consequence "
            "(e.g. 'structural_collapse_risk')."
        ),
    )
    title: str = Field(
        ...,
        description="Concise, human-readable title (e.g. 'Risk of Structural Collapse').",
    )
    description: str = Field(
        ...,
        description=(
            "Detailed causal chain explaining how the observed entity/relationship "
            "changes lead to this consequence. Think step-by-step."
        ),
    )
    affected_entity_ids: List[str] = Field(
        default_factory=list,
        description="List of entity_ids directly affected by this consequence.",
    )
    severity: Severity = Field(
        ...,
        description=(
            "Impact severity. "
            "'low' = minor inconvenience; "
            "'medium' = significant disruption; "
            "'high' = critical risk (safety, irreversible damage, etc.)."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Model's confidence (0.0–1.0) that this consequence will materialise "
            "given the observed changes. Calibrate honestly."
        ),
    )
    mitigation_suggestion: Optional[str] = Field(
        default=None,
        description=(
            "Optional: a concrete action that could prevent or reduce this consequence."
        ),
    )


# ---------------------------------------------------------------------------
# Top-Level Response Schema
# ---------------------------------------------------------------------------

class CounterfactualAnalysis(BaseModel):
    """
    The complete structured output from a single RealityShift analysis call.
    This is the root schema enforced by the Gemini API's structured-output mode.
    """

    summary: str = Field(
        ...,
        description=(
            "A concise (3–5 sentence) executive summary of what changed between "
            "the two reality states and the most critical downstream risk."
        ),
    )
    scene_context_a: str = Field(
        default="",
        description="One-sentence description of what Image A depicts as a whole.",
    )
    scene_context_b: str = Field(
        default="",
        description="One-sentence description of what Image B depicts as a whole.",
    )
    entity_changes: List[EntityChange] = Field(
        default_factory=list,
        description="All entities that were added, removed, moved, or altered.",
    )
    relationship_changes: List[RelationshipChange] = Field(
        default_factory=list,
        description=(
            "Relationships between entities that were broken or newly formed."
        ),
    )
    consequences: List[Consequence] = Field(
        default_factory=list,
        description=(
            "Inferred downstream consequences ranked by severity (highest first)."
        ),
    )
    overall_severity: Severity = Field(
        default=Severity.LOW,
        description="The single highest severity level across all consequences.",
    )
    reasoning_trace: Optional[str] = Field(
        default=None,
        description=(
            "Optional chain-of-thought trace showing how the model reasoned "
            "from observations to consequences. Useful for debugging."
        ),
    )
    causal_graph: Optional[CausalGraph] = Field(
        default=None,
        description=(
            "Interactive graph representation (D3/Vis.js nodes/edges + Mermaid diagram) "
            "mapping entities, relationship changes, and downstream consequences."
        ),
    )


# ---------------------------------------------------------------------------
# Causal Graph Schemas (for frontend visualization and Mermaid diagrams)
# ---------------------------------------------------------------------------

class GraphNodeType(str, Enum):
    ENTITY = "entity"
    CONSEQUENCE = "consequence"


class GraphNode(BaseModel):
    """A node in the causal graph, representing an entity or consequence."""
    id: str = Field(..., description="Unique node ID")
    label: str = Field(..., description="Display label for the node")
    node_type: GraphNodeType = Field(..., description="entity or consequence")
    status: str = Field(..., description="Entity change_type or consequence severity")
    color: str = Field(..., description="Hex color code for rendering")
    metadata: dict = Field(default_factory=dict, description="Arbitrary extra metadata")


class GraphEdge(BaseModel):
    """A directed edge in the causal graph representing a relationship or causal link."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str = Field(..., description="Edge label (e.g. 'supports (broken)', 'triggers')")
    status: str = Field(..., description="broken, formed, strained, or causes")
    style: str = Field(default="solid", description="solid, dashed, or dotted")
    color: str = Field(..., description="Hex stroke color code")


class CausalGraph(BaseModel):
    """
    Complete graph payload:
      - `nodes` & `edges`: for interactive D3.js / React Flow / Cytoscape rendering
      - `mermaid`: for zero-dependency Markdown / GitHub / Mermaid.js rendering
    """
    nodes: List[GraphNode] = Field(default_factory=list, description="All graph nodes")
    edges: List[GraphEdge] = Field(default_factory=list, description="All graph directed edges")
    mermaid: str = Field(..., description="Raw Mermaid.js diagram syntax")
    summary: str = Field(..., description="High-level topological summary of the graph")

