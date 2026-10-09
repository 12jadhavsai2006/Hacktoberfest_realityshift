"""
main.py – RealityShift FastAPI Application
==========================================
Multimodal counterfactual reasoning engine powered by Gemma 4 via the
official `google-genai` SDK.

Key design decisions:
  - Uses `google.genai` (new SDK) — NOT the legacy `google.generativeai`.
  - Structured output is enforced via `response_schema` so the API guarantees
    the response matches our `CounterfactualAnalysis` Pydantic model.
  - Images are forwarded as inline base64 blobs so the endpoint works without
    any external file storage.
  - CORS is opened wide for local hackathon development; tighten for prod.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from typing import Optional

# Load environment variables from .env file if present (with standard library fallback)
def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip("'\""))

_load_env_file()

from pydantic import ValidationError

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types as genai_types

from schemas import CounterfactualAnalysis, CausalGraph
from causal_graph import generate_causal_graph
from graph_ui import GRAPH_VIEWER_HTML

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("realityshift")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GEMMA_MODEL = "gemma-4-26b-a4b-it"          # Multimodal Gemma 4 instruction-tuned model
MAX_IMAGE_BYTES = 10 * 1024 * 1024      # 10 MB per image hard limit
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

SCHEMA_JSON_STR = json.dumps(CounterfactualAnalysis.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""
You are RealityShift — a senior multimodal counterfactual reasoning engine.

Your task is to perform a rigorous, structured analysis of the *delta* between
two photographs of reality: Image A (the "before" state) and Image B (the
"after" / counterfactual state).

## Analytical Framework

Follow this chain-of-thought methodology STRICTLY:

### Step 1 — Scene Grounding
Briefly describe the overall scene in Image A and Image B independently.
Identify the domain: infrastructure, urban environment, nature, indoor space,
mechanical system, etc.

### Step 2 — Entity Inventory
List every distinct, semantically meaningful entity (object, person, structure,
element) visible in either image. Assign each a unique `entity_id` in
snake_case.

### Step 3 — Change Detection
For each entity, determine its state in A versus B:
  - REMOVED: present in A, absent in B
  - ADDED: absent in A, present in B
  - MOVED: same entity, different spatial position
  - ALTERED: same entity, changed state/appearance/properties
  - OCCLUDED: hidden by another element in B

### Step 4 — Relationship Mapping
Identify functional, structural, or causal relationships between entities
that were BROKEN, FORMED, or STRAINED by the observed changes.

Think about:
  - Physical support / load-bearing relationships
  - Power / data / fluid flow connections
  - Visibility / line-of-sight occlusions
  - Human-system interactions
  - Temporal / sequential dependencies

### Step 5 — Consequence Inference
For each broken or formed relationship, reason through the downstream
consequences using causal chains. Be specific. Assign:
  - `severity`: low / medium / high
  - `confidence`: 0.0–1.0 (how certain are you this consequence will occur?)

Rank consequences from highest to lowest severity.

### Step 6 — Overall Severity
Determine the single `overall_severity` that best characterises the aggregate
risk of all consequences.

## Required JSON Output Schema
Your response must be a single, valid JSON object conforming strictly to this schema:
{SCHEMA_JSON_STR}

## Rules
- Return ONLY the valid JSON object conforming to the schema.
- Be precise, concise, and direct. Do NOT repeat phrases or loop endlessly.
- Keep `summary` to 2–3 concise sentences.
- Keep `reasoning_trace` under 150 words.
- Express uncertainty honestly through `confidence` scores < 0.5.
- If the user has provided a change description, treat it as ground-truth
  context to inform (but not replace) your visual analysis.
""".strip()


# ---------------------------------------------------------------------------
# Lifespan: initialise the GenAI client once at startup
# ---------------------------------------------------------------------------

