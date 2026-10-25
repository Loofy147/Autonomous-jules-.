# Extension Plugins & Technology Demonstrations Guide

## Overview
This document outlines proposals, architectural specifications, and implementation patterns for extending **Autonomous Jules** with advanced technology plugins and demonstrations.

---

## 1. Webhook Event Listener Plugin (Real-Time Notifications)

### Purpose
Eliminates polling overhead by providing a real-time HTTP server endpoint (`/webhooks/jules`) that receives task state completion callbacks directly from the Jules API or GitHub Actions dispatches.

### Architecture
- **Framework**: `Starlette` or `FastAPI` with `uvicorn`.
- **Event Dispatcher**: Triggers `AsyncPipelineRunner` execution upon receiving `task.completed` or `workflow_run.completed` payloads.
- **HMAC Signature Validation**: Verifies `X-Jules-Signature` or `X-Hub-Signature-256` headers using secret tokens.

```python
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

async def jules_webhook(request):
    payload = await request.json()
    task_id = payload.get("task_id")
    status = payload.get("status")
    # Resume pipeline step corresponding to task_id
    return JSONResponse({"ok": True, "task_id": task_id, "status": status})

app = Starlette(routes=[Route("/webhooks/jules", jules_webhook, methods=["POST"])])
```

---

## 2. Semantic Comparator Extension for Decision Ledger

### Purpose
Extends `ledger.py` mechanical string comparators (`exact`, `numeric_range`) with a vector-embedding semantic comparator (`semantic_similarity`) that identifies semantic contradictions across differently phrased entries.

### Architecture
- **Embedding Engine**: Lightweight embedding models (e.g. `sentence-transformers` or OpenAI `text-embedding-3-small`).
- **Comparator Function**: Measures cosine similarity between entry values. Values with similarity below a threshold (e.g., `< 0.70`) under the same key are flagged as potential contradictions.

```python
def cmp_semantic_similarity(a: str, b: str, threshold: float = 0.75) -> bool:
    # Example pseudo-implementation using vector similarity
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer('all-MiniLM-L6-v2')
    emb1 = model.encode(a, convert_to_tensor=True)
    emb2 = model.encode(b, convert_to_tensor=True)
    similarity = float(util.cos_sim(emb1, emb2)[0][0])
    return similarity >= threshold
```

---

## 3. Multi-Agent Swarm Consensus Hub Plugin

### Purpose
Leverages `hub_adapter/hub.py` to allow multi-agent swarms to vote on resolving ledger contradictions across independent execution nodes.

### Architecture
- **Protocol**: WebSocket RPC over `hub_adapter/hub.py`.
- **Voting Mechanism**: When `ledger_check` flags a contradiction, the hub requests consensus votes from connected agent peers. Upon majority consensus (`>= 51%`), a resolution entry with `--supersedes` is automatically generated and committed.

```
+----------------+          +------------------------+          +----------------+
| Agent Node A   | -------> | WebSocket RPC Hub      | <------- | Agent Node B   |
| (Proposes Res) |          | (Swarm Consensus Hub)  |          | (Votes on Res) |
+----------------+          +------------------------+          +----------------+
```

---

## 4. OpenTelemetry Observability Plugin

### Purpose
Provides distributed tracing and span context propagation across `AsyncPipelineRunner` steps, Jules API calls, GitHub REST calls, and MCP tool executions.

### Architecture
- **Instrumentation**: Standard `opentelemetry-api` and `opentelemetry-sdk`.
- **Traces**: Emits span metrics for step execution durations, retries, and ledger contradiction checks.

```python
from opentelemetry import trace

tracer = trace.get_tracer("autonomous-jules")

with tracer.start_as_current_span("run_pipeline_step") as span:
    span.set_attribute("action", action)
    span.set_attribute("task_id", task_id)
    # Execute pipeline step action
```
