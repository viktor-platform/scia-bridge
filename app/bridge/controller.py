"""Copyright (c) 2022 VIKTOR B.V.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

VIKTOR B.V. PROVIDES THIS SOFTWARE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from io import BytesIO
from pathlib import Path

from viktor.core import ViktorController
from viktor.external.scia import Model as SciaModel
from viktor.external.scia import ResultType
from viktor.external.scia import SciaAnalysis
from viktor.result import DownloadResult
from viktor.views import GeometryResult
from viktor.views import GeometryView
from viktor.views import PDFResult
from viktor.views import PDFView

from . import scia_model_helper
from . import visualization_helper
from .parametrization import BridgeParametrization


class BridgeController(ViktorController):
    """Controller class which acts as interface for the Sample entity type."""
    label = "Bridge"
    parametrization = BridgeParametrization
    viktor_convert_entity_field = True

    @GeometryView("3D", duration_guess=1)
    def visualize_bridge_layout(self, params, **kwargs):
        """"create a visualization of the bridge"""
        geometry_group_bridge = visualization_helper.create_visualization_bridge_layout(params)
        return GeometryResult(geometry_group_bridge)

    @GeometryView("3D", duration_guess=1)
    def visualize_bridge_foundations(self, params, **kwargs):
        """"create a visualization of a bridge foundations"""
        scia_bridge_model = scia_model_helper.create_scia_model(params)
        geometry_group_bridge_foundations = visualization_helper.create_visualization_bridge_foundations(
            params, scia_bridge_model, opacity=0.5)
        geometry_group_bridge_layout = visualization_helper.create_visualization_bridge_layout(params, opacity=0.1)
        for obj in geometry_group_bridge_layout.children:
            geometry_group_bridge_foundations.add(obj)
        return GeometryResult(geometry_group_bridge_foundations)

    @PDFView("PDF View", duration_guess=20)
    def execute_scia_analysis(self, params, **kwargs):
        """ Perform an analysis using SCIA on a third-party worker and generate engineering report."""
        scia_model = scia_model_helper.create_scia_model(params)
        input_file, xml_def_file = scia_model.generate_xml_input()
        scia_model_esa = self.get_scia_input_esa()

        scia_analysis = SciaAnalysis(input_file=input_file, xml_def_file=xml_def_file, scia_model=scia_model_esa,
                                     result_type=ResultType.ENGINEERING_REPORT, output_document='Report_1')
        scia_analysis.execute(timeout=600)
        engineering_report = scia_analysis.get_engineering_report(as_file=True)

        return PDFResult(file=engineering_report)

    def download_scia_input_esa(self, params, **kwargs):
        """"Download scia input esa file"""
        scia_input_esa = self.get_scia_input_esa()
        filename = "model.esa"
        return DownloadResult(scia_input_esa, filename)

    def download_scia_input_xml(self, params, **kwargs):
        """"Download scia input xml file"""
        scia_model = scia_model_helper.create_scia_model(params)
        input_xml, _ = scia_model.generate_xml_input()
        return DownloadResult(input_xml, 'viktor.xml')

    def download_scia_input_def(self, params, **kwargs):
        """"Download scia input def file."""
        scia_model = SciaModel()
        _, input_def = scia_model.generate_xml_input()
        return DownloadResult(input_def, 'viktor.xml.def')

    def get_scia_input_esa(self) -> BytesIO:
        """Retrieves the model.esa file."""
        esa_path = Path(__file__).parent / 'scia' / 'model.esa'
        scia_input_esa = BytesIO()
        with open(esa_path, "rb") as esa_file:
            scia_input_esa.write(esa_file.read())
        return scia_input_esa
