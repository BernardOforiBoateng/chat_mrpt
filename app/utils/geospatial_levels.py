"""Utility helpers for preparing ward/LGA geographic views."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import geopandas as gpd
import pandas as pd

LGA_CODE_CANDIDATES = [
    "LGACode",
    "lga_code",
    "lgaCode",
    "LGA",
    "lga",
]

LGA_NAME_CANDIDATES = [
    "LGAName",
    "lga_name",
    "LGA_NAME",
    "lgaName",
    "AdminLevel2",
]

STATE_CODE_CANDIDATES = [
    "StateCode",
    "state_code",
    "STATE",
]


def _detect_column(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    for name in candidates:
        if name in df.columns:
            return name
    # Try case-insensitive match as fallback
    lower_map = {col.lower(): col for col in df.columns}
    for name in candidates:
        lowered = name.lower()
        if lowered in lower_map:
            return lower_map[lowered]
    return None


def normalize_lga_code(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def collect_lga_options(*frames: Optional[pd.DataFrame]) -> List[Dict[str, str]]:
    """Collect a unique list of LGAs for dropdown controls."""
    seen: Dict[str, str] = {}
    for frame in frames:
        if frame is None or frame.empty:
            continue
        code_col = _detect_column(frame, LGA_CODE_CANDIDATES)
        if not code_col:
            continue
        name_col = _detect_column(frame, LGA_NAME_CANDIDATES)
        for _, row in frame[[code_col]].dropna().drop_duplicates().iterrows():
            code = normalize_lga_code(row[code_col])
            if not code:
                continue
            label = code
            if name_col and name_col in frame.columns:
                label_value = frame.loc[frame[code_col] == row[code_col], name_col].dropna()
                if not label_value.empty:
                    label = str(label_value.iloc[0]).strip() or code
            seen[code] = label
    options = [
        {"code": code, "label": label}
        for code, label in seen.items()
    ]
    options.sort(key=lambda item: item["label"].lower())
    return options


def dissolve_to_lga(
    gdf: gpd.GeoDataFrame,
    value_columns: Sequence[str],
    sum_columns: Optional[Sequence[str]] = None,
    mean_columns: Optional[Sequence[str]] = None,
) -> gpd.GeoDataFrame:
    """Aggregate a ward-level GeoDataFrame into LGA polygons."""
    if gdf.empty:
        return gdf
    code_col = _detect_column(gdf, LGA_CODE_CANDIDATES)
    if not code_col:
        raise ValueError("No LGACode column available for dissolve")
    agg_dict: Dict[str, str] = {}
    for col in value_columns:
        if col in gdf.columns:
            agg_dict[col] = 'mean'
    for col in sum_columns or []:
        if col in gdf.columns:
            agg_dict[col] = 'sum'
    for col in mean_columns or []:
        if col in gdf.columns:
            agg_dict[col] = 'mean'
    # Preserve identifying columns
    for col in LGA_NAME_CANDIDATES + STATE_CODE_CANDIDATES:
        if col in gdf.columns:
            agg_dict[col] = agg_dict.get(col, 'first')
    dissolved = gdf.dissolve(by=code_col, aggfunc=agg_dict).reset_index()
    if code_col in dissolved.columns:
        dissolved.rename(columns={code_col: 'LGACode'}, inplace=True)
    elif 'LGACode' not in dissolved.columns:
        dissolved['LGACode'] = ''
    dissolved['LGACode'] = dissolved['LGACode'].apply(normalize_lga_code)
    return dissolved


def apply_lga_highlight(
    gdf: gpd.GeoDataFrame,
    selected_lgas: Optional[Iterable[str]],
    code_column: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Add a boolean column indicating whether each record belongs to a selected LGA."""
    if gdf.empty:
        gdf['_is_selected_lga'] = False
        return gdf
    codes = {normalize_lga_code(code) for code in (selected_lgas or []) if code}
    if not code_column:
        code_column = _detect_column(gdf, LGA_CODE_CANDIDATES) or 'LGACode'
    if code_column not in gdf.columns:
        gdf['_is_selected_lga'] = False
        return gdf
    gdf['_is_selected_lga'] = gdf[code_column].apply(lambda value: normalize_lga_code(value) in codes)
    return gdf
