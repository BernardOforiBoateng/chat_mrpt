#!/usr/bin/env python3
"""
Proof of concept: Column sanitization for better agent performance
"""

import pandas as pd
import re
import json

class SmartColumnHandler:
    """
    Industry-standard column handling:
    1. Sanitize column names for Python/Pandas compatibility
    2. Preserve original names for display
    3. Auto-detect column purposes
    """
    
    def __init__(self):
        self.column_mapping = {}
        self.reverse_mapping = {}
        self.semantic_mapping = {}
    
    def sanitize_column_name(self, col, index=None):
        """
        Convert any column name to a Python-friendly identifier.
        Based on industry best practices from Spark, BigQuery, dbt.
        """
        # Step 1: Handle common encoding issues
        col = str(col)
        
        # Common replacements
        replacements = {
            '≥': 'gte',  # Greater than or equal
            '≤': 'lte',  # Less than or equal  
            '<': 'lt',   # Less than
            '>': 'gt',   # Greater than
            '&': 'and',
            '|': 'or',
            '%': 'pct',
            '#': 'num',
            '@': 'at',
            '$': 'dollar',
            '€': 'euro',
            '£': 'pound',
        }
        
        for old, new in replacements.items():
            col = col.replace(old, f'_{new}_')
        
        # Step 2: Remove non-alphanumeric characters
        col = re.sub(r'[^\w\s]', '', col)
        
        # Step 3: Replace spaces with underscores
        col = re.sub(r'\s+', '_', col)
        
        # Step 4: Remove consecutive underscores
        col = re.sub(r'_+', '_', col)
        
        # Step 5: Convert to lowercase
        col = col.lower()
        
        # Step 6: Ensure it starts with a letter
        if col and not col[0].isalpha():
            col = f'col_{col}'
        
        # Step 7: Truncate if too long
        if len(col) > 50:
            col = col[:47] + f'_{index or 0}'
        
        # Step 8: Handle empty result
        if not col:
            col = f'column_{index or 0}'
        
        return col.strip('_')
    
    def detect_semantic_type(self, col_name, df_column):
        """
        Auto-detect what kind of data this column contains.
        Useful for TPR and malaria data.
        """
        col_lower = col_name.lower()
        
        # TPR-specific detections
        if 'rdt' in col_lower:
            if 'positive' in col_lower:
                if '<5' in col_lower or 'under 5' in col_lower:
                    return 'rdt_positive_children'
                elif '≥5' in col_lower or 'over 5' in col_lower:
                    return 'rdt_positive_adults'
                elif 'preg' in col_lower or 'pw' in col_lower:
                    return 'rdt_positive_pregnant'
            else:
                if '<5' in col_lower or 'under 5' in col_lower:
                    return 'rdt_tested_children'
                elif '≥5' in col_lower or 'over 5' in col_lower:
                    return 'rdt_tested_adults'
                elif 'preg' in col_lower or 'pw' in col_lower:
                    return 'rdt_tested_pregnant'
        
        elif 'microscopy' in col_lower:
            if 'positive' in col_lower:
                if '<5' in col_lower:
                    return 'microscopy_positive_children'
                elif '≥5' in col_lower:
                    return 'microscopy_positive_adults'
            else:
                if '<5' in col_lower:
                    return 'microscopy_tested_children'
                elif '≥5' in col_lower:
                    return 'microscopy_tested_adults'
        
        elif 'facility' in col_lower or 'health' in col_lower:
            return 'health_facility'
        
        elif 'ward' in col_lower:
            return 'ward_name'
        
        elif 'lga' in col_lower:
            return 'lga_name'
        
        elif 'state' in col_lower:
            return 'state_name'
        
        elif 'llin' in col_lower:
            if '<5' in col_lower or 'child' in col_lower:
                return 'llin_children'
            elif 'preg' in col_lower or 'pw' in col_lower:
                return 'llin_pregnant'
        
        return None
    
    def process_dataframe(self, df):
        """
        Process a DataFrame to make it agent-friendly.
        """
        original_columns = df.columns.tolist()
        new_columns = []
        
        print("🔄 Processing DataFrame columns...")
        print("=" * 60)
        
        for i, col in enumerate(original_columns):
            # Create safe name
            safe_name = self.sanitize_column_name(col, i)
            
            # Ensure unique
            if safe_name in new_columns:
                counter = 1
                while f"{safe_name}_{counter}" in new_columns:
                    counter += 1
                safe_name = f"{safe_name}_{counter}"
            
            new_columns.append(safe_name)
            
            # Store mappings
            self.column_mapping[safe_name] = col
            self.reverse_mapping[col] = safe_name
            
            # Detect semantic type
            semantic = self.detect_semantic_type(col, df[col])
            if semantic:
                self.semantic_mapping[semantic] = safe_name
            
            # Show the transformation
            if col != safe_name:
                print(f"✓ '{col[:40]}{'...' if len(col) > 40 else ''}'")
                print(f"  → '{safe_name}'")
                if semantic:
                    print(f"  📊 Detected as: {semantic}")
                print()
        
        # Apply new column names
        df_clean = df.copy()
        df_clean.columns = new_columns
        
        # Store metadata
        df_clean.attrs['original_columns'] = original_columns
        df_clean.attrs['column_mapping'] = self.column_mapping
        df_clean.attrs['semantic_mapping'] = self.semantic_mapping
        
        return df_clean
    
    def generate_agent_context(self, df):
        """
        Generate context to help the agent understand the columns.
        """
        context = {
            "instructions": "Use the sanitized column names in all your code. They are Python-friendly and won't cause errors.",
            "column_reference": [],
            "semantic_groups": {
                "testing_columns": [],
                "positive_columns": [],
                "location_columns": [],
                "demographic_columns": []
            }
        }
        
        for safe_name, original in self.column_mapping.items():
            # Add to reference
            context["column_reference"].append({
                "use_this": safe_name,
                "original_name": original,
                "sample_values": df[safe_name].dropna().head(3).tolist() if safe_name in df.columns else []
            })
            
            # Categorize
            if 'test' in safe_name:
                context["semantic_groups"]["testing_columns"].append(safe_name)
            if 'positive' in safe_name:
                context["semantic_groups"]["positive_columns"].append(safe_name)
            if any(loc in safe_name for loc in ['ward', 'lga', 'state', 'facility']):
                context["semantic_groups"]["location_columns"].append(safe_name)
        
        return context

