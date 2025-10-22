#!/usr/bin/env python3
"""
Comparison: How column sanitization makes agent code generation easier
"""

print("🤖 Agent Code Generation Comparison")
print("=" * 60)

# BEFORE: With original column names
print("\n❌ BEFORE (Original Column Names):")
print("-" * 40)
print("Agent tries to generate code like this:\n")

before_code = '''
# This often FAILS due to special characters
try:
    # Calculate total tests - agent struggles with column names
    total_tests = df["Persons presenting with fever & tested by RDT <5yrs"] + \\
                  df["Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)"] + \\
                  df["Persons presenting with fever & tested by RDT Preg Women (PW)"]
    
    # Group by facility - complex escaping needed
    facility_totals = df.groupby("HealthFacility")[
        ["Persons presenting with fever & tested by RDT <5yrs",
         "Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)"]
    ].sum()
except KeyError as e:
    print(f"Column not found: {e}")
    # Agent often gives up here!
'''

print(before_code)

print("\nCommon Issues:")
print("• Special characters (<, ≥) break pandas operations")
print("• Spaces require exact matching")
print("• Long names cause line wrapping issues")
print("• Agent can't reliably reference these columns")
print("• Copy-paste errors are common")

# AFTER: With sanitized column names
print("\n✅ AFTER (Sanitized Column Names):")
print("-" * 40)
print("Agent generates clean, working code:\n")

after_code = '''
# This WORKS reliably!
# Calculate total tests - simple column names
rdt_cols = [col for col in df.columns if 'rdt' in col and 'tested' in col]
total_tests = df[rdt_cols].sum(axis=1)

# Group by facility - clean and simple
facility_totals = df.groupby('healthfacility')[rdt_cols].sum()
facility_totals['total'] = facility_totals.sum(axis=1)
top_10 = facility_totals.nlargest(10, 'total')

# The agent can also use semantic names
children_tested = df['persons_presenting_with_fever_and_tested_by_rdt_7'].sum()
adults_tested = df['persons_presenting_with_fever_and_tested_by_rdt_8'].sum()

print(f"Children tested: {children_tested:,}")
print(f"Adults tested: {adults_tested:,}")
'''

print(after_code)

print("\nBenefits:")
print("• ✅ No special character issues")
print("• ✅ Simple pattern matching (if 'rdt' in col)")
print("• ✅ Shorter, readable code")
print("• ✅ Agent can reliably generate working code")
print("• ✅ No escaping or quoting issues")

# Real-world example
print("\n" + "=" * 60)
print("📊 Real-World Query Comparison")
print("=" * 60)

print('\nUser asks: "Show me top 10 facilities by total testing volume"\n')

print("❌ Current Agent Response (FAILS):")
print("-" * 40)
print("""
The agent generates:
df.groupby("HealthFacility")[
    "Persons presenting with fever & tested by RDT <5yrs",
    "Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)"
].sum()

Result: KeyError or "difficulties accessing columns"
""")

print("✅ With Sanitized Columns (WORKS):")
print("-" * 40)
print("""
The agent generates:
# Get all testing columns
test_cols = [c for c in df.columns if 'tested' in c]

# Calculate totals per facility
facility_totals = df.groupby('healthfacility')[test_cols].sum()
facility_totals['total_tests'] = facility_totals.sum(axis=1)

# Get top 10
top_10 = facility_totals.nlargest(10, 'total_tests')
for facility, row in top_10.iterrows():
    print(f"{facility}: {row['total_tests']:,.0f} tests")

Result: Successfully returns top 10 facilities with counts!
""")

# Performance comparison
print("\n⚡ Performance Benefits:")
print("-" * 40)

import sys
original_col = "Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)"
sanitized_col = "persons_presenting_with_fever_and_tested_by_rdt_8"

print(f"Original column name size: {sys.getsizeof(original_col)} bytes")
print(f"Sanitized column name size: {sys.getsizeof(sanitized_col)} bytes")
print(f"Character count: {len(original_col)} vs {len(sanitized_col)}")

print("\n🎯 Key Insight:")
print("-" * 40)
print("""
The agent (GPT-4) is trained on millions of Python/Pandas examples
that use simple column names like 'age', 'income', 'test_score'.

It struggles with our complex medical column names because:
1. They're unlike its training data
2. Special characters need careful handling
3. The tokenizer splits them unpredictably

By sanitizing to standard Python identifiers, we align with
what the model knows best!
""")