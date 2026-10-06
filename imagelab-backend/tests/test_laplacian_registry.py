from app.operators.filtering.laplacian import Laplacian as FilteringLaplacian
from app.operators.registry import get_operator
from app.operators.transformation.laplacian import Laplacian as TransformationLaplacian


def test_transformation_laplacian_maps_to_transformation_class():
    assert get_operator("transformation_laplacian") is TransformationLaplacian


def test_filtering_laplacian_maps_to_filtering_class():
    assert get_operator("laplacian") is FilteringLaplacian
