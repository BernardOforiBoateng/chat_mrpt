"""
Arena Model-Specific Prompt Builder

Optimizes prompts for each Arena model based on their unique strengths:
- Phi-3 Mini: Logical reasoning and pattern analysis
- Mistral 7B: Statistical analysis and mathematical insights
- Qwen 2.5 7B: Technical implementation and multilingual context
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from scipy import stats

logger = logging.getLogger(__name__)


class ModelSpecificPromptBuilder:
    """
    Creates optimized prompts for each Arena model based on their capabilities.
    """

    # Model personalities and strengths
    MODEL_PROFILES = {
        'phi3:mini': {
            'name': 'The Analyst',
            'strengths': ['logical reasoning', 'pattern recognition', 'causal analysis', 'step-by-step thinking'],
            'focus': 'systematic analysis',
            'temperature': 0.7
        },
        'mistral:7b': {
            'name': 'The Statistician',
            'strengths': ['mathematical analysis', 'statistical significance', 'quantitative reasoning', 'probability'],
            'focus': 'numerical precision',
            'temperature': 0.5
        },
        'qwen2.5:7b': {
            'name': 'The Technician',
            'strengths': ['technical implementation', 'data processing', 'multilingual insights', 'practical solutions'],
            'focus': 'actionable recommendations',
            'temperature': 0.6
        }
    }

    def __init__(self):
        """Initialize the prompt builder."""
        self.model_profiles = self.MODEL_PROFILES

    def build_prompt(self, model_name: str, base_prompt: str, context: Dict[str, Any]) -> str:
        """
        Build model-specific prompt with tailored instructions and focus areas.

        Args:
            model_name: Name of the model (e.g., 'phi3:mini')
            base_prompt: Base prompt with data context
            context: Full data context from ArenaDataContextManager

        Returns:
            Optimized prompt for the specific model
        """
        # Get model profile
        profile = self.model_profiles.get(model_name, self.model_profiles['phi3:mini'])

        # Add model-specific instructions
        if 'phi3' in model_name.lower():
            return self._build_phi3_prompt(base_prompt, context, profile)
        elif 'mistral' in model_name.lower():
            return self._build_mistral_prompt(base_prompt, context, profile)
        elif 'qwen' in model_name.lower():
            return self._build_qwen_prompt(base_prompt, context, profile)
        else:
            # Default prompt
            return self._build_default_prompt(base_prompt, context, profile)

    def _build_phi3_prompt(self, base_prompt: str, context: Dict, profile: Dict) -> str:
        """
        Build Phi-3 optimized prompt focusing on logical reasoning and patterns.
        """
        # Extract pattern-relevant information
        pattern_analysis = self._extract_patterns(context)

        prompt = f"""{base_prompt}

=== YOUR ROLE: {profile['name']} ===
You excel at logical reasoning and pattern recognition. Focus on systematic analysis.

=== SPECIALIZED ANALYSIS FOCUS ===

1. PATTERN IDENTIFICATION:
{pattern_analysis}

2. CAUSAL REASONING:
• Identify cause-effect relationships in the data
• Distinguish correlation from causation
• Explain the logical chain of factors

3. SYSTEMATIC BREAKDOWN:
• Step 1: Identify the primary pattern
• Step 2: Trace contributing factors
• Step 3: Explain the mechanism
• Step 4: Predict implications

4. REASONING FRAMEWORK:
• Use "If... then..." logical structures
• Consider alternative explanations
• Identify necessary vs sufficient conditions

ANALYSIS STYLE:
• Think step-by-step through the problem
• Use clear logical connections
• Identify patterns others might miss
• Explain your reasoning process

Remember: Your strength is in seeing the logical structure and patterns that connect the data points."""

        return prompt

    def _build_mistral_prompt(self, base_prompt: str, context: Dict, profile: Dict) -> str:
        """
        Build Mistral optimized prompt focusing on statistical and mathematical analysis.
        """
        # Calculate advanced statistics
        stats_analysis = self._calculate_advanced_statistics(context)

        prompt = f"""{base_prompt}

=== YOUR ROLE: {profile['name']} ===
You excel at mathematical and statistical analysis. Focus on numerical precision and significance.

=== STATISTICAL ANALYSIS REQUIREMENTS ===

{stats_analysis}

=== QUANTITATIVE FOCUS AREAS ===

1. STATISTICAL SIGNIFICANCE:
• Calculate confidence intervals where applicable
• Assess p-values for key relationships
• Identify statistically significant patterns
• Quantify uncertainty in predictions

2. MATHEMATICAL RELATIONSHIPS:
• Correlation coefficients between variables
• Regression insights if applicable
• Distribution characteristics (normal, skewed, etc.)
• Outlier analysis and impact

3. NUMERICAL PRECISION:
• Provide exact numbers and percentages
• Calculate effect sizes
• Quantify risk differentials
• Compute population attributable fractions

4. PROBABILITY ASSESSMENT:
• Likelihood of outcomes
• Risk probabilities
• Confidence levels in predictions
• Bayesian reasoning where appropriate

ANALYSIS STYLE:
• Lead with numbers and statistics
• Support claims with mathematical evidence
• Calculate, don't estimate
• Quantify everything possible

