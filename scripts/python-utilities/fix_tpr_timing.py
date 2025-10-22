#!/usr/bin/env python3
import re
import sys

# Read the file
with open(sys.argv[1], 'r') as f:
    content = f.read()

# Replace the immediate call with a delayed call
content = content.replace(
    "            // CRITICAL: Verify TPR workflow is active in backend session (multi-worker fix)\n            this.verifyTPRSessionState();",
    """            // CRITICAL: Verify TPR workflow is active in backend session (multi-worker fix)
            // Add delay to allow Redis session save to complete
            setTimeout(() => {
                this.verifyTPRSessionState();
            }, 2000); // 2 second delay"""
)

# Write the file back
with open(sys.argv[1], 'w') as f:
    f.write(content)

print("TPR timing fix applied successfully!")