genai_client: genai.Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise expensive resources at startup, tear down at shutdown."""
    global genai_client

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Export it before starting the server."
        )

    genai_client = genai.Client(api_key=api_key)
    logger.info("Google GenAI client initialised (model=%s)", GEMMA_MODEL)

    yield  # Application is running

    genai_client = None
    logger.info("Google GenAI client released.")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RealityShift API",
    description=(
        "Multimodal counterfactual reasoning engine. "
        "Pass two images (before / after) and receive a structured analysis "
        "of what changed and what the downstream consequences are."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — open for hackathon; restrict `allow_origins` in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper Utilities
# ---------------------------------------------------------------------------

async def _read_and_validate_image(
    upload: UploadFile,
    field_name: str,
) -> tuple[bytes, str]:
    """
    Read uploaded image bytes, enforce size + MIME type constraints.

    Returns:
        (raw_bytes, mime_type)
    """
    mime_type = upload.content_type or "application/octet-stream"

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"'{field_name}' has unsupported MIME type '{mime_type}'. "
                f"Accepted types: {', '.join(sorted(ALLOWED_MIME_TYPES))}."
            ),
        )

    raw_bytes = await upload.read()

    if len(raw_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"'{field_name}' exceeds the {MAX_IMAGE_BYTES // (1024*1024)} MB limit "
                f"({len(raw_bytes) // 1024} KB received)."
            ),
        )

    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{field_name}' is empty.",
        )

    return raw_bytes, mime_type


def _build_user_message(
    bytes_a: bytes,
    mime_a: str,
    bytes_b: bytes,
    mime_b: str,
    user_change_description: Optional[str],
) -> list[genai_types.Part]:
    """
    Construct the multimodal content list for the Gemini API call.
    Images are passed as inline base64 blobs.
    """
    parts: list[genai_types.Part] = []

    # --- Image A ---
    parts.append(
        genai_types.Part(text="**[IMAGE A — Reality State Before / Baseline]**")
    )
    parts.append(
        genai_types.Part(
            inline_data=genai_types.Blob(
                mime_type=mime_a,
                data=base64.b64encode(bytes_a).decode("utf-8"),
            )
        )
    )

    # --- Image B ---
    parts.append(
        genai_types.Part(text="**[IMAGE B — Reality State After / Counterfactual]**")
    )
    parts.append(
        genai_types.Part(
            inline_data=genai_types.Blob(
                mime_type=mime_b,
                data=base64.b64encode(bytes_b).decode("utf-8"),
            )
        )
    )

    # --- Optional user-provided context ---
    if user_change_description and user_change_description.strip():
        parts.append(
            genai_types.Part(
                text=(
                    f"**[USER-PROVIDED CHANGE DESCRIPTION]**\n"
                    f"{user_change_description.strip()}\n\n"
                    "Use this as additional ground-truth context alongside your visual analysis."
                )
            )
        )

    parts.append(
        genai_types.Part(
            text=(
                "Perform your full counterfactual analysis of Image A → Image B "
                "following the analytical framework in the system prompt. "
                "Respond ONLY with the structured JSON output."
            )
        )
    )

    return parts


# ---------------------------------------------------------------------------
# JSON Truncation Repair
# ---------------------------------------------------------------------------

def _repair_truncated_json(raw: str) -> str:
    """
    Best-effort repair of a JSON string that was cut off mid-stream by the
    model hitting its token limit (produces "EOF while parsing a string").

    Strategy:
      1. Walk every character tracking open strings / brackets / braces.
      2. If we end inside a string, close it with '"'.
      3. Close every open array / object in reverse order.

    This lets Pydantic parse the result and fill optional fields (like
    ``reasoning_trace``) with their default values instead of crashing.
    """
    try:
        json.loads(raw)      # Already valid — nothing to do
        return raw
    except json.JSONDecodeError as exc:
        if "EOF" not in str(exc) and "Unterminated" not in str(exc):
            raise            # Structural error we can't repair, re-raise

    stack: list[str] = []   # Tracks '{' and '['
    in_string = False
    escaped = False

    for ch in raw:
        if escaped:
            escaped = False
            continue
        if ch == "\\" and in_string:
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch in ("{", "["):
                stack.append(ch)
            elif ch == "}" and stack and stack[-1] == "{":
                stack.pop()
            elif ch == "]" and stack and stack[-1] == "[":
                stack.pop()

    repaired = raw
    if in_string:
        repaired += '"'                     # Close the dangling string
    for opener in reversed(stack):          # Close open objects / arrays
        repaired += "}" if opener == "{" else "]"

    logger.warning(
        "Repaired truncated JSON: closed %d open structure(s), string_was_open=%s",
        len(stack), in_string,
    )
    return repaired


def _clean_and_extract_json(raw: str) -> str:
    """
    Extract and clean a JSON object string from raw model output.
    Handles:
      1. Pure JSON
      2. Markdown code fences ```json ... ```
      3. Trailing backticks, extra braces, or trailing text after the JSON object
      4. Leading text before the JSON object
      5. Unterminated strings or brackets via repair
    """
    if not raw:
        return ""
    text = raw.strip()

    # If wrapped in markdown code fence, strip it
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()

    # Find the opening brace '{'
    start = text.find("{")
    if start == -1:
        return text

    # Try standard json parse from start to cleanly extract the object
    # ignoring trailing markdown fences or characters
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return json.dumps(obj)
    except Exception:
        pass

    # Try finding the matching last closing brace '}'
    end = text.rfind("}")
    if end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    # Fallback to truncated JSON repair
    repaired = _repair_truncated_json(text[start:])
    try:
        json.loads(repaired)
        return repaired
    except Exception:
        pass

    return text[start:]


# ---------------------------------------------------------------------------
# Standalone Reasoning Helper (usable outside the FastAPI lifecycle)
# ---------------------------------------------------------------------------

def get_realityshift_analysis(prompt: str) -> CounterfactualAnalysis:
    """
    Text-only wrapper around the Gemma 4 structured-output call.

    Intended for:
      - CLI / ``__main__`` smoke-tests (no images needed)
      - Unit tests that mock ``genai.Client``
      - Future batch-processing pipelines

    Args:
        prompt: Free-text scenario description to reason about.

    Returns:
        A fully-validated ``CounterfactualAnalysis`` Pydantic object.

    Raises:
        RuntimeError: If ``GOOGLE_API_KEY`` is not set.
        ValidationError: If the model output cannot be parsed after all retries.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Set it before running the test harness."
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=GEMMA_MODEL,
        contents=[
            genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=prompt)],
            )
        ],
        config=genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
            top_p=0.9,
            max_output_tokens=4096,
            # Disable Automatic Function Calling — we want plain JSON output,
            # not tool-call round-trips.
            automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        ),
    )

    # --- Robust extraction + retry parse (mirrors the endpoint's logic) ---
    MAX_PARSE_RETRIES = 3
    last_exc: ValidationError | None = None

    for attempt in range(1, MAX_PARSE_RETRIES + 1):
        try:
            # Path A: SDK already returned a parsed Pydantic object
            if hasattr(response, "parsed") and response.parsed is not None:
                analysis = response.parsed
                analysis.causal_graph = generate_causal_graph(analysis)
                return analysis

            # Path B: Extract and clean JSON, handling fences and trailing characters
            raw_text: str = response.text or ""
            cleaned = _clean_and_extract_json(raw_text)

            # Path C (attempt 2+): repair JSON truncated by token limit
            if attempt > 1:
                cleaned = _repair_truncated_json(cleaned)

            logger.debug(
                "[standalone] Parse attempt %d/%d | raw=%d chars | cleaned=%d chars",
                attempt, MAX_PARSE_RETRIES, len(raw_text), len(cleaned),
            )

            analysis = CounterfactualAnalysis.model_validate_json(cleaned)
            analysis.causal_graph = generate_causal_graph(analysis)
            return analysis

        except ValidationError as exc:
            last_exc = exc
            logger.warning(
                "[standalone] ValidationError attempt %d/%d: %s",
                attempt, MAX_PARSE_RETRIES, exc,
            )

    raise last_exc  # type: ignore[misc]  — exhausted all retries


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Meta"])
async def health_check() -> dict:
    """Liveness probe — confirms the service is up."""
    return {"status": "ok", "model": GEMMA_MODEL}


