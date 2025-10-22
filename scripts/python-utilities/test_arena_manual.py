#!/usr/bin/env python3
"""
Manual test instructions for Arena routing with uploaded data.
This script provides step-by-step instructions and automated message testing.
"""

import requests
import json
import time
import sys

CLOUDFRONT_URL = "https://d225ar6c86586s.cloudfront.net"

def colored_print(text, color="default"):
    """Print with color for better readability."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "default": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['default']}")

def print_manual_steps():
    """Print manual testing steps."""
    colored_print("\n" + "="*60, "blue")
    colored_print("🧪 MANUAL ARENA ROUTING TEST WITH DATA", "blue")
    colored_print("="*60 + "\n", "blue")
    
    colored_print("📋 MANUAL STEPS:", "cyan")
    colored_print("\n1. Open CloudFront in your browser:", "yellow")
    colored_print(f"   {CLOUDFRONT_URL}", "default")
    
    colored_print("\n2. Upload test data:", "yellow")
    colored_print("   - Click 'Upload CSV' button", "default")
    colored_print("   - Select any CSV file with malaria data", "default")
    colored_print("   - Click 'Upload Shapefile' button", "default")
    colored_print("   - Select any shapefile (or skip if not available)", "default")
    
    colored_print("\n3. Open browser console (F12 > Console tab)", "yellow")
    colored_print("   - This will show Arena battle logs", "default")
    
    colored_print("\n4. Test these GENERAL KNOWLEDGE questions:", "yellow")
    colored_print("   (Should trigger Arena mode with model battles)", "default")
    
    test_questions = [
        "Who are you?",
        "What is malaria?",
        "Explain TPR",
        "How does PCA work?",
        "What causes malaria transmission?"
    ]
    
    for i, q in enumerate(test_questions, 1):
        colored_print(f"   {i}. {q}", "green")
    
    colored_print("\n5. Check browser console for each question:", "yellow")
    colored_print("   ✅ PASS if you see:", "green")
    colored_print("      - '=== INITIAL ARENA BATTLE STARTED ==='", "default")
    colored_print("      - 'Models: llama3.1:8b vs mistral:7b' (or similar)", "default")
    colored_print("      - Multiple model responses", "default")
    
    colored_print("   ❌ FAIL if you see:", "red")
    colored_print("      - No Arena battle logs", "default")
    colored_print("      - Direct OpenAI response", "default")
    colored_print("      - Tool execution messages", "default")
    
    colored_print("\n6. Test these DATA-SPECIFIC questions:", "yellow")
    colored_print("   (Should use OpenAI with tools, NOT Arena)", "default")
    
    data_questions = [
        "Analyze my data",
        "What is the TPR in my file?",
        "Plot the distribution of EVI",
        "Show me the data quality"
    ]
    
    for i, q in enumerate(data_questions, 1):
        colored_print(f"   {i}. {q}", "cyan")
    
    colored_print("\n7. For data questions, console should show:", "yellow")
    colored_print("   - Tool execution logs", "default")
    colored_print("   - NO Arena battle messages", "default")
    
    colored_print("\n" + "="*60, "magenta")
    colored_print("🎯 EXPECTED RESULTS:", "magenta")
    colored_print("="*60, "magenta")
    
    colored_print("\n✅ General questions → Arena mode (even WITH data uploaded)", "green")
    colored_print("✅ Data-specific questions → OpenAI tools", "green")
    colored_print("\n❌ If ALL questions go to OpenAI → Routing fix didn't work", "red")
    
    colored_print("\n" + "="*60, "blue")

def test_without_upload():
    """Test messages without data upload to verify basic Arena mode."""
    colored_print("\n🔍 QUICK TEST (without data upload):", "cyan")
    colored_print("Testing if Arena works in normal mode...\n", "yellow")
    
    test_message = "What is malaria?"
    
    response = requests.post(
        f"{CLOUDFRONT_URL}/send_message_streaming",
        json={'message': test_message},
        stream=True
    )
    
    has_arena = False
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if 'arena_mode' in line_str or 'model_a' in line_str or 'model_b' in line_str:
                has_arena = True
                break
    
    if has_arena:
        colored_print("✅ Arena mode is working in normal chat!", "green")
        colored_print("   Now test with uploaded data using manual steps above.", "yellow")
    else:
        colored_print("⚠️  Arena mode might not be working. Check AWS instances.", "red")

if __name__ == "__main__":
    try:
        # Print manual testing instructions
        print_manual_steps()
        
        # Do a quick test without upload
        colored_print("\nPress Enter to run a quick Arena test (or Ctrl+C to skip):", "cyan")
        try:
            input()
            test_without_upload()
        except KeyboardInterrupt:
            colored_print("\nSkipped quick test.", "yellow")
        
        colored_print("\n📝 Please perform the manual test steps above and report results.", "magenta")
        
    except Exception as e:
        colored_print(f"\n❌ Error: {e}", "red")
        sys.exit(1)