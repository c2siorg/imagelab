from app.operators.arithmetic.add_weighted import ArithmeticAddWeighted
from app.operators.augmentation.gaussian_noise import GaussianNoise
from app.operators.augmentation.salt_pepper_noise import SaltPepperNoise
from app.operators.augmentation.sepia_filter import SepiaFilter
from app.operators.base import BaseOperator
from app.operators.basic.read_image import ReadImage
from app.operators.basic.write_image import WriteImage
from app.operators.blurring.blur import Blur
from app.operators.blurring.gaussian_blur import GaussianBlur
from app.operators.blurring.median_blur import MedianBlur
from app.operators.conversions.bgr_to_hsv import BgrToHsv
from app.operators.conversions.bgr_to_lab import BgrToLab
from app.operators.conversions.bgr_to_ycrcb import BgrToYcrcb
from app.operators.conversions.brightness_and_contrast import BrightnessAndContrast
from app.operators.conversions.channel_split import ChannelSplit
from app.operators.conversions.clahe import ClaheImage
from app.operators.conversions.color_maps import ColorMaps
from app.operators.conversions.color_to_binary import ColorToBinary
from app.operators.conversions.gamma_correction import GammaCorrection
from app.operators.conversions.gray_image import GrayImage
from app.operators.conversions.gray_to_binary import GrayToBinary
from app.operators.conversions.histogram_equalization import HistogramEqualization
from app.operators.conversions.hsv_to_bgr import HsvToBgr
from app.operators.conversions.invert_image import InvertImage
from app.operators.conversions.lab_to_bgr import LabToBgr
from app.operators.conversions.ycrcb_to_bgr import YcrcbToBgr
from app.operators.detection.corner_detection import CornerDetection
from app.operators.detection.eye_detection import EyeDetection
from app.operators.detection.face_detection import FaceDetection
from app.operators.detection.smile_detection import SmileDetection
from app.operators.drawing.draw_arrow_line import DrawArrowLine
from app.operators.drawing.draw_circle import DrawCircle
from app.operators.drawing.draw_ellipse import DrawEllipse
from app.operators.drawing.draw_line import DrawLine
from app.operators.drawing.draw_rectangle import DrawRectangle
from app.operators.drawing.draw_text import DrawText
from app.operators.filtering.bilateral_filter import BilateralFilter
from app.operators.filtering.box_filter import BoxFilter
from app.operators.filtering.canny_edge import CannyEdge
from app.operators.filtering.contour_detection import ContourDetection
from app.operators.filtering.dilation import Dilation
from app.operators.filtering.erosion import Erosion
from app.operators.filtering.gabor_filter import GaborFilter
from app.operators.filtering.hough_lines import HoughLines
from app.operators.filtering.laplacian import Laplacian as FilteringLaplacian
from app.operators.filtering.morphological import Morphological
from app.operators.filtering.pyramid_down import PyramidDown
from app.operators.filtering.pyramid_up import PyramidUp
from app.operators.filtering.sharpen import Sharpen
from app.operators.geometric.affine_image import AffineImage
from app.operators.geometric.crop_image import CropImage
from app.operators.geometric.reflect_image import ReflectImage
from app.operators.geometric.resize_image import ResizeImage
from app.operators.geometric.rotate_image import RotateImage
from app.operators.geometric.scale_image import ScaleImage
from app.operators.segmentation.kmeans_segmentation import KMeansSegmentation
from app.operators.segmentation.mean_shift_segmentation import MeanShiftSegmentation
from app.operators.segmentation.watershed import Watershed
from app.operators.sobel_derivatives.prewitt_operator import PrewittOperator
from app.operators.sobel_derivatives.roberts_operator import RobertsOperator
from app.operators.sobel_derivatives.scharr_derivative import ScharrDerivative
from app.operators.sobel_derivatives.sobel_derivative import SobelDerivative
from app.operators.thresholding.adaptive_threshold import AdaptiveThreshold
from app.operators.thresholding.apply_borders import ApplyBorders
from app.operators.thresholding.apply_threshold import ApplyThreshold
from app.operators.thresholding.otsu_threshold import OtsuThreshold
from app.operators.transformation.distance_transform import DistanceTransform
from app.operators.transformation.laplacian import Laplacian as TransformationLaplacian

