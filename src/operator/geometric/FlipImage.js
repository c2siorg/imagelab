const OpenCvOperator = require("../OpenCvOperator");

class FlipImage extends OpenCvOperator {
    #flipCode = 0; // 0: vertical, 1: horizontal, -1: both

    constructor(type, id) {
        super(type, id);
    }

    /**
     * Sets the parameters for the FlipImage operation.
     * @param {string} param - The parameter name.
     * @param {number} value - The value to set for the parameter.
     */
    setParams(param, value) {
        if (param === "flip_code") {
            const numericValue = Number(value)
            if (![0, 1, -1].includes(numericValue)) {
                throw new Error("Invalid flip_code value. Allowed values: 0 (vertical), 1 (horizontal), -1 (both).");
            }
            this.#flipCode = value;
        } else {
            throw new Error(`Unknown parameter: ${param}`);
        }
    }

    /**
     * Computes the flip transformation on the given image.
     * @param {cv.Mat} image - The image to be flipped.
     * @returns {cv.Mat|null} - The flipped image or null if an error occurs.
     */
    compute(image) {
        try {
            if (!image || !(image instanceof cv.Mat)) {
                console.log("Invalid image provided. Expected a valid OpenCV Mat object.");
                return null;
            }

            let dst = new cv.Mat();
            cv.flip(image, dst, this.#flipCode);
            return dst;

        } catch (error) {
            console.error("Error in FlipImage.compute():", error.message);
            return null;
        }
    }
}

module.exports = FlipImage;