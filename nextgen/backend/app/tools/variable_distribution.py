"""Variable Distribution Visualization Tool for NextGen"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Optional
from uuid import uuid4

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from pydantic import BaseModel, Field
from shapely.geometry import mapping

from ..services.column_store import ColumnStore
from ..services.dataset_registry import DatasetRegistry, DatasetEntry
from ..services.plot_service import PlotService

logger = logging.getLogger(__name__)


class VariableDistributionParams(BaseModel):
    """Parameters for variable distribution visualization."""

    dataset_id: str = Field(..., description="Dataset ID to visualize")
    variable_name: str = Field(..., description="Variable/column name to map")
    level: str = Field("ward", description="Administrative level: ward, lga, or state")
    color_scale: str = Field("Viridis", description="Plotly color scale (Viridis, Reds, Blues, etc.)")


@dataclass
class VariableDistributionResult:
    """Result from variable distribution tool execution."""

    plot_id: str
    title: str
    variable: str
    resolved_variable: str
    level: str
    stats: dict
    figure: dict


class VariableDistributionTool:
    """
    Create spatial distribution maps for any variable from the dataset.

    This tool maps existing data columns (like TPR, rainfall, elevation, housing_quality)
    onto geographic boundaries. Supports ward, LGA, and state-level visualization with
    intelligent fuzzy matching for variable names.
    """

    def __init__(
        self,
        column_store: ColumnStore,
        dataset_registry: DatasetRegistry,
        plot_service: PlotService,
    ) -> None:
        self.column_store = column_store
        self.datasets = dataset_registry
        self.plot_service = plot_service

    def execute(self, session_id: str, params: VariableDistributionParams) -> dict:
        """
        Execute variable distribution visualization.

        Args:
            session_id: Current session ID
            params: Visualization parameters

        Returns:
            dict with plot_id, title, variable info, and figure

        Raises:
            ValueError: If dataset not found, variable not found, or shapefile missing
        """
        try:
            # Get dataset entry
            entry = self.datasets.get_for_session(params.dataset_id, session_id)
            if not entry:
                raise ValueError(f"Dataset {params.dataset_id} not found for session")

            # Load data
            df = self._load_dataset(entry)

            # Fuzzy match variable name
            resolved_var = self._fuzzy_match_column(params.variable_name, df.columns.tolist())
            if not resolved_var:
                suggestions = get_close_matches(params.variable_name, df.columns.tolist(), n=5, cutoff=0.4)
                suggestion_text = f"\n\nDid you mean: {', '.join(suggestions)}" if suggestions else ""
                raise ValueError(
                    f"Variable '{params.variable_name}' not found in dataset.{suggestion_text}\n\n"
                    f"Available columns: {', '.join(df.columns.tolist()[:20])}"
                )

            # Load shapefile for geographic boundaries
            gdf = self._load_shapefile(entry, params.level)
            if gdf is None:
                raise ValueError(
                    f"Shapefile required for spatial visualization. "
                    f"Please ensure shapefile was uploaded with the dataset."
                )

            # Merge data with geography
            merged = self._merge_data(gdf, df, params.level)
            if merged.empty:
                raise ValueError(f"No data could be matched with geographic boundaries at {params.level} level")

            # Create choropleth map
            fig = self._create_choropleth(merged, resolved_var, params.color_scale, params.level)

            # Generate statistics
            stats = self._generate_statistics(df, resolved_var)

            # Save plot
            title = f"{resolved_var.upper()} Distribution at {params.level.upper()} Level"
            plot_id = self.plot_service.save_plot(
                session_id=session_id,
                dataset_id=params.dataset_id,
                plot_function="variable_distribution",
                title=title,
                figure=fig,
            )

            logger.info(
                "Variable distribution created: session=%s, variable=%s, level=%s, plot_id=%s",
                session_id,
                resolved_var,
                params.level,
                plot_id
            )

            return {
                "type": "plot",
                "plot_id": plot_id,
                "title": title,
                "variable": params.variable_name,
                "resolved_variable": resolved_var,
                "level": params.level,
                "stats": stats,
                "figure": fig,
            }

        except Exception as exc:
            logger.error(
                "Variable distribution failed: session=%s, variable=%s, error=%s",
                session_id,
                params.variable_name,
                exc
            )
            raise ValueError(f"Failed to create variable distribution: {exc}") from exc

    def _load_dataset(self, entry: DatasetEntry) -> pd.DataFrame:
        """Load dataset from parquet or CSV."""
        derived = entry.metadata.get("derived_assets", {})
        parquet_path = derived.get("parquet")

        if parquet_path and Path(parquet_path).exists():
            return pd.read_parquet(parquet_path)

        # Fallback to CSV
        return pd.read_csv(entry.path)

    def _fuzzy_match_column(self, target: str, columns: list[str]) -> Optional[str]:
        """
        Fuzzy match column name with intelligent matching.

        Args:
            target: User-provided column name
            columns: Available columns in dataset

        Returns:
            Best matching column name or None
        """
        # Exact match (case-insensitive)
        target_lower = target.lower()
        for col in columns:
            if col.lower() == target_lower:
                return col

        # Fuzzy match using difflib
        matches = get_close_matches(target, columns, n=1, cutoff=0.7)
        if matches:
            logger.info(f"Fuzzy matched '{target}' -> '{matches[0]}'")
            return matches[0]

        return None

    def _load_shapefile(self, entry: DatasetEntry, level: str) -> Optional[gpd.GeoDataFrame]:
        """
        Load shapefile for the specified administrative level.

        Args:
            entry: Dataset entry
            level: Administrative level (ward, lga, state)

        Returns:
            GeoDataFrame or None if shapefile not available
        """
        # Check for shapefile in derived assets
        derived = entry.metadata.get("derived_assets", {})
        shapefile_zip = derived.get("shapefile_zip")

        if not shapefile_zip or not Path(shapefile_zip).exists():
            logger.warning(f"No shapefile found for dataset {entry.dataset_id}")
            return None

        try:
            # Extract and load shapefile
            import tempfile
            import zipfile

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(shapefile_zip, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)

                # Find .shp file
                shp_files = list(Path(tmpdir).glob("**/*.shp"))
                if not shp_files:
                    logger.error(f"No .shp file found in {shapefile_zip}")
                    return None

                gdf = gpd.read_file(shp_files[0])
                logger.info(f"Loaded shapefile: {len(gdf)} features, CRS: {gdf.crs}")

                # Ensure WGS84 for Plotly
                if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")

                return gdf

        except Exception as exc:
            logger.error(f"Failed to load shapefile: {exc}")
            return None

    def _merge_data(self, gdf: gpd.GeoDataFrame, df: pd.DataFrame, level: str) -> gpd.GeoDataFrame:
        """
        Merge tabular data with geographic boundaries.

        Args:
            gdf: GeoDataFrame with boundaries
            df: Tabular data
            level: Administrative level

        Returns:
            Merged GeoDataFrame
        """
        # Try multiple join strategies
        join_attempts = [
            # Ward level
            ("WardCode", "WardCode"),
            ("WardName", "WardName"),
            ("ward_code", "ward_code"),
            ("ward_name", "ward_name"),
            # LGA level
            ("LGACode", "LGACode"),
            ("LGAName", "LGAName"),
            ("lga_code", "lga_code"),
            ("lga_name", "lga_name"),
            # State level
            ("StateCode", "StateCode"),
            ("StateName", "StateName"),
            ("state_code", "state_code"),
            ("state_name", "state_name"),
        ]

        for left_col, right_col in join_attempts:
            if left_col in gdf.columns and right_col in df.columns:
                merged = gdf.merge(df, left_on=left_col, right_on=right_col, how="left")
                logger.info(f"Merged on {left_col} = {right_col}: {len(merged)} records")
                return merged

        # Fallback: try index merge
        logger.warning("No common columns found, attempting index merge")
        return gdf.merge(df, left_index=True, right_index=True, how="left")

    def _create_choropleth(
        self,
        gdf: gpd.GeoDataFrame,
        variable: str,
        color_scale: str,
        level: str
    ) -> dict:
        """
        Create Plotly choropleth map.

        Args:
            gdf: GeoDataFrame with data and geometry
            variable: Variable to visualize
            color_scale: Plotly color scale
            level: Administrative level

        Returns:
            Plotly figure as dict
        """
        # Filter valid data
        clean = gdf.dropna(subset=[variable])
        clean = clean[clean.geometry.notnull() & ~clean.geometry.is_empty]

        if clean.empty:
            raise ValueError(f"No valid data for variable '{variable}'")

        # Auto-select color scale based on variable type
        if variable.lower() in ['pfpr', 'tpr', 'u5_tpr_rdt', 'test_positivity']:
            color_scale = 'Reds'
        elif any(kw in variable.lower() for kw in ['rainfall', 'ndvi', 'vegetation']):
            color_scale = 'Blues'

        # Build GeoJSON
        features = []
        for idx, row in clean.iterrows():
            try:
                features.append({
                    'type': 'Feature',
                    'id': str(idx),
                    'geometry': mapping(row.geometry),
                    'properties': {}
                })
            except Exception as exc:
                logger.warning(f"Skipping invalid geometry at index {idx}: {exc}")
                continue

        if not features:
            raise ValueError("No valid geometries to display")

        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }

        # Get label column
        label_col = self._get_label_column(clean, level)
        labels = clean.get(label_col, clean.index).astype(str)

        # Create figure
        fig = go.Figure()

        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson,
            locations=clean.index.astype(str),
            z=clean[variable],
            colorscale=color_scale,
            text=labels,
            hovertemplate=f'<b>%{{text}}</b><br>{variable}: %{{z:.2f}}<extra></extra>',
            marker_opacity=0.7,
            marker_line_width=1,
            marker_line_color='white',
            showscale=True,
            colorbar=dict(
                title=variable.replace('_', ' ').title(),
                thickness=15,
                len=0.7
            )
        ))

        # Calculate center
        bounds = clean.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        # Update layout
        fig.update_layout(
            title={
                'text': f'{variable.upper()} - {level.upper()} Level Distribution',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#2E3440'}
            },
            mapbox=dict(
                style='open-street-map',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=8
            ),
            height=600,
            margin=dict(t=60, b=20, l=20, r=20),
            template='plotly_white'
        )

        return fig.to_dict()

    def _get_label_column(self, gdf: gpd.GeoDataFrame, level: str) -> str:
        """Get appropriate label column for administrative level."""
        if level == "ward":
            for col in ["WardName", "ward_name", "WardCode", "ward_code"]:
                if col in gdf.columns:
                    return col
        elif level == "lga":
            for col in ["LGAName", "lga_name", "LGACode", "lga_code"]:
                if col in gdf.columns:
                    return col
        elif level == "state":
            for col in ["StateName", "state_name", "StateCode", "state_code"]:
                if col in gdf.columns:
                    return col

        return "index"

    def _generate_statistics(self, df: pd.DataFrame, variable: str) -> dict:
        """Generate summary statistics for the variable."""
        series = df[variable].dropna()

        if series.empty:
            return {}

        return {
            "count": int(series.count()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "q25": float(series.quantile(0.25)),
            "q75": float(series.quantile(0.75)),
        }
