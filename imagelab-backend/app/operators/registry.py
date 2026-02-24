from app.operators.base import BaseOperator
from app.operators.basic.read_image import ReadImage
from app.operators.basic.write_image import WriteImage
from app.operators.blurring.blur import Blur
from app.operators.blurring.gaussian_blur import GaussianBlur
from app.operators.blurring.median_blur import MedianBlur
from app.operators.conversions.color_maps import ColorMaps
from app.operators.conversions.color_to_binary import ColorToBinary
from app.operators.conversions.gray_image import GrayImage
from app.operators.conversions.gray_to_binary import GrayToBinary
from app.operators.drawing.draw_arrow_line import DrawArrowLine
from app.operators.drawing.draw_circle import DrawCircle
from app.operators.drawing.draw_ellipse import DrawEllipse
from app.operators.drawing.draw_line import DrawLine
from app.operators.drawing.draw_rectangle import DrawRectangle
from app.operators.drawing.draw_text import DrawText
from app.operators.filtering.bilateral_filter import BilateralFilter
from app.operators.filtering.box_filter import BoxFilter
from app.operators.filtering.dilation import Dilation
from app.operators.filtering.erosion import Erosion
from app.operators.filtering.morphological import Morphological
from app.operators.filtering.pyramid_down import PyramidDown
from app.operators.filtering.pyramid_up import PyramidUp
from app.operators.geometric.affine_image import AffineImage
from app.operators.geometric.reflect_image import ReflectImage
from app.operators.geometric.rotate_image import RotateImage
from app.operators.geometric.scale_image import ScaleImage
from app.operators.sobel_derivatives.scharr_derivative import ScharrDerivative
from app.operators.sobel_derivatives.sobel_derivative import SobelDerivative
from app.operators.thresholding.adaptive_threshold import AdaptiveThreshold
from app.operators.thresholding.otsu_threshold import OtsuThreshold
from app.operators.thresholding.apply_borders import ApplyBorders
from app.operators.thresholding.apply_threshold import ApplyThreshold
from app.operators.transformation.distance_transform import DistanceTransform
from app.operators.transformation.laplacian import Laplacian

OPERATOR_REGISTRY: dict[str, type[BaseOperator]] = {
    # Basic
    "basic_readimage": ReadImage,
    "basic_writeimage": WriteImage,
    # Geometric
    "geometric_reflectimage": ReflectImage,
    "geometric_rotateimage": RotateImage,
    "geometric_scaleimage": ScaleImage,
    "geometric_affineimage": AffineImage,
    # Conversions
    "imageconvertions_grayimage": GrayImage,
    "imageconvertions_graytobinary": GrayToBinary,
    "imageconvertions_colormaps": ColorMaps,
    "imageconvertions_colortobinary": ColorToBinary,
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
    "filtering_pyramidup": PyramidUp,
    "filtering_pyramiddown": PyramidDown,
    "filtering_erosion": Erosion,
    "filtering_dilation": Dilation,
    "filtering_morphological": Morphological,
    # Thresholding
    "thresholding_applythreshold": ApplyThreshold,
    "thresholding_adaptivethreshold": AdaptiveThreshold,
    "thresholding_applyborders": ApplyBorders,
    "thresholding_otsuthreshold": OtsuThreshold,
    # Sobel Derivatives
    "sobelderivatives_soblederivate": SobelDerivative,
    "sobelderivatives_scharrderivate": ScharrDerivative,
    # Transformation
    "transformation_distance": DistanceTransform,
    "transformation_laplacian": Laplacian,
}


def get_operator(block_type: str) -> type[BaseOperator] | None:
    return OPERATOR_REGISTRY.get(block_type)