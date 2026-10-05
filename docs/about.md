---
layout: page
title: About
---

ImageLab is a standalone tool which supports anyone to get started with image processing related concepts and techniques in an interactive, visual way. Users drag and connect blocks to build image processing pipelines without writing code. ImageLab is ideal for beginners learning image processing and for experienced users who want a quick test environment.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## How It Works

The interface is a set of drag-and-drop blocks in the browser, built with [Google Blockly](https://blockly.google.com/). Connecting those blocks defines a pipeline, and a separate Python backend executes that pipeline against the uploaded image using OpenCV. The frontend never runs image processing itself, so the same blocks behave identically whether the app is served from a development machine or deployed.

The Electron desktop build is the legacy application. The current application is the React web frontend plus the Python API.

## Supported Image Processing Operations

The toolbox exposes 13 categories covering 64 blocks:

| Category | What it covers |
|---|---|
| Basic | Reading and writing the image |
| Geometric | Reflect, crop, rotate, affine transform, scale, resize |
| Conversions | Colour space conversion (gray, HSV, LAB, YCrCb), channel split, CLAHE, colour maps, binarisation, histogram equalisation, invert, brightness and contrast |
| Augmentation | Gaussian noise, salt and pepper noise, sepia |
| Drawing | Lines, arrows, circles, ellipses, rectangles, text |
| Blurring | Box, Gaussian, median |
| Filtering | Bilateral, sharpen, morphological erode and dilate, Gabor, box, pyramid up and down, contour detection, Canny edge detection |
| Thresholding | Global and adaptive threshold, Otsu, borders |
| Segmentation | K-Means, Mean Shift, Watershed |
| Detection | Smile and eye detection using Haar cascades |
| Sobel Derivatives | Sobel, Scharr, Prewitt |
| Transformation | Distance transform, Laplacian |
| Advanced control flow macros | Parallel blend, conditional (if/else) |

## Technologies

### Frontend

| Technology | Description |
|---|---|
| React | UI library |
| Vite | Build tool and development server |
| TypeScript | Language |
| Blockly | Visual block editor |
| Tailwind CSS | Styling |
| Zustand | Client-side state |

### Backend

| Technology | Description |
|---|---|
| FastAPI | HTTP API and pipeline execution |
| OpenCV (`opencv-python-headless`) | Image processing |
| SQLModel with PostgreSQL | Persistence for saved pipelines and macros |
| Alembic | Database migrations |
| Pydantic | Configuration and request validation |

### Testing and tooling

| Technology | Description |
|---|---|
| Vitest with Testing Library | Frontend testing |
| pytest | Backend testing |
| ESLint and Prettier | Linting and formatting |
| Node.js | Frontend build toolchain |

## Mentors
- [Namal Jayasuriya]()
- [Oshan Mudannayake](https://github.com/ivantha)
- [Deniz Karakay](https://github.com/dkarakay)
- [Tuan Amith]()
- [Sumedha Dissanayaka](https://github.com/sumedhe)

## Contributors
- [Dilum De Silva](https://github.com/dilum1995)
- [Sahan Dissanayaka](https://github.com/SahanDisa)
