"""
Check if TPR data is present in the map HTML files
"""

import re

# Session IDs from the user's recent runs
sessions = {
    'Plateau': 'cc6a7674-4763-41bc-99e0-41ffdbf21b5a',
    'Nasarawa': 'b0b5de1b-c71a-4f25-90e2-b458b69c5ee5',
    'Kebbi': '7645bda3-52af-4e69-82e7-04bcacaa553b',
    'Benue': 'fa14700b-9ec9-4024-a3ca-256302509b19',
    'Ebonyi': 'c3dcaca7-8ff9-4169-8c1f-a06f45a228e8',
}

for state, session_id in sessions.items():
    map_file = f'/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/instance/uploads/{session_id}/tpr_distribution_map.html'

    try:
        with open(map_file, 'r') as f:
            html = f.read()

        # Look for the z data array
        z_pattern = r'"z":\[(.*?)\]'
        match = re.search(z_pattern, html)

        if match:
            z_values = match.group(1)
            values_list = z_values.split(',')

            # Count null vs non-null values
            null_count = z_values.count('null')
            total_values = len(values_list)
            non_null_count = total_values - null_count

            print(f"\n{state} ({session_id[:8]}...):")
            print(f"  Total values: {total_values}")
            print(f"  Non-null values: {non_null_count}")
            print(f"  Null values: {null_count}")

            # Show first 10 values
            first_10 = values_list[:10]
            print(f"  First 10 values: {first_10}")

            # Check if all values are null
            if non_null_count == 0:
                print(f"  ⚠️ WARNING: All z values are null!")
            elif non_null_count < 10:
                print(f"  ⚠️ WARNING: Very few non-null values!")
        else:
            print(f"\n{state}: No z data found!")
    except FileNotFoundError:
        print(f"\n{state}: File not found locally")
    except Exception as e:
        print(f"\n{state}: Error - {e}")