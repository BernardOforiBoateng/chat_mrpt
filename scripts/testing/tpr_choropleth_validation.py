#!/usr/bin/env python3
"""Batch-generate TPR choropleth maps for pretest states.

This script exercises the ``TPRVisualizationService`` directly so we can
verify that every pretest state produces a filled choropleth (rather than an
empty basemap) after the Plotly serialization fix.  It aggregates ward-level
TPR from the cleaned facility records, writes the map HTML to the normal
``instance/uploads`` tree, then inspects the serialized Plotly payload to
confirm we have non-null ``z`` values.

Usage
-----
Run from the project root:

```
python3 scripts/testing/tpr_choropleth_validation.py
```

The script prints a compact summary table at the end and exits with status 1
if any state fails so it can be wired into smoke checks.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import importlib.util
import types

# Discover project root (directory containing the ``app`` package).
_current = Path(__file__).resolve().parent
while _current != _current.parent:
    if (_current / "app").exists():
        ROOT_DIR = _current
        break
    _current = _current.parent
else:
    raise RuntimeError("Unable to locate project root containing 'app' directory")

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd


def load_visualization_service():
    """Import ``TPRVisualizationService`` without triggering the full package."""

    services_path = ROOT_DIR / "app/tpr_module/services"
    tpr_module_path = ROOT_DIR / "app/tpr_module"
    app_path = ROOT_DIR / "app"

    # Create package placeholders for app and app.tpr_module so relative
    # imports inside the visualization module resolve correctly.
    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = [str(app_path)]
    sys.modules.setdefault("app", app_pkg)

    tpr_pkg = types.ModuleType("app.tpr_module")
    tpr_pkg.__path__ = [str(tpr_module_path)]
    sys.modules.setdefault("app.tpr_module", tpr_pkg)

    # Load shapefile extractor first so the relative import succeeds.
    shapefile_spec = importlib.util.spec_from_file_location(
        "app.tpr_module.services.shapefile_extractor",
        services_path / "shapefile_extractor.py",
    )
    shapefile_module = importlib.util.module_from_spec(shapefile_spec)
    shapefile_spec.loader.exec_module(shapefile_module)
    sys.modules["app.tpr_module.services.shapefile_extractor"] = shapefile_module

    services_pkg = types.ModuleType("app.tpr_module.services")
    services_pkg.__path__ = [str(services_path)]
    sys.modules.setdefault("app.tpr_module.services", services_pkg)
    sys.modules.setdefault("app.tpr_module.services.services", services_pkg)

    spec = importlib.util.spec_from_file_location(
        "app.tpr_module.services.tpr_visualization_service",
        services_path / "tpr_visualization_service.py",
        submodule_search_locations=[str(services_path)],
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TPRVisualizationService


TPRVisualizationService = load_visualization_service()


PRETEST_STATES: Dict[str, str] = {
    "Bauchi": "bauchi_tpr_cleaned.csv",
    "Benue": "benue_tpr_cleaned.csv",
    "Zamfara": "zamfara_tpr_cleaned.csv",
    "Sokoto": "sokoto_tpr_cleaned.csv",
    "Kebbi": "kebbi_tpr_cleaned.csv",
    "Akwa Ibom": "akwa_ibom_tpr_cleaned.csv",
    "Cross River": "cross_river_tpr_cleaned.csv",
    "Ebonyi": "ebonyi_tpr_cleaned.csv",
    "Plateau": "plateau_tpr_cleaned.csv",
    "Nasarawa": "nasarawa_tpr_cleaned.csv",
}

DATA_ROOT = ROOT_DIR / "www/all_states_cleaned"
PLOT_SPEC_REGEX = re.compile(r"const plotSpec = (\{.*?\});", re.DOTALL)


@dataclass
class StateResult:
    """Holds validation metrics for a single state run."""

    state: str
    ward_total: int = 0
    ward_with_data: int = 0
    z_min: float | None = None
    z_max: float | None = None
    html_path: Path | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None and self.ward_with_data > 0


def _load_state_frame(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Missing input file: {file_path}")

    df = pd.read_csv(file_path)

    if "WardName" not in df.columns:
        raise ValueError(f"Expected 'WardName' column in {file_path}")

    return df


def _aggregate_ward_tpr(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols: List[str] = []
    for col in df.columns:
        col_lower = col.lower()
        if "tested" in col_lower or "positive" in col_lower:
            numeric_cols.append(col)

    as_numeric = df.copy()
    for col in numeric_cols:
        as_numeric[col] = pd.to_numeric(as_numeric[col], errors="coerce")

    ward_group = as_numeric.groupby("WardName", dropna=True)

    tested_cols = [col for col in numeric_cols if "tested" in col.lower() and "positive" not in col.lower()]
    positive_cols = [col for col in numeric_cols if "positive" in col.lower()]

    if not tested_cols or not positive_cols:
        raise ValueError("Could not identify tested/positive columns for aggregation")

    aggregated = ward_group.agg({col: "sum" for col in tested_cols + positive_cols})

    aggregated = aggregated.rename_axis("WardName").reset_index()

    aggregated["Tested"] = aggregated[tested_cols].sum(axis=1, skipna=True)
    aggregated["Positive"] = aggregated[positive_cols].sum(axis=1, skipna=True)

    # Avoid divide-by-zero warnings.
    aggregated["TPR"] = np.where(
        aggregated["Tested"] > 0,
        (aggregated["Positive"] / aggregated["Tested"]) * 100.0,
        np.nan,
    )

    aggregated["DataCompleteness"] = 100.0

    selection = aggregated[["WardName", "TPR", "Tested", "Positive", "DataCompleteness"]]
    return selection.dropna(subset=["TPR"])


def _extract_z_values(html_path: Path) -> List[float | None]:
    html_text = html_path.read_text(encoding="utf-8")
    match = PLOT_SPEC_REGEX.search(html_text)
    if not match:
        raise ValueError(f"Could not locate plotSpec JSON in {html_path}")

    plot_spec = json.loads(match.group(1))
    data = plot_spec.get("data", [])
    if not data:
        raise ValueError("Plot spec contains no data traces")

    z_values = data[0].get("z")
    if z_values is None:
        raise ValueError("Missing 'z' array in plot spec")

    return z_values


def validate_state(state: str, filename: str) -> StateResult:
    result = StateResult(state=state)

    try:
        source_path = DATA_ROOT / filename
        ward_frame = _load_state_frame(source_path)

        aggregated = _aggregate_ward_tpr(ward_frame)
        result.ward_total = len(aggregated)

        if aggregated.empty:
            raise ValueError("No ward-level TPR values after aggregation")

        session_id = f"tpr-map-check-{state.lower().replace(' ', '-')}"
        service = TPRVisualizationService(session_id=session_id)
        viz_url = service.create_tpr_distribution_map(aggregated, state_name=state)

        html_filename = viz_url.rsplit("/", 1)[-1]
        html_path = Path("instance/uploads") / session_id / "visualizations" / html_filename
        if not html_path.exists():
            raise FileNotFoundError(f"Expected visualization at {html_path}")

        result.html_path = html_path

        z_values = _extract_z_values(html_path)
        numeric_values = [value for value in z_values if value is not None]

        result.ward_with_data = len(numeric_values)
        if numeric_values:
            result.z_min = float(min(numeric_values))
            result.z_max = float(max(numeric_values))
        else:
            raise ValueError("All z values are null")

    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)

    return result


def main() -> int:
    results: List[StateResult] = []
    for state, filename in PRETEST_STATES.items():
        print(f"→ Generating map for {state}…", end=" ")
        res = validate_state(state, filename)
        if res.success:
            print("ok")
        else:
            print("FAILED")
        results.append(res)

    print("\nState map validation:")
    print("State           | Wards | With Data | Min TPR | Max TPR | Status")
    print("-" * 70)
    for res in results:
        status = "OK" if res.success else f"FAIL ({res.error})"
        print(
            f"{res.state:<15}|"
            f" {res.ward_total:5d} |"
            f" {res.ward_with_data:9d} |"
            f" {res.z_min if res.z_min is not None else float('nan'):7.2f} |"
            f" {res.z_max if res.z_max is not None else float('nan'):7.2f} |"
            f" {status}"
        )

    failures = [res for res in results if not res.success]
    if failures:
        print("\n❌ Map generation failed for:")
        for res in failures:
            print(f" - {res.state}: {res.error}")
        return 1

    print("\n✅ All pretest states produced choropleth data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
