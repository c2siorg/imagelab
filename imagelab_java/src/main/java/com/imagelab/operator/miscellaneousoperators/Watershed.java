package com.imagelab.operator.miscellaneousoperators;

import java.util.HashSet;
import java.util.Set;

import org.opencv.core.Core;
import org.opencv.core.CvType;
import org.opencv.core.Mat;
import org.opencv.core.Point;
import org.opencv.core.Size;
import org.opencv.imgproc.Imgproc;

import com.imagelab.operator.OpenCVOperator;
import com.imagelab.operator.basic.ReadImage;
import com.imagelab.operator.basic.WriteImage;
import com.imagelab.operator.drawing.DrawCircle;
import com.imagelab.operator.drawing.DrawLine;
import com.imagelab.operator.filtering.ApplyBoxFilter;
import com.imagelab.operator.filtering.ApplyErosion;
import com.imagelab.operator.filtering.ApplyImagePyramid;
import com.imagelab.operator.filtering.ApplyImagePyramidDown;
import com.imagelab.operator.geotransformation.ImageAffine;
import com.imagelab.operator.geotransformation.ImageReflection;
import com.imagelab.operator.geotransformation.RotateImage;
import com.imagelab.operator.imagebluring.ApplyBlurEffect;
import com.imagelab.operator.imagebluring.ApplyGaussianBlurEffect;
import com.imagelab.operator.imagebluring.ApplyMedianBlurEffect;
import com.imagelab.operator.imageconversion.ColoredImageToBinary;
import com.imagelab.operator.imageconversion.ConvertToGrayscale;


public class Watershed extends OpenCVOperator{

	private int lowThreshold = 60;
	
	private int highThreshold = 180;

	@Override
	public boolean validate(OpenCVOperator previous) {
		if (previous == null) {
            return false;
        }
        return allowedOperators().contains(previous.getClass());
	}

	@Override
	public Mat compute(Mat image) {
		System.out.println("Applied Watershed Algorithm");
        return watershedAlgorithm(image,getLowThreshold(),getHighThresold());
	}

	private Mat watershedAlgorithm(Mat src,int low,int high){
		  // Creating an empty matrix to store the result -> store the edges
	      Mat bg = new Mat();
          Mat fg = new Mat();
          Mat markers = new Mat();
          Mat marker_tempo = new Mat();
      
	      // Empty matrix for gry image
	      Mat gray = new Mat();
          // Kernel for morphological operations
          Mat kernel = Imgproc.getStructuringElement(Imgproc.MORPH_RECT, new Size((2*2) + 1, (2*2)+1));
	      
	      // Converting the image from color to Gray
	      Imgproc.cvtColor(src, gray, Imgproc.COLOR_BGR2GRAY);

          // Thresholding the image
	      Imgproc.threshold(gray, gray, low, high, Imgproc.THRESH_OTSU);
	      
	      // Open
	      Imgproc.morphologyEx(gray, gray, Imgproc.MORPH_OPEN, kernel);

          // Background
          Imgproc.dilate(gray, bg, kernel);
          Imgproc.threshold(bg,bg,1, 128,Imgproc.THRESH_BINARY_INV);

          // Foreground
          Imgproc.erode(gray,fg,new Mat(),new Point(-1,-1),2);

          Core.add(fg, bg, markers);

          markers.convertTo(marker_tempo, CvType.CV_32S);
        
          // Watershed Algorithm
          Imgproc.watershed(src, marker_tempo);

	      return marker_tempo;
	}
	/**
	 * Type integer
	 * @return
	 */
	public int getLowThreshold() {
		return this.lowThreshold;
	}
	/**
     * To set the low threshold of the output image.
     *
     * @return - low threshold
     */ 
	public void setLowThreshold(int low) {
		this.lowThreshold = low;
	}
	/**
     * To get the high threshold of the output image.
     *
     * @return - high threshold
     */
    public int getHighThresold() {
        return this.highThreshold;
    }

    /**
     * To set the high threshold of the output image.
     *
     * @param highThreshold -high threshold
     */
    public void setHighThresold(int high) {
        this.highThreshold = high;
    }

	@Override
	public Set<Class<?>> allowedOperators() {
		Set<Class<?>> allowed = new HashSet<>();
		allowed.add(ReadImage.class);
        allowed.add(RotateImage.class);
        allowed.add(WriteImage.class);
        allowed.add(DrawLine.class);
        allowed.add(DrawCircle.class);
        allowed.add(ColoredImageToBinary.class);
        allowed.add(ConvertToGrayscale.class);
        allowed.add(ApplyBlurEffect.class);
        allowed.add(ApplyGaussianBlurEffect.class);
        allowed.add(ApplyMedianBlurEffect.class);
        allowed.add(ApplyBoxFilter.class);
        allowed.add(ApplyImagePyramidDown.class);
        allowed.add(ApplyImagePyramid.class);
        allowed.add(ApplyErosion.class);
        allowed.add(ImageAffine.class);
        allowed.add(ImageReflection.class);
        return allowed;
	}
	public enum Information {
        /**
         * Operator information in string format.
         */
        OPERATOR_INFO {
            /**
             * @return - Operator information and name
             * of the operator.
             */
            public String toString() {
                return "Watershed\n\n used to detect the edges in an image."
                        + " It accepts a RGB image as input and it uses a multistage algorithm."
                        + " You can perform this operation on an image using the Watershed() function in OpenCV.";
            }
        }
    }
	
	
}
