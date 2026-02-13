# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
import plotly.graph_objects as go
import plotly.io as pio
from cl.runtime.ui.control.html_control import HtmlControl
from cl.runtime.ui.ui_app_state import UiAppState


@dataclass(slots=True, kw_only=True, eq=False)
class PlotlyControl(HtmlControl):
    """
    Specialized HtmlControl for embedding Plotly-generated plots.
    Content must be provided in the same HTML format expected by HtmlControl.
    """

    @classmethod
    def encode_plot(cls, plot: go.Figure, use_app_theme: bool = True) -> bytes:
        """Encode Plotly Figure as HTML content."""
        if use_app_theme:
            app_theme = UiAppState.get_current_user_app_theme()
            pio.templates.default = "plotly_dark" if app_theme == "Dark" else "plotly_white"

        fig_content = pio.to_html(plot, full_html=False, include_plotlyjs="cdn")
        return fig_content.encode("utf-8")

    def get_control_type(self) -> str:
        return PlotlyControl.__name__
