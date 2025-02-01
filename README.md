
# ImageLab

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Introduction

Introduction

ImageLab is a standalone tool designed to help users learn and experiment with image processing techniques interactively. It provides an intuitive environment for beginners to understand image processing concepts without deep programming knowledge. Advanced users can use ImageLab as a test environment before implementing actual image processing applications.

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Contributing](#contributing)
- [Built Using](#built_using)

## About <a name = "about"></a>

ImageLab is built using the Blockly library and other technologies to provide a visual programming experience for image processing.

https://user-images.githubusercontent.com/43797542/130302770-b43a8ee4-fb59-4af2-b804-20e1847866f4.mp4

## Getting Started <a name = "getting_started"></a>

ImageLab is built using the Blockly library and other technologies to provide a visual programming experience for image processing.

### Prerequisites

Clone the ImageLab repository:

```
git clone https://github.com/c2siorg/imagelab.git
```

ImageLab uses ElectronJS, which requires Node.js. Download and install the latest LTS version from [Node.js](https://nodejs.org/en).

Verify the installation:

```
node -v
npm -v
```

These commands should display the installed versions of Node.js and npm.

### Installing

Install all dependencies:

```
npm install
```

## Usage <a name="usage"></a>

Start the ImageLab application:

```
npm start
```

After starting the application you can implement any combinations of image processing and
test them. But to execute correctly you need to set the first operator as "read_image" and
the last operator as "write_image" in the operations stack.

Following are the implemented functions that working currently,

- Basic functions
- Geometric functions (Except Image Reflect)
- Drawing functions (Except Draw Arrow)
- Blurring functions
- Filtering functions

\*Note - When starting the application two windows will be open. Main application window and the developer console. If you want to remove the developer console window remove the following line in the /main.js file.

```
 mainWindow.webContents.openDevTools();
```

### Debugging

When installing packages and running the application few issues can be arised. Following are the few steps that you can fix those isses.

- Check you node and npm versions. Make sure that they are updated to latest versions
- There may be npm libraries that have outdated. Try to fix those depedency issues by reffering [npmjs](https://www.npmjs.com)

## Contributing <a name = "contributing"></a>

If you need to contribute to this project, we are happy to hear that. Before starting any contributions please read our developer guidelines and then proceed. Following are the steps that you need to follow before implementing coding.

- Fork our repository and clone the individual repository and setup the development environment
- If you want to start implementing a new function type which not been implemented yet such as
  "Thresholding" then create a folder inside src/operator directory.
  Ex: If you need to implement the Thresholding functions create a folder name "thresholding" inside src/operator directory.
- Then create a javascript file with the name of the operator and implement the code.
  Ex: If you need to implement the Apply Border operator create a file named "applyborder.js".
- When implementing the functions use classes as below,

```javascript
class YourOperator extends OpenCvOperator {

    // This is the main contructor of the function
    constructor(type,id){
        super(type,id);
    }

    // This function set the parameters which are related with the class
    setParams(type, value) {
    }

    // This is the method which does the image processing work.
    compute(image){
      return image;
    }

}

```

Before running the implemented function you need to setup few other things as well,

- In /operations.js file define your opeation with the matching type selected from the /imagelab-blocks.js file.
  Ex:

```javascript
ADD_BORDER:"add_border"
```

- Modify the addOperator function inside the /src/controller/main.js file.

```javascript
case ADD_BORDER:
  this.#appliedOperators.push(
          new ApplyBorder(PROCESS_OPERATIONS.ADD_BORDER, id)
        );
  break;
```

After procceding above steps you can execute the implemented functions in the application.

## Adding Unit Tests

Unit tests are an essential part of ensuring the correctness and reliability of your image processing operators. This section provides a guide on how to add unit tests to the project.

### Prerequisites

1. **Install Dependencies:** If you haven't already, install the necessary dependencies by running the following command in your project's root directory:

   ```sh
   npm install --save-dev jest
   ```

### Getting Started

1. **Create Mocks:** To test image processing operators, create mock implementations for the OpenCv.js dependencies they use. Mock files should be placed in the `tests/unit/opencv-mocks/` directory. For each type of operator, create a mock file following this structure:
```bash
    tests/
    |-- unit/
    |   |-- opencv-mocks/
    |       |-- basic.mock.js
    |       |-- blurring.mock.js
    |       |-- conversions.mock.js
    |       |-- drawing.mock.js
    |       |-- filtering.mock.js
    |       |-- geometric.mock.js
    |       |-- thresholding.mock.js
```
2. **Write Unit Tests:** In the `tests/unit/ directory`, create test files for each operator. Name your test files using the format `<OperatorName>.test.js`. Here's an example of a generic unit test file:
    ```javascript

    //tests/unit/ExampleOperator.test.js
    const ExampleOperator = require('../../src/operators/ExampleOperator');
    const opencvMock = require('./opencv-mocks/example.mock'); // Adjust the path

    describe('ExampleOperator', () => {
      afterEach(() => {
        jest.clearAllMocks();
      });

      it('should apply example operator', () => {
        // Your code goes here
      });
      // Add more test cases as needed
    });
    ```

3. **Run Unit Tests:** Execute your unit tests using the following command:
    ```bash
    npm test -- --config=jest.config.js
    ```
