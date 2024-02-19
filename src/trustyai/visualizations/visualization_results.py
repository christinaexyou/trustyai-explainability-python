# pylint: disable = too-few-public-methods, line-too-long
"""Generic class for Visualization results"""
from abc import ABC, abstractmethod
from typing import Dict

import bokeh.models


class VisualizationResults(ABC):
    """Abstract class for visualization results"""
    @abstractmethod
    def _matplotlib_plot(self, explanations, output_name: str, block: bool, call_show: bool) -> None:
        """Plot the saliencies of a particular output in matplotlib"""

    @abstractmethod
    def _get_bokeh_plot(self, explanations, output_name: str) -> bokeh.models.Plot:
        """Get a bokeh plot visualizing the saliencies of a particular output"""

    @abstractmethod
    def _get_bokeh_plot_dict(self, explanations, output_name) -> Dict[str, bokeh.models.Plot]:
        """Get a dictionary containing visualizations of the saliencies of all outputs,
        keyed by output name"""
        return {
            output_name: self._get_bokeh_plot(explanations, output_name)
            for output_name in explanations.saliency_map().keys()
        }
