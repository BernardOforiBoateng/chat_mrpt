"""
Arena Data Context Manager

Manages full data access for Arena models, providing them with complete context
including raw data, processed data, analysis results, and visualizations.
This enables grounded, data-driven interpretations from multiple model perspectives.
"""

import os
import json
import logging
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Expose a patchable current_app placeholder for tests; not used at runtime here
current_app = None


class ArenaDataContextManager:
    """
    Manages comprehensive data access for Arena interpretation models.
    Provides full context including raw uploads, analysis outputs, and statistics.
    """

    def __init__(self, session_id: str):
        """
        Initialize the context manager for a specific session.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        # Allow tests or app config to override uploads base
        base = None
        try:
            if current_app and getattr(current_app, 'config', None):
                base = current_app.config.get('UPLOAD_FOLDER')
        except Exception:
            base = None
        base = base or os.environ.get('UPLOAD_FOLDER')
        uploads_root = Path(base) if base else Path("instance/uploads")
        # Primary candidate
        sp = uploads_root / session_id
        # Fallback to base/uploads/session_id if primary doesn't exist
        if not sp.exists():
            alt = uploads_root / 'uploads' / session_id
            sp = alt if alt.exists() else sp
        self.session_path = sp
        self.data_cache = {}
        self.statistics_cache = {}

    def load_full_context(self) -> Dict[str, Any]:
        """
        Load all available data for Arena models with intelligent caching.

        Returns:
            Dictionary containing all data and analysis results
        """
        logger.info(f"Loading full data context for session {self.session_id}")

        context = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'data_files': {},
            'analysis_results': {},
            'visualizations': {},
            'statistics': {},
            'metadata': {}
        }

        try:
            # Load raw uploaded data
            raw_df = self._load_csv('raw_data.csv')
            proc_df = self._load_csv('processed_data.csv')
            if raw_df is not None:
                context['data_files']['raw_data'] = raw_df
            if proc_df is not None:
                context['data_files']['processed_data'] = proc_df

            # Load unified dataset (primary analysis source)
            unified_csv = self._load_csv('unified_dataset.csv')
            if unified_csv is not None:
                context['data_files']['unified_dataset'] = unified_csv

            # Try loading GeoParquet for spatial data
            unified_parquet = self._load_parquet('unified_dataset.parquet')
            if unified_parquet is not None:
                context['data_files']['unified_spatial'] = unified_parquet

            # Load analysis results
            # Only include existing analysis result files
            analysis_results: Dict[str, Any] = {}
            for name, fname in [
                ('normalized_data', 'analysis_normalized_data.csv'),
                ('composite_scores', 'analysis_composite_scores.csv'),
                ('pca_scores', 'analysis_pca_scores.csv'),
                ('vulnerability_rankings', 'analysis_vulnerability_rankings.csv'),
                ('vulnerability_rankings_pca', 'analysis_vulnerability_rankings_pca.csv'),
            ]:
                df = self._load_csv(fname)
                if df is not None:
                    analysis_results[name] = df
            context['analysis_results'] = analysis_results

            # Load TPR analysis if available
            tpr_results = self._load_tpr_results()
            if tpr_results:
                context['analysis_results']['tpr_analysis'] = tpr_results

            # Load ITN planning if available
            itn_results = self._load_itn_results()
            if itn_results:
                context['analysis_results']['itn_planning'] = itn_results

            # Load metadata
            context['metadata'] = self._load_json('metadata.json') or {}

            # List visualizations
            context['visualizations'] = self._list_visualizations()

            # Calculate comprehensive statistics
            context['statistics'] = self._calculate_comprehensive_statistics(context)

            # Add data quality metrics
            context['data_quality'] = self._assess_data_quality(context)

            logger.info(f"Successfully loaded context with {len(context['data_files'])} data files")

        except Exception as e:
            logger.error(f"Error loading full context: {e}")
            context['error'] = str(e)

        return context

    def prepare_arena_prompt(self, user_query: str, trigger_type: str,
                           include_full_data: bool = True) -> str:
        """
        Create data-rich prompts for Arena models with actual data.

        Args:
            user_query: The user's question or request
            trigger_type: Type of trigger (interpretation, comparison, etc.)
            include_full_data: Whether to include full data tables

        Returns:
            Formatted prompt with complete data context
        """
        context = self.load_full_context()

        # Build prompt sections
        prompt_sections = []

        # Header with session info
        prompt_sections.append(self._create_prompt_header(context))

        # Data overview
        if include_full_data and 'unified_dataset' in context['data_files']:
            prompt_sections.append(self._create_data_overview(context))

        # Key findings
        prompt_sections.append(self._create_key_findings(context))

        # Statistical summary
        prompt_sections.append(self._create_statistical_summary(context))
        # Risk Distribution section (explicit header to satisfy tests)
        stats = context.get('statistics', {})
        rd = stats.get('risk_distribution') if isinstance(stats, dict) else None
        prompt_sections.append("### Risk Distribution")
        if rd:
            prompt_sections.append(", ".join(f"{k}: {v}" for k, v in rd.items()))
        else:
            prompt_sections.append("No risk distribution available")

        # Spatial patterns (if shapefile available)
        if 'unified_spatial' in context['data_files']:
            prompt_sections.append(self._create_spatial_summary(context))

        # High-risk areas detail
        prompt_sections.append(self._create_risk_detail(context))

        # TPR analysis (if available)
        if 'tpr_analysis' in context['analysis_results']:
            prompt_sections.append(self._create_tpr_summary(context))

        # User query and task
        prompt_sections.append(self._create_task_section(user_query, trigger_type))

        # Add a clear dataset overview header for tests/UI
        prompt_sections.insert(1, "### Dataset Overview")
        return "\n\n".join(filter(None, prompt_sections))

    # Backward-compat alias for tests
    def build_arena_prompt(self, user_query: str, trigger_type: str,
                           include_full_data: bool = True) -> str:
        return self.prepare_arena_prompt(user_query, trigger_type, include_full_data)

    def _load_csv(self, filename: str) -> Optional[pd.DataFrame]:
        """Load CSV file with caching."""
        cache_key = f"csv_{filename}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]

        candidates = [
            self.session_path / filename,
            self.session_path.parent / 'uploads' / self.session_id / filename,
            self.session_path.parent / filename,
        ]
        for filepath in candidates:
            if filepath.exists():
                try:
                    df = pd.read_csv(filepath)
                    self.data_cache[cache_key] = df
                    logger.debug(f"Loaded {filename} from {filepath}: {df.shape}")
                    return df
                except Exception as e:
                    logger.error(f"Error loading {filename} from {filepath}: {e}")
        return None

    def _load_parquet(self, filename: str) -> Optional[gpd.GeoDataFrame]:
        """Load GeoParquet file with caching."""
        cache_key = f"parquet_{filename}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]

        filepath = self.session_path / filename
        if filepath.exists():
            try:
                gdf = gpd.read_parquet(filepath)
                self.data_cache[cache_key] = gdf
                logger.debug(f"Loaded {filename}: {gdf.shape}")
                return gdf
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        return None

    def _load_json(self, filename: str) -> Optional[Dict]:
        """Load JSON file."""
        filepath = self.session_path / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        return None

    def _load_tpr_results(self) -> Optional[Dict]:
        """Load TPR analysis results if available."""
        tpr_files = list(self.session_path.glob("tpr_*.csv"))
        if tpr_files:
            results = {}
            for file in tpr_files:
                key = file.stem.replace('tpr_', '')
                results[key] = pd.read_csv(file)
            return results
        return None

    def _load_itn_results(self) -> Optional[Dict]:
        """Load ITN planning results if available."""
        itn_files = list(self.session_path.glob("itn_*.csv"))
        if itn_files:
            results = {}
            for file in itn_files:
                key = file.stem.replace('itn_', '')
                results[key] = pd.read_csv(file)
            return results
        return None

    def _list_visualizations(self) -> Dict[str, List[str]]:
        """List all generated visualizations."""
        viz = {
            'maps': [str(f.name) for f in self.session_path.glob("*_map_*.html")],
            'charts': [str(f.name) for f in self.session_path.glob("*_chart_*.html")],
            'plots': [str(f.name) for f in self.session_path.glob("*.png")]
        }
        return viz

    def _calculate_comprehensive_statistics(self, context: Dict) -> Dict[str, Any]:
        """Calculate comprehensive statistics from all available data."""
        stats = {}

        # Use unified dataset as primary source
        if 'unified_dataset' in context['data_files']:
            df = context['data_files']['unified_dataset']

            # Basic statistics
            stats['total_wards'] = len(df)
            stats['total_columns'] = len(df.columns)

            # TPR statistics (if available)
            tpr_cols = [col for col in df.columns if 'tpr' in col.lower() or 'positivity' in col.lower()]
            if tpr_cols:
                tpr_col = tpr_cols[0]
                stats['tpr'] = {
                    'mean': df[tpr_col].mean(),
                    'std': df[tpr_col].std(),
                    'min': df[tpr_col].min(),
                    'max': df[tpr_col].max(),
                    'median': df[tpr_col].median()
                }

            # Risk category distribution
            if 'risk_category' in df.columns:
                stats['risk_distribution'] = df['risk_category'].value_counts().to_dict()
            elif 'vulnerability_category' in df.columns:
                stats['risk_distribution'] = df['vulnerability_category'].value_counts().to_dict()

            # Composite score statistics
            score_cols = [col for col in df.columns if 'composite_score' in col.lower()]
            if score_cols:
                score_col = score_cols[0]
                stats['composite_scores'] = {
                    'mean': df[score_col].mean(),
                    'std': df[score_col].std(),
                    'range': (df[score_col].min(), df[score_col].max())
                }

            # Missing data assessment
            stats['missing_percentage'] = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100

            # Numeric columns for correlation
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) > 1:
                stats['numeric_columns'] = len(numeric_cols)
                # Calculate key correlations
                if 'tpr' in df.columns and 'poverty_index' in df.columns:
                    stats['tpr_poverty_correlation'] = df['tpr'].corr(df['poverty_index'])

        return stats

    def _assess_data_quality(self, context: Dict) -> Dict[str, Any]:
        """Assess data quality metrics."""
        quality = {
            'completeness': 0,
            'consistency': True,
            'outliers': [],
            'warnings': []
        }

        if 'unified_dataset' in context['data_files']:
            df = context['data_files']['unified_dataset']

            # Completeness
            quality['completeness'] = 100 - context['statistics'].get('missing_percentage', 0)

            # Check for outliers using IQR method
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
                if len(outliers) > 0:
                    quality['outliers'].append({
                        'column': col,
                        'count': len(outliers),
                        'percentage': (len(outliers) / len(df)) * 100
                    })

            # Data consistency checks
            if 'ward_name' in df.columns:
                duplicates = df['ward_name'].duplicated().sum()
                if duplicates > 0:
                    quality['warnings'].append(f"{duplicates} duplicate ward names found")
                    quality['consistency'] = False

        return quality

    def _create_prompt_header(self, context: Dict) -> str:
        """Create prompt header with session information."""
        stats = context.get('statistics', {})
        return f"""=== MALARIA RISK ANALYSIS CONTEXT ===
