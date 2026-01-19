"""ITN Allocation Map Tool for NextGen - Bed Net Distribution Visualization"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from pydantic import BaseModel, Field
from shapely.geometry import mapping

from ..services.column_store import ColumnStore
from ..services.dataset_registry import DatasetRegistry, DatasetEntry
from ..services.plot_service import PlotService

logger = logging.getLogger(__name__)


class ITNAllocationMapParams(BaseModel):
    """Parameters for ITN allocation map visualization."""

    dataset_id: str = Field(..., description="Dataset ID with ITN allocation results")
    level: str = Field("ward", description="Administrative level: ward, lga, or state")


@dataclass
class ITNAllocationMapResult:
    """Result from ITN allocation map tool execution."""

    plot_id: str
    title: str
    level: str
    total_nets: int
    total_wards: int
    figure: dict


class ITNAllocationMapTool:
    """
    Create ITN (bed net) allocation visualization maps.

    This tool creates choropleth maps showing how insecticide-treated nets
    are allocated across wards based on vulnerability rankings and population.
    Requires that ITN planning has been completed first.
    Supports ward, LGA, and state-level visualization.
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

    def execute(self, session_id: str, params: ITNAllocationMapParams) -> dict:
        """
        Execute ITN allocation map visualization.

        Args:
            session_id: Current session ID
            params: Visualization parameters

        Returns:
            dict with plot_id, title, allocation info, and figure

        Raises:
            ValueError: If dataset not found, ITN results missing, or shapefile missing
        """
        try:
            # Get dataset entry
            entry = self.datasets.get_for_session(params.dataset_id, session_id)
            if not entry:
                raise ValueError(f"Dataset {params.dataset_id} not found for session")

            # Load data
            df = self._load_dataset(entry)

            # Check for ITN allocation columns
            nets_col = self._find_nets_column(df)
            if not nets_col:
                raise ValueError(
                    "ITN allocation data not found. "
                    "Please run ITN planning first to allocate bed nets."
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

            # Calculate statistics
            total_nets = int(merged[nets_col].sum())
            total_wards = len(merged[merged[nets_col] > 0])

            # Create ITN allocation map
            fig = self._create_itn_map(merged, nets_col, params.level)

            # Save plot
            title = f"ITN Allocation Map - {params.level.upper()} Level"
            plot_id = self.plot_service.save_plot(
                session_id=session_id,
                dataset_id=params.dataset_id,
                plot_function="itn_allocation_map",
                title=title,
                figure=fig,
            )

            logger.info(
                "ITN allocation map created: session=%s, level=%s, total_nets=%d, plot_id=%s",
                session_id,
                params.level,
                total_nets,
                plot_id
            )

            return {
                "type": "plot",
                "plot_id": plot_id,
                "title": title,
                "level": params.level,
                "total_nets": total_nets,
                "total_wards": total_wards,
                "wards_with_nets": total_wards,
                "figure": fig,
            }

        except Exception as exc:
            logger.error(
                "ITN allocation map failed: session=%s, error=%s",
                session_id,
                exc
            )
            raise ValueError(f"Failed to create ITN allocation map: {exc}") from exc

    def _load_dataset(self, entry: DatasetEntry) -> pd.DataFrame:
        """Load dataset from parquet or CSV."""
        derived = entry.metadata.get("derived_assets", {})
        parquet_path = derived.get("parquet")

        if parquet_path and Path(parquet_path).exists():
            return pd.read_parquet(parquet_path)

        return pd.read_csv(entry.path)

    def _find_nets_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Find ITN allocation column in the dataset.

        Returns:
            Column name or None if not found
        """
        candidates = [
            "nets_allocated",
            "itn_allocated",
            "itns_allocated",
            "bed_nets_allocated",
            "nets",
            "itns"
        ]

        for candidate in candidates:
            if candidate in df.columns:
                return candidate

        return None

    def _load_shapefile(self, entry: DatasetEntry, level: str) -> Optional[gpd.GeoDataFrame]:
        """Load shapefile for the specified administrative level."""
        derived = entry.metadata.get("derived_assets", {})
        shapefile_zip = derived.get("shapefile_zip")

        if not shapefile_zip or not Path(shapefile_zip).exists():
            logger.warning(f"No shapefile found for dataset {entry.dataset_id}")
            return None

        try:
            import tempfile
            import zipfile

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(shapefile_zip, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)

                shp_files = list(Path(tmpdir).glob("**/*.shp"))
                if not shp_files:
                    logger.error(f"No .shp file found in {shapefile_zip}")
                    return None

                gdf = gpd.read_file(shp_files[0])
                logger.info(f"Loaded shapefile: {len(gdf)} features, CRS: {gdf.crs}")

                if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")

                return gdf

        except Exception as exc:
            logger.error(f"Failed to load shapefile: {exc}")
            return None

    def _merge_data(self, gdf: gpd.GeoDataFrame, df: pd.DataFrame, level: str) -> gpd.GeoDataFrame:
        """Merge tabular data with geographic boundaries."""
        join_attempts = [
            ("WardCode", "WardCode"), ("WardName", "WardName"),
            ("ward_code", "ward_code"), ("ward_name", "ward_name"),
            ("LGACode", "LGACode"), ("LGAName", "LGAName"),
            ("lga_code", "lga_code"), ("lga_name", "lga_name"),
            ("StateCode", "StateCode"), ("StateName", "StateName"),
            ("state_code", "state_code"), ("state_name", "state_name"),
        ]

        for left_col, right_col in join_attempts:
            if left_col in gdf.columns and right_col in df.columns:
                merged = gdf.merge(df, left_on=left_col, right_on=right_col, how="left")
                logger.info(f"Merged on {left_col} = {right_col}: {len(merged)} records")
                return merged

        logger.warning("No common columns found, attempting index merge")
        return gdf.merge(df, left_index=True, right_index=True, how="left")

    def _create_itn_map(
        self,
        gdf: gpd.GeoDataFrame,
        nets_col: str,
        level: str
    ) -> dict:
        """Create Plotly ITN allocation choropleth map."""
        # Filter valid data
        clean = gdf.copy()
        clean = clean[clean.geometry.notnull() & ~clean.geometry.is_empty]

        if clean.empty:
            raise ValueError("No valid data for ITN allocation mapping")

        # Fill NaN nets with 0
        clean[nets_col] = clean[nets_col].fillna(0)

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

        # Prepare hover text
        label_col = self._get_label_column(clean, level)
        labels = clean.get(label_col, clean.index).astype(str)

        # Check for priority/rank columns
        priority_col = None
        for col in ["priority", "itn_priority", "allocation_priority"]:
            if col in clean.columns:
                priority_col = col
                break

        hover_text = []
        for i in range(len(clean)):
            parts = [
                f"<b>{labels.iloc[i]}</b>",
                f"Nets Allocated: {int(clean[nets_col].iloc[i]):,}"
            ]
            if priority_col:
                parts.append(f"Priority: {clean[priority_col].iloc[i]}")
            hover_text.append('<br>'.join(parts))

        # ITN maps use Blues color scale (nets = resource, blue = water/resource)
        fig = go.Figure()

        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson,
            locations=clean.index.astype(str),
            z=clean[nets_col],
            colorscale='Blues',
            text=hover_text,
            hovertemplate='%{text}<extra></extra>',
            marker_opacity=0.7,
            marker_line_width=1,
            marker_line_color='white',
            showscale=True,
            colorbar=dict(
                title="Nets<br>Allocated",
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
                'text': f'ITN Allocation Map - {level.upper()} Level',
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
