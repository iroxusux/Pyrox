from pyrox.models import eplan, plc


class BaseEplanProject(eplan.project.EplanProject):
    """Base class for Eplan project generation logic."""
    supporting_class = plc.Controller