@app.post(
    "/api/v1/analyze-shift",
    response_model=CounterfactualAnalysis,
    status_code=status.HTTP_200_OK,
    summary="Analyse counterfactual delta between two images",
    description=(
        "Upload two images representing two states of reality. "
        "Gemma 4 will identify what changed, which relationships were disrupted, "
        "and reason about the downstream consequences in structured JSON."
    ),
    tags=["Analysis"],
)
async def analyze_shift(
    file_a: UploadFile = File(
        ...,
        description="Image A — the baseline / before state of reality.",
    ),
    file_b: UploadFile = File(
        ...,
        description="Image B — the counterfactual / after state of reality.",
    ),
    user_change_description: Optional[str] = Form(
        default=None,
        description=(
            "Optional free-text description of what the user believes changed. "
            "Treated as ground-truth context to augment visual analysis."
        ),
    ),
) -> CounterfactualAnalysis:
    """
    Core RealityShift endpoint.

    Workflow:
      1. Validate and read both uploaded images.
      2. Build a multimodal prompt with the two images and optional description.
      3. Call Gemma 4 with structured-output mode enforced.
      4. Parse and return the validated `CounterfactualAnalysis` object.
    """
    if genai_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GenAI client is not initialised. Check server logs.",
        )

    # --- 1. Validate Images ---
    logger.info(
        "Received analysis request | file_a=%s | file_b=%s | desc_provided=%s",
        file_a.filename,
        file_b.filename,
        bool(user_change_description),
    )

    bytes_a, mime_a = await _read_and_validate_image(file_a, "file_a")
    bytes_b, mime_b = await _read_and_validate_image(file_b, "file_b")

    # --- 2. Build Multimodal Prompt ---
    user_parts = _build_user_message(
        bytes_a, mime_a, bytes_b, mime_b, user_change_description
    )

    # --- 3. Call Gemma 4 with Structured Output ---
    try:
        logger.info("Sending request to Gemini API (model=%s)…", GEMMA_MODEL)

        response = genai_client.models.generate_content(
            model=GEMMA_MODEL,
            contents=[
                genai_types.Content(
                    role="user",
                    parts=user_parts,
                )
            ],
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.2,
                top_p=0.9,
                max_output_tokens=4096,
                # Disable AFC — pure structured JSON generation, no tool calls.
                automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

        logger.info(
            "Gemini API responded | finish_reason=%s | tokens_used=%s",
            response.candidates[0].finish_reason if response.candidates else "N/A",
            response.usage_metadata.total_token_count if response.usage_metadata else "N/A",
        )

    except Exception as exc:
        logger.exception("Gemini API call failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream model call failed: {type(exc).__name__}: {exc}",
        ) from exc

    # --- 4. Parse & Validate Structured Output (with retry) ---
    MAX_PARSE_RETRIES = 3
    last_exc: Exception | None = None
    analysis: CounterfactualAnalysis | None = None

    for attempt in range(1, MAX_PARSE_RETRIES + 1):
        try:
            # Path A: SDK already parsed the response into a Pydantic model.
            if hasattr(response, "parsed") and response.parsed is not None:
                analysis = response.parsed
                break

            # Path B: Robust extract & clean JSON from raw text response
            raw_text: str = response.text or ""
            cleaned = _clean_and_extract_json(raw_text)

            # Path C (attempt 2+): repair JSON if truncated
            if attempt > 1:
                cleaned = _repair_truncated_json(cleaned)

            logger.debug(
                "Parse attempt %d/%d | raw_len=%d | cleaned_len=%d",
                attempt, MAX_PARSE_RETRIES, len(raw_text), len(cleaned),
            )

            analysis = CounterfactualAnalysis.model_validate_json(cleaned)
            break  # Success — exit retry loop

        except ValidationError as exc:
            last_exc = exc
            logger.warning(
                "ValidationError on attempt %d/%d: %s",
                attempt, MAX_PARSE_RETRIES, exc,
            )
            if attempt == MAX_PARSE_RETRIES:
                logger.error(
                    "All %d parse attempts exhausted. Raw response: %s",
                    MAX_PARSE_RETRIES,
                    getattr(response, "text", "N/A"),
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Model output failed Pydantic validation after "
                        f"{MAX_PARSE_RETRIES} attempts: {exc}\n\n"
                        f"Raw response: {getattr(response, 'text', 'N/A')}"
                    ),
                ) from exc
            # On non-final attempts, fall through to retry the same response
            # text with a fresh parse (handles transient regex edge-cases).

        except Exception as exc:
            # Non-validation errors (e.g. response.text is None) — fail fast.
            logger.exception("Unexpected error parsing model output: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Unexpected parse error: {type(exc).__name__}: {exc}\n\n"
                    f"Raw response: {getattr(response, 'text', 'N/A')}"
                ),
            ) from exc

    logger.info(
        "Analysis complete | overall_severity=%s | entity_changes=%d | consequences=%d",
        analysis.overall_severity,
        len(analysis.entity_changes),
        len(analysis.consequences),
    )

    # Attach interactive causal graph with D3 nodes/edges + Mermaid diagram
    analysis.causal_graph = generate_causal_graph(analysis)

    return analysis


