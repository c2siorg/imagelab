from app.models.pipeline import PipelineExportRequest, PipelineStep
from app.services.pipeline_python_exporter import export_pipeline_to_python


def test_export_pipeline_to_python_includes_imports_and_steps():
    request = PipelineExportRequest(
        pipeline=[
            PipelineStep(type="basic_readimage"),
            PipelineStep(type="imageconvertions_grayimage"),
            PipelineStep(type="filtering_gaborfilter", params={"lambda_": 2.0, "sigma": 5.0}),
            PipelineStep(type="basic_writeimage"),
        ],
        input_path="samples/input.png",
        output_path="samples/output.png",
    )

    script = export_pipeline_to_python(request)

    assert "import cv2" in script
    assert "import numpy as np" in script
    assert "from app.operators.registry import get_operator" in script
    assert "DEFAULT_INPUT_PATH = 'samples/input.png'" in script
    assert "DEFAULT_OUTPUT_PATH = 'samples/output.png'" in script
    assert "# 2. GrayImage" in script
    assert "# 3. GaborFilter" in script
    assert "'lambda_': 2.0" in script
    assert "Saved processed image to" in script


def test_export_pipeline_to_python_rejects_unknown_operator():
    request = PipelineExportRequest(pipeline=[PipelineStep(type="not_a_real_operator")])

    try:
        export_pipeline_to_python(request)
    except ValueError as exc:
        assert str(exc) == "Unknown operator 'not_a_real_operator' at step 1"
    else:
        raise AssertionError("Expected exporter to reject unknown operators")
