package com.imagelab.operator.imagebluring;

import com.imagelab.operator.OpenCVOperator;
import com.imagelab.operator.basic.ReadImage;
import com.imagelab.operator.basic.WriteImage;
import com.imagelab.operator.geotransformation.ColorMaps;
import com.imagelab.operator.geotransformation.ImageAffine;
import com.imagelab.operator.geotransformation.ImageReflection;
import com.imagelab.operator.geotransformation.RotateImage;
import com.imagelab.operator.geotransformation.ScaleImage;
import com.imagelab.operator.imageconversion.ColoredImageToBinary;
import com.imagelab.operator.imageconversion.ConvertToGrayscale;
import org.opencv.core.Mat;
import org.opencv.imgproc.Imgproc;

import java.util.HashSet;
import java.util.Set;

/**
 * Operator class which contains the logic related to the
 * applying bilateral blur effects to an image  UI element.
 */
public class ApplyBilateralBlur extends OpenCVOperator {
    // properties of bilateral blur effect.
    private int diameter = 15;
    private int sigmaColor = 80;
    private int sigmaSpace = 80;

    @Override
    public boolean validate(OpenCVOperator previous) {
        if (previous == null) {
            return false;
        }
        return allowedOperators().contains(previous.getClass());
    }


    @Override
    public Mat compute(Mat image) {
        return applyBilateralBlurEffect(image, getDiameter(), getsigmaColor(), getsigmaSpace());
    }

    @Override
    public Set<Class<?>> allowedOperators() {
        Set<Class<?>> allowed = new HashSet<>();
        allowed.add(ReadImage.class);
        allowed.add(RotateImage.class);
        allowed.add(ColorMaps.class);
        allowed.add(ScaleImage.class);
        allowed.add(ImageAffine.class);
        allowed.add(ImageReflection.class);
        allowed.add(WriteImage.class);
        allowed.add(ColoredImageToBinary.class);
        allowed.add(ConvertToGrayscale.class);
        allowed.add(ApplyBlurEffect.class);
        allowed.add(ApplyGaussianBlurEffect.class);
        allowed.add(ApplyMedianBlurEffect.class);
        allowed.add(ApplyBilateralBlur.class);
        return allowed;
    }

    private Mat applyBilateralBlurEffect(Mat imageFile,
                                        int diameter, int sigmaSpace, int sigmaColor) {
        Mat image = new Mat();
        Imgproc.bilateralFilter(imageFile, image, diameter, sigmaColor, sigmaSpace);
        return image;
    }

    public int getDiameter() {
        return diameter;
    }

    public void setDiameter(int diameter) {
        this.diameter = diameter;
    }

    public int getsigmaColor() {
        return sigmaColor;
    }

    public void setsigmaColor(int sigmaColor) {
        this.sigmaColor = sigmaColor;
    }

    public int getsigmaSpace() {
        return sigmaSpace;
    }

    public void setsigmaSpace(int sigmaSpace) {
        this.sigmaSpace = sigmaSpace;
    }

    /**
     * Information related to the ApplyBilateralBlurEffect operator.
     */
    public enum Information {
        /**
         * Operator information in string format.
         */
        OPERATOR_INFO {
            /**
             * @return - Operator information and name of the operator.
             */
            public String toString() {
                return "Apply bilateral blur\n\nThis operations allows"
                        + " you to apply bilateral blur effects to your image.";
            }
        }
    }
}
