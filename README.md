# ImageLab

[![CI](https://github.com/c2siorg/imagelab/actions/workflows/ci.yml/badge.svg)](https://github.com/c2siorg/imagelab/actions/workflows/ci.yml)
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
- PostgreSQL

## Getting Started

### Electron App (Legacy)

```bash
cd electron-app-legacy
npm install
npm start
```

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
# Electron app
cd electron-app-legacy && npm test

# Backend
cd imagelab-backend && uv run pytest

# Frontend
cd imagelab-frontend && npm run test
```

## Project Structure

```
imagelab/
  electron-app-legacy/   # Original Electron + Blockly app
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
