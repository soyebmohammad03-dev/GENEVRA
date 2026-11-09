"""Load the experiment scripts shared by the checkout and installed CLI."""

from importlib import resources, util
from types import ModuleType

from genevra.utils.provenance import source_checkout

_SCRIPTS = {"baseline.py", "exp1_isolated_vs_shared.py", "exp_ecology_corrected.py"}


def load_experiment_script(filename: str) -> ModuleType:
    """Load a named runtime experiment from the wheel or an editable checkout."""
    if filename not in _SCRIPTS:
        raise ValueError(f"unknown runtime experiment: {filename}")
    script = resources.files("genevra.experiments").joinpath("_scripts", filename)
    if not script.is_file():
        root = source_checkout()
        if root is not None:
            script = root / "experiments" / filename
    if not script.is_file():
        raise RuntimeError(f"missing GENEVRA runtime resource {filename}; reinstall GENEVRA")
    with resources.as_file(script) as path:
        spec = util.spec_from_file_location(f"genevra_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load GENEVRA runtime resource {filename}")
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module
