# pylint: disable = import-error, invalid-name, wrong-import-order, no-name-in-module
"""General model classes"""
from trustyai import _default_initializer  # pylint: disable=unused-import
from org.kie.trustyai.explainability.metrics import (
    ExplainabilityMetrics as _ExplainabilityMetrics,
)

ExplainabilityMetrics = _ExplainabilityMetrics
