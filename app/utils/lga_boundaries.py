"""Utilities for working with national LGA boundaries."""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent.parent / "reference_data" / "nga_lga_boundaries.gpkg"


@lru_cache(maxsize=1)
def get_lga_boundaries() -> Optional[gpd.GeoDataFrame]:
    """Load the canonical LGA boundary dataset (EPSG:4326)."""
    if not _DATA_PATH.exists():
        logger.error("LGA boundary file not found at %s", _DATA_PATH)
        return None

    try:
        gdf = gpd.read_file(_DATA_PATH)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to read LGA boundaries: %s", exc)
        return None

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326, allow_override=True)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf["state_name_norm"] = gdf["state_name"].str.strip().str.lower()
    gdf["lga_name_norm"] = gdf["lga_name"].str.strip().str.lower()
    return gdf


def annotate_with_lga_names(wards_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add LGA/State names to a ward GeoDataFrame via spatial join."""
    reference = get_lga_boundaries()
    if reference is None:
        return wards_gdf

    needs_state = "StateName" not in wards_gdf.columns or wards_gdf["StateName"].isna().all()
    needs_lga = "LGAName" not in wards_gdf.columns or wards_gdf["LGAName"].isna().all()
    if not needs_state and not needs_lga:
        return wards_gdf

    working = wards_gdf.copy()
    if working.crs is None:
        working = working.set_crs(epsg=4326, allow_override=True)
    else:
        working = working.to_crs(epsg=4326)

    centroids = working.geometry.centroid
    centroid_gdf = gpd.GeoDataFrame(
        {
            "__orig_index": working.index,
        },
        geometry=centroids,
        crs=working.crs,
    )

    joined = gpd.sjoin_nearest(
        centroid_gdf,
        reference[["state_name", "lga_name", "geometry"]],
        how="left",
        distance_col="__distance",
    )

    mapping = (
        joined.set_index("__orig_index")
        .loc[:, ["state_name", "lga_name"]]
        .rename(columns={"state_name": "StateName", "lga_name": "LGAName"})
    )

    for column in ["StateName", "LGAName"]:
        if column not in wards_gdf.columns:
            wards_gdf[column] = pd.NA

    for idx, values in mapping.iterrows():
        if needs_state and pd.isna(wards_gdf.at[idx, "StateName"]):
            wards_gdf.at[idx, "StateName"] = values.get("StateName")
        if needs_lga and pd.isna(wards_gdf.at[idx, "LGAName"]):
            wards_gdf.at[idx, "LGAName"] = values.get("LGAName")

    return wards_gdf


def get_reference_lga_geometries(lga_info: pd.DataFrame) -> Optional[gpd.GeoDataFrame]:
    """Return LGA polygons that correspond to the provided LGACodes."""
    reference = get_lga_boundaries()
    if reference is None or lga_info is None or lga_info.empty:
        return None

    required_cols = {"LGACode", "StateName", "LGAName"}
    if not required_cols.issubset(lga_info.columns):
        return None

    normalized = (
        lga_info.dropna(subset=["LGACode", "LGAName"])
        .drop_duplicates("LGACode")
        .copy()
    )
    if normalized.empty:
        return None

    normalized["state_name_norm"] = normalized["StateName"].astype(str).str.strip().str.lower()
    normalized["lga_name_norm"] = normalized["LGAName"].astype(str).str.strip().str.lower()

    merged = normalized.merge(
        reference[
            [
                "state_name",
                "lga_name",
                "state_name_norm",
                "lga_name_norm",
                "geometry",
            ]
        ],
        on=["state_name_norm", "lga_name_norm"],
        how="left",
    )

    missing = merged["geometry"].isna().sum()
    if missing:
        logger.warning("%s LGAs could not be matched to reference boundaries", missing)
        merged = merged.dropna(subset=["geometry"])

    if merged.empty:
        return None

    result = gpd.GeoDataFrame(
        merged.drop(columns=["state_name_norm", "lga_name_norm"]),
        geometry="geometry",
        crs=reference.crs,
    )
    return result
