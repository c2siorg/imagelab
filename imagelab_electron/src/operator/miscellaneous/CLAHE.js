const OpenCvOperator = require("../OpenCvOperator");

/**
 * This class contains the main logic
 * of CLAHE processing of the image
 */
class CLAHE extends OpenCvOperator {
  constructor(type, id) {
    super(type, id);
  }

  /**
   *
   * @param {Mat Image} image
   * @returns
   * Computes CLAHE
   * to the Processed Mat image
   */
  compute(image) {
    let equalDst = new this.cv2.Mat();
    let claheDst = new this.cv2.Mat();
    this.cv2.cvtColor(image, image, this.cv2.COLOR_RGBA2GRAY, 0);
    this.cv2.equalizeHist(image, equalDst);
    let tileGridSize = new this.cv2.Size(8, 8);
    let clahe = new this.cv2.CLAHE(40, tileGridSize);
    clahe.apply(image, claheDst);
    return claheDst;
  }
}

module.exports = CLAHE;
