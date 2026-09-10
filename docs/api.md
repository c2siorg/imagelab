---
layout: page
title: API
---

The React frontend executes image pipelines through the FastAPI backend.

## Pipeline execution

`POST /api/v1/pipeline/executions`

Executes a submitted pipeline and returns:

- the final processed image
- an `execution_id`
- lightweight thumbnails for each completed step
- per-step and total timings

## Step inspection

`GET /api/v1/pipeline/executions/{execution_id}/steps/inspect?block_id=...`

Fetches the full-resolution image for one cached step. Pass `block_id` as a query parameter because Blockly block IDs may contain characters that are unsafe in URL path segments.

## Cache behavior

Full-resolution step images are cached in backend memory with a time-to-live and a maximum entry count. Clients should keep the thumbnails returned by the execution endpoint and request a full-resolution step image only when the user selects or expands that step.

The legacy `/api/pipeline/execute` endpoint has been removed.
