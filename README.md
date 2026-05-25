# ImageLab

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A desktop application for visual, block-based image processing using Google Blockly and OpenCV.js. ImageLab lets users drag and connect blocks to build image processing pipelines without writing code. The project includes a legacy Electron app, a new React frontend, and a Python backend.

## Features

- Block-based image processing using Google Blockly — no coding required
- OpenCV.js powered operations: blurring, filtering, thresholding, geometric transforms, and more
- Drag-and-connect blocks to build image processing pipelines
- Real-time preview of processing results
- Legacy Electron desktop app and modern React + FastAPI web app

## Prerequisites

- [Node.js](https://nodejs.org/) >= 18
- Python 3.12+
- [PostgreSQL](https://www.postgresql.org/download/)
- [uv](https://github.com/astral-sh/uv) - Python package installer
  ```bash
  pip install uv
  ```

## Getting Started

### Backend

```bash
cd imagelab-backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 4100
```

### Frontend

```bash
cd imagelab-frontend
cp .env.example .env
npm install
npm run dev
```

| Service  | Port |
|----------|------|
| Frontend | 3100 |
| Backend  | 4100 |

## Running Tests

```bash
# Backend
cd imagelab-backend && uv run pytest

# Frontend
cd imagelab-frontend && npm run test
```

## Pipeline API

The React app uses the FastAPI backend to execute pipelines and inspect intermediate images.

- `POST /api/v1/pipeline/executions` executes the submitted pipeline and returns the final image, per-step thumbnails, timings, and an `execution_id`.
- `GET /api/v1/pipeline/executions/{execution_id}/steps/inspect?block_id=...` returns the full-resolution image for one cached step.

The legacy `/api/pipeline/execute` endpoint has been removed. Full-resolution step images are cached in backend memory with a TTL and max-entry bound; clients should keep the lightweight thumbnails from the execution response and fetch full-resolution step images only when selected.

## Project Structure

```
imagelab/
  imagelab-frontend/     # React + Vite frontend
  imagelab-backend/      # Python FastAPI backend
  docs/                  # Project documentation site
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).

## License

[Apache 2.0](LICENSE)

## Author

[Oshan Mudannayake](mailto:oshan.ivantha@gmail.com)

For questions or queries about this project, please reach out via email.
