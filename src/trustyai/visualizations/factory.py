"""Visualizations.factory module"""
# pylint: disable=protected-access, missing-final-newline
from bokeh.io import show

from trustyai.explainers import (
    SHAPResults,
    LimeResults,
    pdp
)
from .visualization_results import VisualizationResults
from .shap import SHAPViz
from .lime import LimeViz
from .pdp import PDPViz


def get_viz(explanations) -> VisualizationResults:
    """
    Get visualization according to the explanation method
    """
    if isinstance(explanations, SHAPResults):
        return SHAPViz()
    if isinstance(explanations, LimeResults):
        return LimeViz()
    if isinstance(explanations, pdp.PDPResults):
        return PDPViz()
    else:
        raise ValueError("Explanation method unknown")

def plot(
        explanations, output_name=None, render_bokeh=False, block=True, call_show=True
    ) -> None:
    """
    Plot the found feature saliencies.

        Parameters
        ----------
        output_name : str
            (default= `None`) The name of the output to be explainer. If `None`, all outputs will
            be displayed
        render_bokeh : bool
            (default= `False`) If true, render plot in bokeh, otherwise use matplotlib.
        block: bool
            (default= `True`) Whether displaying the plot blocks subsequent code execution
        call_show: bool
            (default= 'True') Whether plt.show() will be called by default at the end of the
            plotting function. If `False`, the plot will be returned to the user for further
            editing.
        """
    viz = get_viz(explanations)

    if isinstance(explanations, pdp.PDPResults):
        viz.plot(explanations, output_name)
    elif output_name is None:
        for output_name_iterator in explanations.saliency_map().keys():
            if render_bokeh:
                show(viz._get_bokeh_plot(explanations, output_name_iterator))
            else:
                viz._matplotlib_plot(explanations, output_name_iterator, block, call_show)
    else:
        if render_bokeh:
            show(viz._get_bokeh_plot(explanations, output_name))
        else:
            viz._matplotlib_plot(explanations, output_name, block, call_show)