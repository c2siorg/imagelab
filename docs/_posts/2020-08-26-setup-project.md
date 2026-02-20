---
layout: post
title: ImageLab Documentation
---

<br>Documentation for setting up and contributing to ImageLab.

## Outline

1. Setting up the environment
2. Setting up the project
3. Starting Contribution
4. Adding new image processing operations
5. Updating Docs

<br>

## 1. Setting up the environment

ImageLab is built with Electron, Blockly, and OpenCV.js. You need Node.js to run it.

### 1.1 Install Node.js

Download and install the latest LTS version from [Node.js](https://nodejs.org/en).

Verify the installation:

```
node -v
npm -v
```

<br>

## 2. Setting up the project

Clone the repository:

```
git clone https://github.com/c2siorg/imagelab.git
```

Navigate to the project directory and install dependencies:

```
cd imagelab
npm install
```

Run the application:

```
npm start
```

Run tests:

```
npm test
```

<br>

## 3. Starting Contribution

The project follows a modular structure:

- `src/blocks/` — Blockly block definitions (one file per category)
- `src/operator/` — Image processing operator classes (grouped by category)
- `src/registry/` — Operator registry and operation constants
- `src/controller/` — Pipeline controller
- `src/blockly/` — Workspace setup and extensions
- `src/ui/` — UI components (theme toggle, titlebar, guide)
- `tests/unit/` — Unit tests with OpenCV mocks

<br>

## 4. Adding new image processing operations

To add a new operator, follow these steps:

### 4.1 Create the operator class

Create a new file in `src/operator/<category>/<OperatorName>.js` extending `OpenCvOperator`:

```javascript
const OpenCvOperator = require("../OpenCvOperator");

class YourOperator extends OpenCvOperator {
    constructor(type, id) {
        super(type, id);
    }

    setParams(param, value) {
        // Update internal parameters
    }

    compute(image) {
        // Process and return cv2 Mat
        return image;
    }
}

module.exports = YourOperator;
```

### 4.2 Define the Blockly block

Add a block definition to the appropriate file in `src/blocks/<category>.blocks.js`.

### 4.3 Register the operator

In `src/registry/operations.js`, import your operator and register it:

```javascript
const YourOperator = require("../operator/<category>/YourOperator");
OperatorRegistry.register("category_youroperator", "YOUROPERATOR", YourOperator);
```

### 4.4 Add unit tests

Create a test file at `tests/unit/<category>/YourOperator.test.js` using the mock patterns in `tests/unit/opencv-mocks/`.

<br>

## 5. Updating Docs

The documentation site uses Jekyll. To run it locally:

1. Install [Ruby](https://www.ruby-lang.org/) and [Jekyll](https://jekyllrb.com/)
2. Run `bundle install` in the `docs/` directory
3. Run `bundle exec jekyll serve --livereload`
4. Visit `localhost:4000`

<br>
