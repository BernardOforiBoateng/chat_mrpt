#!/usr/bin/env python3
import sys

# Read the file
with open(sys.argv[1], 'r') as f:
    content = f.read()

# Comment out the reload line
content = content.replace(
    "                window.location.reload();",
    "                // window.location.reload(); // DISABLED FOR TESTING"
)

# Write the file back
with open(sys.argv[1], 'w') as f:
    f.write(content)

print("TPR verification reload DISABLED for testing!")