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

import io
from dataclasses import dataclass
import matplotlib
from matplotlib import pyplot as plt
from cl.runtime.plots.matplotlib_util import MatplotlibUtil
from cl.runtime.plots.plot import Plot
from cl.runtime.plots.plot_line_style import PlotLineStyle
from cl.runtime.plots.plot_surface_style import PlotSurfaceStyle
from cl.runtime.plots.scatter_values_3d import ScatterValues3D
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.views.png_view import PngView

matplotlib.use("Agg")


@dataclass(slots=True, kw_only=True)
class ScatterPlot3D(Plot):
    """3D scatter plot with markers and surfaces."""

    data: list[ScatterValues3D] = required()
    """List of values objects, each containing data and style settings."""

    x_label: str | None = None
    """X-axis label."""

    y_label: str | None = None
    """Y-axis label."""

    z_label: str | None = None
    """Z-axis label."""

    x_lim: tuple[float, ...] | None = None
    """Y-axis limits (optional)."""

    y_lim: tuple[float, ...] | None = None
    """Y-axis limits (optional)."""

    z_lim: tuple[float, ...] | None = None
    """Y-axis limits (optional)."""

    def get_view(self) -> PngView:
        """Return a PNG view of the 3D scatter plot."""
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        for values in self.data:
            if values.surface_style == PlotSurfaceStyle.SOLID:
                ax.plot_trisurf(values.x, values.y, values.z, alpha=0.8, label=values.legend)
            elif values.line_style == PlotLineStyle.SOLID:
                ax.plot(values.x, values.y, values.z, label=values.legend, linewidth=0.5)
            else:
                ax.scatter(values.x, values.y, values.z, label=values.legend)
        if self.x_label:
            ax.set_xlabel(self.x_label)
        if self.y_label:
            ax.set_ylabel(self.y_label)
        if self.z_label:
            ax.set_zlabel(self.z_label)
        if self.x_lim:
            ax.set_xlim(self.x_lim)
        if self.y_lim:
            ax.set_ylim(self.y_lim)
        if self.z_lim:
            ax.set_zlim(self.z_lim)
        ax.legend()
        png_buffer = io.BytesIO()
        fig.savefig(
            png_buffer, format="png", transparent=False, metadata=MatplotlibUtil.no_png_metadata(),
            dpi=100, bbox_inches="tight", pad_inches=0.1,
        )
        plt.close(fig)
        return PngView(png_bytes=png_buffer.getvalue())
