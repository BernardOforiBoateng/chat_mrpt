"""
Urban Percentage Analysis and Visualization Script
Processes results from multi-method GEE urban percentage calculations
Author: Bernard Ofori Boateng
Date: November 2024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for professional plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class UrbanPercentageAnalyzer:
    """Analyze and visualize urban percentage results from multiple methods"""
    
    def __init__(self, csv_path):
        """Initialize with path to GEE export CSV"""
        self.df = pd.read_csv(csv_path)
        self.methods = ['NDBI', 'Africapolis', 'GHSL', 'EBBI']
        self.urban_threshold = 50  # Default threshold for urban classification
        
    def clean_data(self):
        """Clean and prepare the data"""
        # Ensure numeric columns
        for method in self.methods:
            col_name = f'{method}_urban_percent'
            if col_name in self.df.columns:
                self.df[col_name] = pd.to_numeric(self.df[col_name], errors='coerce')
        
        # Remove any rows with all NaN values
        urban_cols = [f'{m}_urban_percent' for m in self.methods if f'{m}_urban_percent' in self.df.columns]
        self.df = self.df.dropna(subset=urban_cols, how='all')
        
        return self.df
    
    def calculate_statistics(self):
        """Calculate summary statistics across methods"""
        urban_cols = [f'{m}_urban_percent' for m in self.methods if f'{m}_urban_percent' in self.df.columns]
        
        # Calculate mean, std, min, max for each ward
        self.df['mean_urban_percent'] = self.df[urban_cols].mean(axis=1)
        self.df['std_urban_percent'] = self.df[urban_cols].std(axis=1)
        self.df['min_urban_percent'] = self.df[urban_cols].min(axis=1)
        self.df['max_urban_percent'] = self.df[urban_cols].max(axis=1)
        self.df['range_urban_percent'] = self.df['max_urban_percent'] - self.df['min_urban_percent']
        
        # Classify based on mean
        self.df['classification'] = self.df['mean_urban_percent'].apply(self.classify_urbanicity)
        
        # Agreement score (how consistent are the methods)
        self.df['agreement_score'] = 1 - (self.df['std_urban_percent'] / self.df['mean_urban_percent'].replace(0, np.nan))
        
        return self.df
    
    def classify_urbanicity(self, percentage):
        """Classify urbanicity based on percentage"""
        if pd.isna(percentage):
            return 'No Data'
        elif percentage >= 50:
            return 'Urban'
        elif percentage >= 30:
            return 'Peri-urban'
        elif percentage >= 10:
            return 'Rural with Development'
        else:
            return 'Rural'
    
    def identify_suspicious_wards(self, suspicious_list=None):
        """Identify and flag suspicious wards based on consistent rural classification"""
        # Wards that are consistently rural across all methods
        urban_cols = [f'{m}_urban_percent' for m in self.methods if f'{m}_urban_percent' in self.df.columns]
        
        # Flag wards where ALL methods show < 50% urban
        self.df['consistently_rural'] = self.df[urban_cols].apply(
            lambda row: all(row < self.urban_threshold), axis=1
        )
        
        # If suspicious list provided, mark them
        if suspicious_list:
            self.df['is_suspicious'] = self.df['ward_name'].isin(suspicious_list)
        
        return self.df[self.df['consistently_rural']]
    
    def create_comparison_plot(self, save_path=None):
        """Create bar plot comparing methods for each ward"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Prepare data for plotting
        urban_cols = [f'{m}_urban_percent' for m in self.methods if f'{m}_urban_percent' in self.df.columns]
        plot_df = self.df[['ward_name'] + urban_cols].set_index('ward_name')
        plot_df.columns = [col.replace('_urban_percent', '') for col in plot_df.columns]
        
        # Plot 1: Bar plot comparison
        ax1 = axes[0]
        plot_df.head(20).plot(kind='bar', ax=ax1, width=0.8)
        ax1.set_title('Urban Percentage by Ward - Multiple Methods Comparison', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Ward Name', fontsize=12)
        ax1.set_ylabel('Urban Percentage (%)', fontsize=12)
        ax1.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Urban Threshold (50%)')
        ax1.legend(title='Method', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Plot 2: Scatter plot showing agreement
        ax2 = axes[1]
        if 'mean_urban_percent' in self.df.columns and 'std_urban_percent' in self.df.columns:
            scatter = ax2.scatter(self.df['mean_urban_percent'], 
                                 self.df['std_urban_percent'],
                                 c=self.df['mean_urban_percent'],
                                 cmap='RdYlGn_r', s=100, alpha=0.6, edgecolors='black')
            ax2.set_title('Method Agreement Analysis', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Mean Urban Percentage (%)', fontsize=12)
            ax2.set_ylabel('Standard Deviation (Method Disagreement)', fontsize=12)
            ax2.axvline(x=50, color='red', linestyle='--', alpha=0.5)
            ax2.grid(True, alpha=0.3)
            plt.colorbar(scatter, ax=ax2, label='Mean Urban %')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def create_heatmap(self, save_path=None):
        """Create heatmap of urban percentages"""
        urban_cols = [f'{m}_urban_percent' for m in self.methods if f'{m}_urban_percent' in self.df.columns]
        
        # Prepare data for heatmap
        heatmap_data = self.df[['ward_name'] + urban_cols].set_index('ward_name')
        heatmap_data.columns = [col.replace('_urban_percent', '') for col in heatmap_data.columns]
        
        # Create heatmap
        plt.figure(figsize=(10, len(self.df) * 0.3))
        sns.heatmap(heatmap_data.head(30), 
                   annot=True, fmt='.1f', 
                   cmap='RdYlGn_r', 
                   center=50, 
                   cbar_kws={'label': 'Urban Percentage (%)'},
                   linewidths=0.5)
        plt.title('Urban Percentage Heatmap - All Methods', fontsize=14, fontweight='bold')
        plt.xlabel('Method', fontsize=12)
        plt.ylabel('Ward Name', fontsize=12)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, output_path='urban_analysis_report.txt'):
        """Generate text report of findings"""
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("URBAN PERCENTAGE ANALYSIS REPORT\n")
            f.write("Multi-Method Validation of Ward Urbanicity Classifications\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total wards analyzed: {len(self.df)}\n")
            
            if 'classification' in self.df.columns:
                class_counts = self.df['classification'].value_counts()
                f.write("\nClassification Summary:\n")
                for cls, count in class_counts.items():
                    f.write(f"  {cls}: {count} wards ({count/len(self.df)*100:.1f}%)\n")
            
            # Consistently rural wards
            if 'consistently_rural' in self.df.columns:
                rural_wards = self.df[self.df['consistently_rural']]
                f.write(f"\nConsistently Rural Wards (all methods < {self.urban_threshold}%): {len(rural_wards)}\n")
                
                if len(rural_wards) > 0:
                    f.write("\nDetailed Rural Ward Analysis:\n")
                    f.write("-" * 40 + "\n")
                    for _, ward in rural_wards.iterrows():
                        f.write(f"\nWard: {ward['ward_name']}\n")
                        for method in self.methods:
                            col = f'{method}_urban_percent'
                            if col in ward and not pd.isna(ward[col]):
                                f.write(f"  {method}: {ward[col]:.2f}%\n")
                        if 'mean_urban_percent' in ward:
                            f.write(f"  Average: {ward['mean_urban_percent']:.2f}%\n")
            
            # Method agreement analysis
            f.write("\n" + "=" * 80 + "\n")
            f.write("METHOD AGREEMENT ANALYSIS\n")
            f.write("-" * 40 + "\n")
            
            if 'agreement_score' in self.df.columns:
                high_agreement = self.df[self.df['agreement_score'] > 0.8]
                low_agreement = self.df[self.df['agreement_score'] < 0.5]
                
                f.write(f"Wards with high method agreement (>80%): {len(high_agreement)}\n")
                f.write(f"Wards with low method agreement (<50%): {len(low_agreement)}\n")
                
                if len(low_agreement) > 0:
                    f.write("\nWards requiring further investigation (low agreement):\n")
                    for _, ward in low_agreement.head(10).iterrows():
                        f.write(f"  - {ward['ward_name']} (Agreement: {ward['agreement_score']:.2f})\n")
            
            # Recommendations
            f.write("\n" + "=" * 80 + "\n")
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            f.write("1. Wards consistently classified as rural across all methods should be\n")
            f.write("   flagged for review if selected for urban-targeted interventions.\n")
            f.write("2. Wards with low method agreement require additional field validation.\n")
            f.write("3. Consider using the mean of all methods for final classification.\n")
            f.write("4. Document any local knowledge that might explain classification discrepancies.\n")
            
        print(f"Report generated: {output_path}")
        return output_path
    
    def export_summary_table(self, output_path='summary_table.csv'):
        """Export summary table for presentation"""
        summary_cols = ['ward_name', 'mean_urban_percent', 'classification', 'consistently_rural']
        
        # Add individual method columns
        for method in self.methods:
            col = f'{method}_urban_percent'
            if col in self.df.columns:
                summary_cols.append(col)
        
        # Add agreement score if available
        if 'agreement_score' in self.df.columns:
            summary_cols.append('agreement_score')
        
        # Filter and export
        summary_df = self.df[summary_cols].copy()
        summary_df = summary_df.sort_values('mean_urban_percent')
        summary_df.to_csv(output_path, index=False)
        
        print(f"Summary table exported: {output_path}")
        return summary_df


def main():
    """Main execution function"""
    # Path to your GEE export CSV
    csv_path = 'Urban_Percentage_Multi_Methods.csv'
    
    # Initialize analyzer
    print("Initializing Urban Percentage Analyzer...")
    analyzer = UrbanPercentageAnalyzer(csv_path)
    
    # Clean data
    print("Cleaning data...")
    analyzer.clean_data()
    
    # Calculate statistics
    print("Calculating statistics...")
    analyzer.calculate_statistics()
    
    # Identify suspicious wards
    print("Identifying consistently rural wards...")
    rural_wards = analyzer.identify_suspicious_wards()
    print(f"Found {len(rural_wards)} consistently rural wards")
    
    # Create visualizations
    print("Creating visualizations...")
    analyzer.create_comparison_plot('urban_comparison_plot.png')
    analyzer.create_heatmap('urban_heatmap.png')
    
    # Generate report
    print("Generating report...")
    analyzer.generate_report()
    
    # Export summary table
    print("Exporting summary table...")
    summary = analyzer.export_summary_table()
    
    print("\nAnalysis complete!")
    print(f"Total wards analyzed: {len(analyzer.df)}")
    print(f"Consistently rural wards: {len(rural_wards)}")
    
    # Display top rural wards
    if len(rural_wards) > 0:
        print("\nTop 5 most rural wards (lowest urban %):")
        print(summary[['ward_name', 'mean_urban_percent', 'classification']].head(5).to_string(index=False))


if __name__ == "__main__":
    # Check if CSV exists
    csv_path = Path('Urban_Percentage_Multi_Methods.csv')
    if csv_path.exists():
        main()
    else:
        print(f"CSV file not found: {csv_path}")
        print("Please run the Google Earth Engine script first to generate the CSV export.")
        print("\nCreating sample data for demonstration...")
        
        # Create sample data for testing
        sample_data = {
            'ward_name': [f'Ward_{i}' for i in range(1, 21)],
            'NDBI_urban_percent': np.random.uniform(5, 95, 20),
            'Africapolis_urban_percent': np.random.uniform(5, 95, 20),
            'GHSL_urban_percent': np.random.uniform(5, 95, 20),
            'EBBI_urban_percent': np.random.uniform(5, 95, 20)
        }
        sample_df = pd.DataFrame(sample_data)
        sample_df.to_csv('sample_urban_data.csv', index=False)
        print("Sample data created: sample_urban_data.csv")
        print("You can test the script with this sample data.")