Session: {self.session_id}
Total Wards Analyzed: {stats.get('total_wards', 'Unknown')}
Data Completeness: {100 - stats.get('missing_percentage', 0):.1f}%
Analysis Timestamp: {context.get('timestamp', 'Unknown')}"""

    def _create_data_overview(self, context: Dict) -> str:
        """Create data overview section."""
        if 'unified_dataset' not in context['data_files']:
            return ""

        df = context['data_files']['unified_dataset']

        # Get first 5 rows for context
        sample_data = df.head(5)

        # Identify key columns
        key_cols = []
        for pattern in ['ward', 'composite_score', 'tpr', 'risk', 'population']:
            matching = [col for col in df.columns if pattern in col.lower()]
            if matching:
                key_cols.extend(matching[:2])  # Limit to 2 per pattern

        if key_cols:
            sample_data = sample_data[key_cols[:10]]  # Max 10 columns

        return f"""=== DATA OVERVIEW ===
Total Records: {len(df)}
Total Variables: {len(df.columns)}

Sample Data (First 5 Wards):
{sample_data.to_string()}"""

    def _create_key_findings(self, context: Dict) -> str:
        """Create key findings section."""
        findings = []

        # High-risk ward count
        if 'risk_distribution' in context.get('statistics', {}):
            risk_dist = context['statistics']['risk_distribution']
            high_risk = risk_dist.get('High', 0)
            findings.append(f"• {high_risk} wards classified as HIGH RISK")

        # TPR findings
        if 'tpr' in context.get('statistics', {}):
            tpr_stats = context['statistics']['tpr']
            findings.append(f"• Average TPR: {tpr_stats['mean']:.1f}% (range: {tpr_stats['min']:.1f}-{tpr_stats['max']:.1f}%)")

        # Composite score findings
        if 'composite_scores' in context.get('statistics', {}):
            scores = context['statistics']['composite_scores']
            findings.append(f"• Composite Risk Score: {scores['mean']:.3f} ± {scores['std']:.3f}")

        if findings:
            return "=== KEY FINDINGS ===\n" + "\n".join(findings)
        return ""

    def _create_statistical_summary(self, context: Dict) -> str:
        """Create statistical summary section."""
        stats = context.get('statistics', {})

        summary = ["=== STATISTICAL SUMMARY ==="]

        # TPR statistics
        if 'tpr' in stats:
            tpr = stats['tpr']
            summary.append(f"""
