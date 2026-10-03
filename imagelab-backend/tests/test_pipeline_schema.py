from app.models.pipeline import PipelineRequest
from app.operators.registry import OPERATOR_REGISTRY


def test_openapi_example_is_valid():
    example = PipelineRequest.model_config["json_schema_extra"]["examples"][0]
    PipelineRequest.model_validate(example)
    for step in example["pipeline"]:
        assert step["type"] in OPERATOR_REGISTRY