OPERATOR_REGISTRY: dict[str, type[BaseOperator]] = {
    # Basic
    "basic_readimage": ReadImage,
    "basic_writeimage": WriteImage,
    # Geometric
    "geometric_reflectimage": ReflectImage,
    "geometric_resizeimage": ResizeImage,
    "geometric_rotateimage": RotateImage,
    "geometric_scaleimage": ScaleImage,
    "geometric_affineimage": AffineImage,
    "geometric_cropimage": CropImage,
    # Conversions
    "imageconversions_clahe": ClaheImage,
    "imageconversions_grayimage": GrayImage,
    "imageconversions_channelsplit": ChannelSplit,
    "imageconversions_graytobinary": GrayToBinary,
    "imageconversions_colormaps": ColorMaps,
    "imageconversions_colortobinary": ColorToBinary,
    "imageconversions_histogramequalization": HistogramEqualization,
    "imageconversions_bgrtohsv": BgrToHsv,
    "imageconversions_hsvtobgr": HsvToBgr,
    "imageconversions_bgrtolab": BgrToLab,
    "imageconversions_labtobgr": LabToBgr,
    "imageconversions_bgrtoycrcb": BgrToYcrcb,
    "imageconversions_ycrcbtobgr": YcrcbToBgr,
    "imageconversions_invertimage": InvertImage,
    "imageconversions_brightnessandcontrast": BrightnessAndContrast,
    "imageconversions_gammacorrection": GammaCorrection,
    # Drawing
    "drawingoperations_drawline": DrawLine,
    "drawingoperations_drawcircle": DrawCircle,
    "drawingoperations_drawellipse": DrawEllipse,
    "drawingoperations_drawrectangle": DrawRectangle,
    "drawingoperations_drawarrowline": DrawArrowLine,
    "drawingoperations_drawtext": DrawText,
    # Blurring
    "blurring_applyblur": Blur,
    "blurring_applygaussianblur": GaussianBlur,
    "blurring_applymedianblur": MedianBlur,
    # Filtering
    "filtering_boxfilter": BoxFilter,
    "filtering_bilateral": BilateralFilter,
    "filtering_cannyedge": CannyEdge,
    "filtering_houghlines": HoughLines,
    "filtering_sharpen": Sharpen,
    "filtering_pyramidup": PyramidUp,
    "filtering_pyramiddown": PyramidDown,
    "filtering_erosion": Erosion,
    "filtering_dilation": Dilation,
    "filtering_morphological": Morphological,
    # Augmentation
    "augmentation_gaussiannoise": GaussianNoise,
    "augmentation_saltpeppernoise": SaltPepperNoise,
    "augmentation_sepiafilter": SepiaFilter,
    "filtering_gaborfilter": GaborFilter,
    "filtering_contourdetection": ContourDetection,
    # Detection
    "detection_cornerdetection": CornerDetection,
    "detection_eyedetection": EyeDetection,
    "detection_facedetection": FaceDetection,
    "detection_smiledetection": SmileDetection,
    # Thresholding
    "thresholding_applythreshold": ApplyThreshold,
    "thresholding_adaptivethreshold": AdaptiveThreshold,
    "thresholding_applyborders": ApplyBorders,
    "thresholding_otsuthreshold": OtsuThreshold,
    # Sobel Derivatives
    "sobelderivatives_soblederivate": SobelDerivative,
    "sobelderivatives_scharrderivate": ScharrDerivative,
    "sobelderivatives_prewittoperator": PrewittOperator,
    "sobelderivatives_robertsoperator": RobertsOperator,
    # Transformation
    "transformation_distance": DistanceTransform,
    "transformation_laplacian": TransformationLaplacian,
    # Segmentation
    "segmentation_watershed": Watershed,
    "segmentation_kmeans": KMeansSegmentation,
    "segmentation_meanshift": MeanShiftSegmentation,
    "laplacian": FilteringLaplacian,
    "arithmetic_addweighted": ArithmeticAddWeighted,
}

# Deliberate legacy alias table for backward compatibility with saved pipelines
LEGACY_OPERATOR_ALIASES: dict[str, str] = {
    f"imageconvertions_{name}": f"imageconversions_{name}"
    for name in [
        "clahe",
        "grayimage",
        "channelsplit",
        "graytobinary",
        "colormaps",
        "colortobinary",
        "histogramequalization",
        "bgrtohsv",
        "hsvtobgr",
        "bgrtolab",
        "labtobgr",
        "bgrtoycrcb",
        "ycrcbtobgr",
        "invertimage",
        "brightnessandcontrast",
    ]
}


def resolve_operator_name(block_type: str) -> str:
    """Resolve legacy operator key typos to their canonical names."""
    return LEGACY_OPERATOR_ALIASES.get(block_type, block_type)


def get_operator(block_type: str) -> type[BaseOperator] | None:
    return OPERATOR_REGISTRY.get(resolve_operator_name(block_type))
