import sys
import re
import os

# Ensure repo root is importable
sys.path.insert(0, os.getcwd())

print("[SMOKE] Phase 1 quick checks")

try:
    from app.core.column_resolver import ColumnResolver
    import pandas as pd
    print("[OK] Imported ColumnResolver")

    df = pd.DataFrame({
        'WardName': ['Alpha','Beta'],
        'TPR': [12.3, 45.6],
        'Rainfall': [100, 200],
        'composite_score': [0.7, 0.5],
    })
    resolver = ColumnResolver(df)
    print("[OK] Resolver canonical map:", resolver.canonical_map)
    print("[OK] resolve('tpr') ->", resolver.resolve('tpr'))
    print("[OK] resolve('test positivity rate') ->", resolver.resolve('test positivity rate'))
    print("[OK] resolve('ward_name') ->", resolver.resolve('ward_name'))
    print("[OK] df_norm columns:", list(resolver.df_norm.columns))
except Exception as e:
    print("[FAIL] ColumnResolver:", e)
    sys.exit(1)

try:
    from app.data_analysis_v3.core.data_validator import DataValidator
    tests = [
        '1. Ward A',
        '1. WardName 1',
        'Top wards: WardName 10',
        'WardName 2 is highest',
        'Gwagwalada',
    ]
    for t in tests:
        valid, issues = DataValidator.validate_output(t)
        print("[OK] Validator on '{0}' -> issues: {1}".format(t, issues))
except Exception as e:
    print("[FAIL] DataValidator:", e)
    sys.exit(1)

try:
    from app.data_analysis_v3.prompts.system_prompt import MAIN_SYSTEM_PROMPT
    print("[OK] Prompt MUST clause present:", ('MUST use the tool' in MAIN_SYSTEM_PROMPT))
    print("[OK] TPR->Risk synonyms present:", ('vulnerability' in MAIN_SYSTEM_PROMPT and 'rank wards' in MAIN_SYSTEM_PROMPT))
except Exception as e:
    print("[FAIL] System prompt:", e)
    sys.exit(1)

print("[SMOKE] Completed")
