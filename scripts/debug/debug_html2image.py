#!/usr/bin/env python3
"""Debug html2image with Chrome on AWS"""

from html2image import Html2Image
import os
import tempfile

# Test with Chrome path
chrome_path = '/usr/bin/google-chrome-stable'
print(f'Chrome exists: {os.path.exists(chrome_path)}')

# Try to create Html2Image
try:
    print("\n1. Creating Html2Image instance...")
    hti = Html2Image(
        browser_executable=chrome_path,
        custom_flags=['--no-sandbox', '--headless', '--disable-gpu', '--disable-dev-shm-usage', '--window-size=1920,1080']
    )
    print('✓ Html2Image created successfully!')

    # Try to take a screenshot
    print("\n2. Taking screenshot...")

    with tempfile.TemporaryDirectory() as tmpdir:
        hti = Html2Image(
            output_path=tmpdir,
            browser_executable=chrome_path,
            custom_flags=['--no-sandbox', '--headless', '--disable-gpu', '--disable-dev-shm-usage']
        )

        test_html = '<html><body style="background:linear-gradient(red,yellow,green);width:600px;height:400px;"><h1>Test TPR Map</h1></body></html>'

        files = hti.screenshot(html_str=test_html, save_as='test.png')
        print(f'Screenshot result: {files}')

        # Check if file exists
        output_file = os.path.join(tmpdir, 'test.png')
        print(f'Output exists: {os.path.exists(output_file)}')

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f'File size: {file_size} bytes')

            if file_size > 0:
                print("✓ Screenshot successfully captured!")
            else:
                print("✗ Screenshot file is empty")

except Exception as e:
    import traceback
    print(f'✗ Error: {e}')
    traceback.print_exc()

print("\n3. Checking Chrome process...")
import subprocess
result = subprocess.run([chrome_path, '--version'], capture_output=True, text=True)
print(f"Chrome version: {result.stdout}")