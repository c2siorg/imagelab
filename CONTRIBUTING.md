# Contributing to ImageLab

Thank you for your interest in contributing to ImageLab! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/imagelab.git
   cd imagelab
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

ImageLab has two sub-projects. Depending on what you are working on, you may need to set up one or both of them.

### Frontend

The React + Vite frontend.

```bash
cd imagelab-frontend
cp .env.example .env
npm install
npm run dev
```

The frontend development server runs on port **3100**.

### Backend

The Python FastAPI backend that provides image processing services.

```bash
cd imagelab-backend
cp .env.example .env
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
uvicorn app.main:app --reload --port 4100
```

The backend API runs on port **4100**.

## Development Workflow

1. Make your changes in the appropriate sub-project.
2. Test your changes thoroughly.
3. Lint your code to ensure it follows the project style guidelines.
4. Write clear, descriptive commit messages.
5. Push your branch to your fork and open a Pull Request against the `main` branch.

### Pre-Commit Checklist to format the code

Before pushing your changes, run:

```bash
# Frontend
cd imagelab-frontend
npm run lint
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}"

# Backend
cd imagelab-backend
uv run ruff check . --fix
uv run ruff format
```

## Code Style

- **JavaScript/TypeScript:** We use ESLint and Prettier for linting and formatting. Run `npm run lint` where available to check your code.
- **Testing:** The frontend uses Vitest for unit testing (`imagelab-frontend/`); the backend uses pytest (`imagelab-backend/`).
- **Python:** Follow PEP 8 conventions for backend code.

## Reporting Bugs / Requesting Features

We use GitHub issue templates to track bugs and feature requests. When opening a new issue, please select the appropriate template:

- **Bug Report** -- for reporting bugs or unexpected behavior.
- **Feature Request** -- for suggesting new features or improvements.

Fill out the template as completely as possible to help us understand and address the issue.

## License

By contributing to ImageLab, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).