@app.post(
    "/api/v1/generate-graph",
    response_model=CausalGraph,
    status_code=status.HTTP_200_OK,
    summary="Generate a Causal Graph from an existing CounterfactualAnalysis",
    tags=["Graph"],
)
async def generate_graph_endpoint(analysis: CounterfactualAnalysis) -> CausalGraph:
    """
    Takes an existing CounterfactualAnalysis payload and returns an interactive
    causal graph with D3 nodes, edges, and renderable Mermaid syntax.
    """
    return generate_causal_graph(analysis)


@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Interactive RealityShift Web UI Dashboard",
    tags=["UI"],
)
@app.get(
    "/graph-viewer",
    response_class=HTMLResponse,
    summary="Interactive Causal Graph Viewer",
    tags=["UI"],
)
async def graph_viewer_dashboard() -> HTMLResponse:
    """
    Serves a modern glassmorphic dashboard with live image uploading,
    Gemma 4 counterfactual reasoning, and interactive Mermaid causal graph rendering.
    """
    return HTMLResponse(content=GRAPH_VIEWER_HTML, status_code=200)


# ---------------------------------------------------------------------------
# CLI Test Harness
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Prompt explicitly asks for markdown fences to exercise the regex stripper.
    test_prompt = (
        "Generate a simple counterfactual analysis for the scenario: "
        "'What if the apple was blue instead of red?' "
        "Return the response strictly as a CounterfactualAnalysis JSON object. "
        "Wrap your response in ```json markdown formatting."
    )

    print("=" * 60)
    print(" RealityShift — Standalone Test Harness")
    print("=" * 60)
    print(f"Model  : {GEMMA_MODEL}")
    print(f"Prompt : {test_prompt[:80]}...")
    print("-" * 60)
    print("Initiating RealityShift test sequence...\n")

    try:
        result = get_realityshift_analysis(test_prompt)

        print("\n[OK] SUCCESS: Engine returned a valid CounterfactualAnalysis object!")
        print("-" * 60)
        # model_dump_json() confirms Pydantic successfully instantiated the object
        print(result.model_dump_json(indent=2))

    except Exception as e:
        print(f"\n[FAIL] Engine crashed. Error details:\n{e}")
        sys.exit(1)
