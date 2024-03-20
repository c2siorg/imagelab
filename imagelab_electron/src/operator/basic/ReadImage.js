const OpenCvOperator = require("../OpenCvOperator");

/**
 * This class contains the main logic to read the image
 */
class ReadImage extends OpenCvOperator {
  constructor(type, id) {
    super(type, id);
  }

  /**
   * This function reads the given image
   * @param {Mat} image
   * @returns processed image
   */
  compute(image) {
    if(image.id.includes("video"))
    {
      console.log("inside video");
      const video = image
      let canvas = document.getElementById('image-preview')
      const FPS = 30;

      let cv; // Declare cv outside the promise for global access

        // Load OpenCV.js asynchronously (assuming you have a local copy)
        const cvPromise = new Promise(resolve => {
            const script = document.createElement("script");
            script.src = "C:\Users\dipak\practice\Gsoc\c2si\imagelabc2sr\imagelab_electron\src\opencv.js";
            script.onload = () => resolve(cv);
            script.onerror = () => reject(new Error("Error loading OpenCV.js")); // Handle error
            document.body.appendChild(script);
        });

        cvPromise.then(async (cv) => {
            const processVideo = async () => {
                if (!video.readyState) {
                    console.log("Video not ready yet...");
                    await new Promise(resolve => setTimeout(resolve, 100));
                    return processVideo(); // Recursively call until video is ready
                }

                const srcImage = new cv.Mat(video.height, video.width, cv.CV_8UC4);
                const dstImage = new cv.Mat(video.height, video.width, cv.CV_8UC1);

                video.play(); // Ensure video playback

                const captureVideoFrame = async () => {
                    await new Promise(resolve => video.onplaying = resolve); // Wait for video to start playing

                    if (!video.paused && video.videoWidth > 0) {
                        const cap = new cv.VideoCapture(video);

                        cap.read(srcImage);
                        cv.cvtColor(srcImage, dstImage, cv.COLOR_RGBA2GRAY);
                        cv.imshow(canvas, dstImage);

                        const delay = 1000 / FPS - (Date.now() - performance.now()); // Use performance.now() for better timing
                        setTimeout(captureVideoFrame, Math.max(0, delay)); // Cap delay at 0 to avoid negative values

                        cap.release(); // Release capture object after each frame
                    } else {
                        console.log("Video capture failed");
                    }
                };

                await captureVideoFrame();
            };

            processVideo();
        });
    }
    else
    {
    console.log("inside image");
    return this.cv2.imread(image);
    }
  }
}

module.exports = ReadImage;