def test_with_real_data():
    """Test with actual TPR data columns."""
    
    # Read the TPR data
    df = pd.read_csv('www/adamawa_tpr_cleaned.csv')
    
    print("📊 Original DataFrame")
    print(f"Shape: {df.shape}")
    print(f"Columns: {len(df.columns)}")
    print("\nFirst 5 original column names:")
    for col in df.columns[:5]:
        print(f"  • {col}")
    
    print("\n" + "=" * 60)
    
    # Process with SmartColumnHandler
    handler = SmartColumnHandler()
    df_clean = handler.process_dataframe(df)
    
    print("✅ Processed DataFrame")
    print(f"Shape: {df_clean.shape}")
    print("\nFirst 5 sanitized column names:")
    for col in df_clean.columns[:5]:
        print(f"  • {col}")
    
    # Test semantic detection
    print("\n📊 Semantic Detection Results:")
    for semantic_type, column in handler.semantic_mapping.items():
        print(f"  {semantic_type}: '{column}'")
    
    # Generate agent context
    context = handler.generate_agent_context(df_clean)
    
    print("\n🤖 Agent Context Generated:")
    print(f"  Testing columns: {len(context['semantic_groups']['testing_columns'])}")
    print(f"  Positive columns: {len(context['semantic_groups']['positive_columns'])}")
    print(f"  Location columns: {len(context['semantic_groups']['location_columns'])}")
    
    # Test that we can now easily work with the data
    print("\n🧪 Testing Easy Calculations:")
    
    # Sum all RDT tests (would have failed before due to special chars)
    rdt_columns = [col for col in df_clean.columns if 'rdt' in col and 'tested' in col]
    if rdt_columns:
        print(f"\nRDT testing columns found: {len(rdt_columns)}")
        for col in rdt_columns[:3]:
            print(f"  • {col}")
        
        # This would work now without special character issues!
        total_rdt_tests = df_clean[rdt_columns].sum().sum()
        print(f"\nTotal RDT tests: {total_rdt_tests:,.0f}")
    
    # Top facilities by total tests (this calculation would work now!)
    if 'health_facility' in handler.semantic_mapping.values():
        facility_col = list(handler.semantic_mapping.values())[list(handler.semantic_mapping.keys()).index('health_facility')] if 'health_facility' in handler.semantic_mapping else df_clean.columns[4]
        
        test_cols = [col for col in df_clean.columns if 'persons_presenting' in col]
        if test_cols:
            df_clean['total_tests'] = df_clean[test_cols].sum(axis=1)
            top_facilities = df_clean.groupby(facility_col)['total_tests'].sum().nlargest(5)
            
            print(f"\n🏥 Top 5 Facilities by Total Tests:")
            for facility, count in top_facilities.items():
                # Get original name for display
                original_col = handler.column_mapping.get(facility_col, facility_col)
                print(f"  • {facility}: {count:,.0f} tests")
    
    return df_clean, handler

if __name__ == "__main__":
    print("🚀 Smart Column Handler - Proof of Concept")
    print("=" * 60)
    df_clean, handler = test_with_real_data()
    
    print("\n✨ Benefits:")
    print("1. ✅ No more special character errors")
    print("2. ✅ Agent can reference columns easily") 
    print("3. ✅ Works with any language/encoding")
    print("4. ✅ Original names preserved for display")
    print("5. ✅ Semantic understanding of data")
    
    print("\n📝 Next Steps:")
    print("1. Integrate into EncodingHandler")
    print("2. Update agent prompts to use sanitized names")
    print("3. Test with various international datasets")