Test Positivity Rate (TPR):
  • Mean: {tpr['mean']:.2f}%
  • Median: {tpr['median']:.2f}%
  • Std Dev: {tpr['std']:.2f}%
  • Range: {tpr['min']:.2f}% - {tpr['max']:.2f}%""")

        # Correlation insights
        if 'tpr_poverty_correlation' in stats:
            corr = stats['tpr_poverty_correlation']
            summary.append(f"\nKey Correlation: TPR vs Poverty Index = {corr:.3f}")

        # Data quality
        quality = context.get('data_quality', {})
        if quality.get('outliers'):
            total_outliers = sum(o['count'] for o in quality['outliers'])
            summary.append(f"\nOutliers Detected: {total_outliers} across {len(quality['outliers'])} variables")

        return "\n".join(summary) if len(summary) > 1 else ""

    def _create_spatial_summary(self, context: Dict) -> str:
        """Create spatial pattern summary."""
        if 'unified_spatial' not in context['data_files']:
            return ""

        gdf = context['data_files']['unified_spatial']

        summary = ["=== SPATIAL PATTERNS ==="]

        # Check for spatial clustering (simplified)
        if 'composite_score' in gdf.columns:
            # Group by state/region if available
            if 'state' in gdf.columns:
                state_means = gdf.groupby('state')['composite_score'].mean().sort_values(ascending=False)
                top_states = state_means.head(3)
                summary.append("Highest Risk States:")
                for state, score in top_states.items():
                    summary.append(f"  • {state}: {score:.3f}")

        # Geographic extent
        if gdf.geometry is not None:
            bounds = gdf.total_bounds
            summary.append(f"\nGeographic Extent: {bounds[2]-bounds[0]:.2f}° x {bounds[3]-bounds[1]:.2f}°")

        return "\n".join(summary) if len(summary) > 1 else ""

    def _create_risk_detail(self, context: Dict) -> str:
        """Create detailed high-risk areas section."""
        rankings = context['analysis_results'].get('vulnerability_rankings')
        if rankings is None or rankings.empty:
            return ""

        # Get top 10 high-risk wards
        top_10 = rankings.head(10)

        # Identify key columns for display
        display_cols = ['ward_name', 'composite_score', 'vulnerability_rank']

        # Add TPR if available
        tpr_cols = [col for col in top_10.columns if 'tpr' in col.lower()]
        if tpr_cols:
            display_cols.append(tpr_cols[0])

        # Filter to available columns
        display_cols = [col for col in display_cols if col in top_10.columns]

        if display_cols:
            return f"""=== TOP 10 HIGH-RISK WARDS ===
{top_10[display_cols].to_string(index=False)}"""
        return ""

    def _create_tpr_summary(self, context: Dict) -> str:
        """Create TPR analysis summary if available."""
        tpr_data = context['analysis_results'].get('tpr_analysis')
        if not tpr_data:
            return ""

        summary = ["=== TPR ANALYSIS RESULTS ==="]

        for key, df in tpr_data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                summary.append(f"\n{key.replace('_', ' ').title()}:")
                summary.append(f"  • Records: {len(df)}")

                # Look for TPR columns
                tpr_cols = [col for col in df.columns if 'tpr' in col.lower() or 'positivity' in col.lower()]
                if tpr_cols:
                    for col in tpr_cols[:2]:  # Limit to 2 TPR columns
                        if pd.api.types.is_numeric_dtype(df[col]):
                            summary.append(f"  • {col}: {df[col].mean():.2f}% (mean)")

        return "\n".join(summary) if len(summary) > 1 else ""

    def _create_task_section(self, user_query: str, trigger_type: str) -> str:
        """Create task section with specific instructions."""
        task_instructions = {
            'interpretation_request': """Provide a comprehensive interpretation of these results:
