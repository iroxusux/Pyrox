"""Matcher for Ford controllers."""
from pyrox.models import plc
from .ford import FordController


class FordControllerMatcher(plc.ControllerMatcher):
    """Matcher for GM controllers.
    """

    @classmethod
    def get_controller_constructor(cls):
        return FordController

    @staticmethod
    def get_datatype_patterns() -> list[str]:
        return [
            'Fudc_*',
            'Fudf_*',
            'Fudh_*',
            'Fuds_*',
            'Fudm_*',
        ]

    @staticmethod
    def get_module_patterns() -> list[str]:
        return [
            'HMI1KS1',
            'HMI1KS2',
        ]

    @staticmethod
    def get_program_patterns() -> list[str]:
        return [
            'NETWORK_DIAG',
            'HMI_COMN',
            'CONV_FIS',
            'HMI1_SCREENDRIVER',
        ]

    @staticmethod
    def get_safety_program_patterns() -> list[str]:
        return [
            '*_MAPPINGINPUTS_EDIT',
            '*_MAPPINGOUTPUTS_EDIT',
            '*_COMMONSAFETY_EDIT',
        ]

    @staticmethod
    def get_tag_patterns() -> list[str]:
        return [
            'FB1',
            'MB1',
            'WB1',
            'ZeroRef',
            'ZeroRefSafety'
        ]
