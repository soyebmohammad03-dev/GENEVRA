# Research notebooks

[When more calibration stops helping](certification_evidence.ipynb) reads verified
Phase 11–19 outputs. It compares within-phase precision, distinguishes false
certificates from threshold calls, and derives the identification width floor.
Reusable algorithms remain in the simulator and experiment modules.

Complete the [archive replay](../docs/research/README.md) first. From the repository root:

```sh
uv pip install --python .venv-replay/bin/python nbclient==0.10.2 ipykernel==6.30.1
export GENEVRA_REPLAY=/tmp/genevra-replay
export GENEVRA_NOTEBOOK_FIGURES=/tmp
.venv-replay/bin/python - <<'PY'
import nbformat
from nbclient import NotebookClient

book = nbformat.read("notebooks/certification_evidence.ipynb", as_version=4)
nbformat.validate(book)
nbformat.write(
    NotebookClient(book, timeout=60, kernel_name="python3").execute(),
    "/tmp/genevra-certification-executed.ipynb",
)
PY
```

The committed [identification-floor figure](../docs/research/identification_floor.png)
comes from the notebook sensitivity cell. Its inputs are the frozen extension's
conditional score span and precision target. The panel is algebraic sensitivity,
not newly sampled data. Other panels and tables are generated in the executed
notebook from the archive CSV and JSON outputs.
