"""
Statistical tests for PCA suitability.
Implements Kaiser-Meyer-Olkin (KMO) test and Bartlett's test of sphericity.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2
import logging

logger = logging.getLogger(__name__)

class PCAStatisticalTests:
    """Class for performing statistical tests to assess PCA suitability."""
    
    @staticmethod
    def calculate_kmo(data):
        """
        Calculate Kaiser-Meyer-Olkin (KMO) measure of sampling adequacy.
        
        KMO values interpretation:
        - >= 0.9: Marvelous
        - 0.8-0.89: Meritorious  
        - 0.7-0.79: Middling
        - 0.6-0.69: Mediocre
        - 0.5-0.59: Miserable
        - < 0.5: Unacceptable for PCA
        
        Args:
            data: numpy array or pandas DataFrame of standardized data
            
        Returns:
            dict with 'kmo_overall' (float) and 'kmo_per_variable' (array)
        """
        try:
            if isinstance(data, pd.DataFrame):
                data = data.values
            
            n_vars = data.shape[1]
            
            # Calculate correlation matrix
            corr_matrix = np.corrcoef(data.T)
            
            # Calculate partial correlation matrix
            try:
                inv_corr = np.linalg.pinv(corr_matrix)
                partial_corr = -inv_corr / np.sqrt(np.outer(np.diag(inv_corr), np.diag(inv_corr)))
                np.fill_diagonal(partial_corr, 0)
            except:
                logger.warning("Could not compute partial correlations, using fallback method")
                partial_corr = np.zeros_like(corr_matrix)
            
            # Calculate KMO for each variable
            kmo_per_variable = np.zeros(n_vars)
            
            for i in range(n_vars):
                # Sum of squared correlations
                sum_corr_sq = np.sum(corr_matrix[i, :] ** 2) - 1  # Exclude diagonal
                # Sum of squared partial correlations
                sum_partial_sq = np.sum(partial_corr[i, :] ** 2)
                
                if (sum_corr_sq + sum_partial_sq) > 0:
                    kmo_per_variable[i] = sum_corr_sq / (sum_corr_sq + sum_partial_sq)
                else:
                    kmo_per_variable[i] = 0
            
            # Calculate overall KMO
            # Sum of all squared correlations (excluding diagonal)
            sum_corr_sq_total = np.sum(corr_matrix ** 2) - n_vars
            # Sum of all squared partial correlations
            sum_partial_sq_total = np.sum(partial_corr ** 2)
            
            if (sum_corr_sq_total + sum_partial_sq_total) > 0:
                kmo_overall = sum_corr_sq_total / (sum_corr_sq_total + sum_partial_sq_total)
            else:
                kmo_overall = 0
            
            return {
                'kmo_overall': kmo_overall,
                'kmo_per_variable': kmo_per_variable
            }
            
        except Exception as e:
            logger.error(f"Error calculating KMO: {e}")
            return {
                'kmo_overall': 0,
                'kmo_per_variable': np.array([])
            }
    
    @staticmethod
    def bartletts_test(data):
        """
        Perform Bartlett's test of sphericity.
        
        Tests the hypothesis that the correlation matrix is an identity matrix,
        which would indicate that variables are unrelated and unsuitable for PCA.
        
        Args:
            data: numpy array or pandas DataFrame of standardized data
            
        Returns:
            dict with 'statistic' (float), 'p_value' (float), and 'suitable' (bool)
        """
        try:
            if isinstance(data, pd.DataFrame):
                data = data.values
            
            n_samples, n_vars = data.shape
            
            # Calculate correlation matrix
            corr_matrix = np.corrcoef(data.T)
            
            # Calculate determinant of correlation matrix
            det_corr = np.linalg.det(corr_matrix)
            
            if det_corr <= 0:
                logger.warning("Correlation matrix is singular or negative definite")
                return {
                    'statistic': 0,
                    'p_value': 1.0,
                    'suitable': False
                }
            
            # Bartlett's test statistic
            # Formula: -[(n-1) - (2p+5)/6] * ln(det(R))
            # where n = number of observations, p = number of variables
            statistic = -((n_samples - 1) - (2 * n_vars + 5) / 6) * np.log(det_corr)
            
            # Degrees of freedom
            df = n_vars * (n_vars - 1) / 2
            
            # Calculate p-value
            p_value = 1 - chi2.cdf(statistic, df)
            
            # Test is significant if p < 0.05 (reject null hypothesis of identity matrix)
            suitable = p_value < 0.05
            
            return {
                'statistic': statistic,
                'p_value': p_value,
                'suitable': suitable,
                'degrees_of_freedom': df
            }
            
        except Exception as e:
            logger.error(f"Error in Bartlett's test: {e}")
            return {
                'statistic': 0,
                'p_value': 1.0,
                'suitable': False,
                'degrees_of_freedom': 0
            }
    
    @staticmethod
    def check_pca_suitability(data, kmo_threshold=0.5):
        """
        Check if data is suitable for PCA using both KMO and Bartlett's tests.
        
        Args:
            data: numpy array or pandas DataFrame of standardized data
            kmo_threshold: minimum KMO value for PCA suitability (default: 0.5)
            
        Returns:
            dict with test results and overall suitability assessment
        """
        try:
            print("\n" + "="*60)
            print("🔍 PCA STATISTICAL TESTS STARTING")
            print("="*60)
            
            # Get data shape info
            if isinstance(data, pd.DataFrame):
                n_samples, n_vars = data.shape
                print(f"📊 Data shape: {n_samples} samples × {n_vars} variables")
            else:
                n_samples, n_vars = data.shape if len(data.shape) == 2 else (len(data), 1)
                print(f"📊 Data shape: {n_samples} samples × {n_vars} variables")
            
            # Run KMO test
            print("\n📈 Running Kaiser-Meyer-Olkin (KMO) test...")
            kmo_results = PCAStatisticalTests.calculate_kmo(data)
            kmo_value = kmo_results['kmo_overall']
            kmo_suitable = kmo_value >= kmo_threshold
            print(f"   KMO value: {kmo_value:.4f}")
            print(f"   Threshold: {kmo_threshold}")
            print(f"   Result: {'✅ PASS' if kmo_suitable else '❌ FAIL'}")
            
            # Run Bartlett's test
            print("\n📊 Running Bartlett's test of sphericity...")
            bartlett_results = PCAStatisticalTests.bartletts_test(data)
            bartlett_suitable = bartlett_results['suitable']
            print(f"   Test statistic: {bartlett_results['statistic']:.2f}")
            print(f"   P-value: {bartlett_results['p_value']:.4e}")
            print(f"   Result: {'✅ PASS (p < 0.05)' if bartlett_suitable else '❌ FAIL (p >= 0.05)'}")
            
            # Both tests should pass for PCA to be suitable
            overall_suitable = kmo_suitable and bartlett_suitable
            
            print("\n" + "-"*60)
            print("📋 OVERALL ASSESSMENT:")
            print("-"*60)
            
            # Prepare interpretation message
            if kmo_value >= 0.9:
                kmo_interpretation = "Marvelous - excellent for PCA"
            elif kmo_value >= 0.8:
                kmo_interpretation = "Meritorious - good for PCA"
            elif kmo_value >= 0.7:
                kmo_interpretation = "Middling - adequate for PCA"
            elif kmo_value >= 0.6:
                kmo_interpretation = "Mediocre - acceptable for PCA"
            elif kmo_value >= 0.5:
                kmo_interpretation = "Miserable - barely acceptable for PCA"
            else:
                kmo_interpretation = "Unacceptable - not suitable for PCA"
            
            # Create detailed message
            messages = []
            
            if not kmo_suitable:
                messages.append(f"KMO test failed: {kmo_value:.3f} < {kmo_threshold} (threshold)")
            else:
                messages.append(f"KMO test passed: {kmo_value:.3f} - {kmo_interpretation}")
            
            if not bartlett_suitable:
                messages.append(f"Bartlett's test failed: p-value = {bartlett_results['p_value']:.4f} (not significant)")
            else:
                messages.append(f"Bartlett's test passed: p-value = {bartlett_results['p_value']:.4e} (significant)")
            
            if overall_suitable:
                summary = "Data is suitable for PCA analysis"
                print(f"✅ {summary}")
                print(f"   KMO: {kmo_interpretation}")
                print(f"   Both statistical tests passed")
                print("\n🎯 DECISION: Proceeding with PCA analysis")
            else:
                summary = "Data is not suitable for PCA. Using composite analysis only."
                print(f"❌ {summary}")
                print(f"   KMO: {kmo_interpretation}")
                if not kmo_suitable:
                    print(f"   KMO test failed ({kmo_value:.3f} < {kmo_threshold})")
                if not bartlett_suitable:
                    print(f"   Bartlett's test failed (p={bartlett_results['p_value']:.3f} >= 0.05)")
                print("\n⚠️ DECISION: Skipping PCA, using composite analysis only")
            
            print("="*60 + "\n")
            
            return {
                'suitable': overall_suitable,
                'kmo_value': kmo_value,
                'kmo_threshold': kmo_threshold,
                'kmo_interpretation': kmo_interpretation,
                'bartlett_statistic': bartlett_results['statistic'],
                'bartlett_p_value': bartlett_results['p_value'],
                'messages': messages,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error checking PCA suitability: {e}")
            return {
                'suitable': False,
                'kmo_value': 0,
                'kmo_threshold': kmo_threshold,
                'messages': [f"Error running statistical tests: {str(e)}"],
                'summary': "Could not assess PCA suitability. Using composite analysis only."
            }