Remember: Your strength is in rigorous quantitative analysis and mathematical precision."""

        return prompt

    def _build_qwen_prompt(self, base_prompt: str, context: Dict, profile: Dict) -> str:
        """
        Build Qwen optimized prompt focusing on technical implementation and practical solutions.
        """
        # Extract technical specifications
        tech_specs = self._extract_technical_specs(context)

        prompt = f"""{base_prompt}

=== YOUR ROLE: {profile['name']} ===
You excel at technical implementation and practical solutions. Focus on actionable recommendations.

=== TECHNICAL SPECIFICATIONS ===
{tech_specs}

=== IMPLEMENTATION FOCUS AREAS ===

1. DATA ARCHITECTURE:
• Data pipeline considerations
• Processing optimizations
• Storage requirements
• Scalability factors

2. PRACTICAL INTERVENTIONS:
• Specific implementation steps
• Resource requirements
• Timeline estimates
• Technical prerequisites

3. OPERATIONAL CONSIDERATIONS:
• Health facility capacity
• Supply chain logistics
• Training requirements
• Monitoring systems

4. CROSS-CULTURAL FACTORS:
• Local context considerations
• Language/communication needs
• Cultural sensitivities
• Community engagement strategies

5. TECHNICAL SOLUTIONS:
• Code snippets for analysis (if helpful)
• Database queries for monitoring
• Dashboard specifications
• API integration points

ANALYSIS STYLE:
• Provide concrete, actionable steps
• Include technical specifications
• Consider implementation challenges
• Suggest monitoring metrics

Remember: Your strength is in translating analysis into practical, implementable solutions."""

        return prompt

    def _build_default_prompt(self, base_prompt: str, context: Dict, profile: Dict) -> str:
        """
        Build default prompt for unknown models.
        """
        return f"""{base_prompt}

=== YOUR ROLE ===
Analyze the data comprehensively, focusing on your unique perspective.

=== ANALYSIS GUIDELINES ===
• Identify key patterns and insights
• Explain your reasoning clearly
• Provide actionable recommendations
• Support claims with data

