# ImageLab

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A desktop application for visual, block-based image processing using Google Blockly and OpenCV.js. ImageLab lets users drag and connect blocks to build image processing pipelines without writing code. The project includes a legacy Electron app, a new React frontend, and a Python backend.

## Quick Demo

1. **Start the application** using the setup instructions above
2. **Load an image** using the "Read Image" block
3. **Add processing blocks** like "Gaussian Blur" or "Gray Image" 
4. **Connect the blocks** to create your processing pipeline
5. **See real-time results** as you build your pipeline
6. **Save your result** using the "Write Image" block

The visual interface makes it easy to experiment with different image processing techniques without writing any code!

## Features

- Block-based image processing using Google Blockly — no coding required
- OpenCV.js powered operations: blurring, filtering, thresholding, geometric transforms, and more
- Drag-and-connect blocks to build image processing pipelines
- Real-time preview of processing results
- Legacy Electron desktop app and modern React + FastAPI web app

## Prerequisites

- [Node.js](https://nodejs.org/) >= 18
- Python 3.12+
- PostgreSQL (for backend database)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker (optional, for containerized deployment)

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

## Docker Deployment

For containerized deployment, you can use Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop services
docker-compose down
```

This will start both the frontend and backend services in containers with the appropriate networking configured.

## Environment Variables

### Backend (.env)
Make sure to configure your backend environment by copying `.env.example` to `.env` and setting:
- **DATABASE_URL**: PostgreSQL connection string
- **CORS_ORIGINS**: Allowed CORS origins (typically frontend URL)

### Frontend (.env)
Configure your frontend environment by copying `.env.example` to `.env` and setting:
- **VITE_API_BASE_URL**: Backend API URL (typically `http://localhost:4100`)

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