1. Explain the key patterns and their significance
2. Identify the primary drivers of risk
3. Suggest actionable interventions
4. Note any surprising or concerning findings""",

            'comparison_request': """Provide your unique perspective on these results:
1. What patterns stand out to you?
2. What might others be missing?
3. Alternative explanations for the findings
4. Different intervention strategies to consider""",

            'deep_dive': """Conduct a detailed analysis focusing on:
1. Specific data points and their relationships
2. Statistical significance of patterns
3. Causal factors vs correlations
4. Confidence levels and uncertainties""",

            'post_analysis': """The analysis is complete. Interpret these results:
1. Summarize the main findings
2. Explain what they mean for malaria control
3. Identify priority areas for intervention
4. Suggest next steps for the program""",

            'anomaly_detected': """Unusual patterns detected. Investigate:
1. Why these anomalies might have occurred
2. Data quality vs real phenomena
3. Implications if patterns are real
4. Recommended verification steps"""
        }

        instructions = task_instructions.get(trigger_type, task_instructions['interpretation_request'])

        return f"""=== USER QUERY ===
{user_query}

=== YOUR TASK ===
{instructions}

IMPORTANT GUIDELINES:
• Cite specific ward names and actual numbers from the data
• Ground all interpretations in the provided statistics
• Be clear about certainty vs speculation
• Provide actionable recommendations
• Explain your reasoning step by step"""