Focus on providing valuable insights that complement other analytical perspectives."""

    def _extract_patterns(self, context: Dict) -> str:
        """
        Extract pattern-relevant information for Phi-3.
        """
        patterns = []

        # Spatial clustering patterns
        if 'unified_dataset' in context.get('data_files', {}):
            df = context['data_files']['unified_dataset']

            # Check for geographic patterns
            if 'state' in df.columns and 'composite_score' in df.columns:
                state_variance = df.groupby('state')['composite_score'].var()
                if len(state_variance) > 1:
                    patterns.append(f"• Geographic clustering: Variance between states = {state_variance.mean():.4f}")

            # Temporal patterns if date columns exist
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'month' in col.lower()]
            if date_cols:
                patterns.append(f"• Temporal data available in {len(date_cols)} columns")

            # Risk category patterns
            if 'risk_category' in df.columns:
                risk_dist = df['risk_category'].value_counts()
                patterns.append(f"• Risk distribution pattern: {risk_dist.to_dict()}")

        # Correlation patterns
        if 'statistics' in context:
            stats = context['statistics']
            if 'tpr_poverty_correlation' in stats:
                corr = stats['tpr_poverty_correlation']
                patterns.append(f"• TPR-Poverty correlation strength: {abs(corr):.3f} ({'positive' if corr > 0 else 'negative'})")

        # Outlier patterns
        if 'data_quality' in context:
            outliers = context['data_quality'].get('outliers', [])
            if outliers:
                patterns.append(f"• Outlier patterns detected in {len(outliers)} variables")

        return "\n".join(patterns) if patterns else "• No clear patterns identified yet - investigate further"

    def _calculate_advanced_statistics(self, context: Dict) -> str:
        """
        Calculate advanced statistics for Mistral.
        """
        stats_lines = ["=== ADVANCED STATISTICAL METRICS ==="]

        if 'unified_dataset' in context.get('data_files', {}):
            df = context['data_files']['unified_dataset']

            # Identify numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            # Basic statistics
            stats_lines.append(f"\n• Dataset size: n = {len(df)}")
            stats_lines.append(f"• Variables: p = {len(numeric_cols)} numeric")

            # Distribution tests
            if 'composite_score' in numeric_cols:
                scores = df['composite_score'].dropna()
                if len(scores) > 20:
                    # Shapiro-Wilk test for normality
                    stat, p_value = stats.shapiro(scores[:5000])  # Limit for performance
                    stats_lines.append(f"\n• Composite Score Distribution:")
                    stats_lines.append(f"  - Shapiro-Wilk test: W={stat:.4f}, p={p_value:.4f}")
                    stats_lines.append(f"  - Distribution: {'Normal' if p_value > 0.05 else 'Non-normal'}")

                    # Skewness and kurtosis
                    skew = scores.skew()
                    kurt = scores.kurtosis()
                    stats_lines.append(f"  - Skewness: {skew:.3f} ({'right' if skew > 0 else 'left'}-skewed)")
                    stats_lines.append(f"  - Excess kurtosis: {kurt:.3f}")

            # Correlation matrix insights
            if len(numeric_cols) > 2:
                corr_matrix = df[numeric_cols].corr()

                # Find strongest correlations
                upper_tri = corr_matrix.where(
                    np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
                )
                strongest = upper_tri.abs().unstack().sort_values(ascending=False)

                stats_lines.append(f"\n• Strongest Correlations:")
                for i, (pair, corr_val) in enumerate(strongest.head(3).items()):
                    if not pd.isna(corr_val):
                        stats_lines.append(f"  - {pair[0]} vs {pair[1]}: r={corr_val:.3f}")

            # Variance explained (if PCA results available)
            if 'pca_scores' in context.get('analysis_results', {}):
                pca_df = context['analysis_results']['pca_scores']
                if 'PC1' in pca_df.columns:
                    stats_lines.append(f"\n• PCA Variance Explained:")
                    pc_cols = [col for col in pca_df.columns if col.startswith('PC')]
                    for i, pc in enumerate(pc_cols[:3], 1):
                        # Estimate variance (would need actual values from PCA)
                        stats_lines.append(f"  - Component {i}: ~{100/len(pc_cols):.1f}% (estimate)")

            # Sample size calculations
            stats_lines.append(f"\n• Statistical Power:")
            stats_lines.append(f"  - For α=0.05, β=0.80: Adequate for detecting medium effect sizes")
            if len(df) < 30:
                stats_lines.append(f"  - WARNING: Small sample size (n<30), use non-parametric tests")
            elif len(df) < 100:
                stats_lines.append(f"  - Moderate sample size, suitable for most analyses")
            else:
                stats_lines.append(f"  - Large sample size, robust statistical inference possible")

        return "\n".join(stats_lines)

    def _extract_technical_specs(self, context: Dict) -> str:
        """
        Extract technical specifications for Qwen.
        """
        specs = ["=== TECHNICAL ENVIRONMENT ==="]

        # Data specifications
        if 'unified_dataset' in context.get('data_files', {}):
            df = context['data_files']['unified_dataset']

            specs.append(f"\n• Data Specifications:")
            specs.append(f"  - Format: {'GeoDataFrame' if 'geometry' in df.columns else 'DataFrame'}")
            specs.append(f"  - Memory usage: ~{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
            specs.append(f"  - Shape: {df.shape[0]} rows × {df.shape[1]} columns")

            # Data types
            dtypes = df.dtypes.value_counts()
            specs.append(f"\n• Column Types:")
            for dtype, count in dtypes.items():
                specs.append(f"  - {dtype}: {count} columns")

        # File inventory
        specs.append(f"\n• Generated Files:")
        if 'visualizations' in context:
            viz = context['visualizations']
            specs.append(f"  - Maps: {len(viz.get('maps', []))} HTML files")
            specs.append(f"  - Charts: {len(viz.get('charts', []))} HTML files")
            specs.append(f"  - Plots: {len(viz.get('plots', []))} PNG files")

        # Processing capabilities
        specs.append(f"\n• Processing Capabilities:")
        specs.append(f"  - Spatial analysis: {'Available' if 'unified_spatial' in context.get('data_files', {}) else 'Limited'}")
        specs.append(f"  - Time series: {'Available' if any('date' in str(col).lower() for col in context.get('data_files', {}).get('unified_dataset', pd.DataFrame()).columns) else 'Not available'}")
        specs.append(f"  - ML-ready: {'Yes' if 'normalized_data' in context.get('analysis_results', {}) else 'Requires preprocessing'}")

        # Intervention requirements (if ITN planning available)
        if 'itn_planning' in context.get('analysis_results', {}):
            specs.append(f"\n• ITN Distribution Requirements:")
            itn_data = context['analysis_results']['itn_planning']
            for key, value in itn_data.items():
                if isinstance(value, pd.DataFrame) and not value.empty:
                    specs.append(f"  - {key.replace('_', ' ').title()}: {len(value)} records")

        # API/Integration readiness
        specs.append(f"\n• Integration Readiness:")
        specs.append(f"  - Data format: JSON-serializable")
        specs.append(f"  - Session-based: {context.get('session_id', 'Unknown')}")
        specs.append(f"  - Real-time capable: Yes (via Redis)")

        return "\n".join(specs)

    def get_model_temperature(self, model_name: str) -> float:
        """
        Get recommended temperature setting for a model.

        Args:
            model_name: Name of the model

        Returns:
            Recommended temperature value
        """
        profile = self.model_profiles.get(model_name, {})
        return profile.get('temperature', 0.7)

    def get_model_role(self, model_name: str) -> str:
        """
        Get the role/persona for a model.

        Args:
            model_name: Name of the model

        Returns:
            Model role/persona string
        """
        profile = self.model_profiles.get(model_name, {})
        return profile.get('name', 'Analyst')

    def get_model_strengths(self, model_name: str) -> List[str]:
        """
        Get list of model strengths.

        Args:
            model_name: Name of the model

        Returns:
            List of strength areas
        """
        profile = self.model_profiles.get(model_name, {})
        return profile.get('strengths', [])