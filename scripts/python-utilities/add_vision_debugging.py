#!/usr/bin/env python3
"""Add debugging to vision explanation flow"""

import sys
import os

# Read the file
with open('app/services/universal_viz_explainer.py', 'r') as f:
    content = f.read()

# Add debug logging at key points
debug_additions = [
    # After line checking if LLM supports vision
    (
        "            if hasattr(self.llm_manager, 'generate_with_image'):",
        """            logger.info(f"🔍 DEBUG: LLM Manager type: {type(self.llm_manager)}")
            logger.info(f"🔍 DEBUG: Has generate_with_image: {hasattr(self.llm_manager, 'generate_with_image')}")
            if hasattr(self.llm_manager, 'generate_with_image'):"""
    ),
    # Before calling generate_with_image
    (
        "                explanation = self.llm_manager.generate_with_image(",
        """                logger.info(f"🎯 DEBUG: Calling generate_with_image with image URL: {img_url[:100]}...")
                logger.info(f"🎯 DEBUG: Prompt: {focused_instructions[:200]}...")
                explanation = self.llm_manager.generate_with_image("""
    ),
    # After getting explanation
    (
        "                )\n            else:",
        """                )
                logger.info(f"✅ DEBUG: Got vision explanation, length: {len(explanation)} chars")
                logger.info(f"✅ DEBUG: First 200 chars: {explanation[:200]}")
            else:"""
    ),
    # In the else branch (fallback)
    (
        '                logger.warning("LLM doesn\'t support vision, using text fallback")',
        """                logger.warning(f"⚠️ DEBUG: LLM doesn't support vision, using text fallback")
                logger.warning(f"⚠️ DEBUG: LLM type: {type(self.llm_manager)}")
                logger.warning(f"⚠️ DEBUG: Available methods: {[m for m in dir(self.llm_manager) if not m.startswith('_')][:10]}")"""
    ),
    # At the beginning of explain_visualization
    (
        '        logger.info(f"Starting vision-based explanation for: {viz_path}, type: {viz_type}")',
        """        logger.info(f"🚀 DEBUG: Starting vision-based explanation")
        logger.info(f"🚀 DEBUG: viz_path: {viz_path}")
        logger.info(f"🚀 DEBUG: viz_type: {viz_type}")
        logger.info(f"🚀 DEBUG: session_id: {session_id}")
        logger.info(f"🚀 DEBUG: LLM Manager available: {self.llm_manager is not None}")
        if self.llm_manager:
            logger.info(f"🚀 DEBUG: LLM Manager type: {type(self.llm_manager)}")
            logger.info(f"🚀 DEBUG: Has generate_with_image: {hasattr(self.llm_manager, 'generate_with_image')}")"""
    ),
    # After capturing image
    (
        '            logger.info(f"Successfully converted visualization to image, getting LLM explanation")',
        """            logger.info(f"📸 DEBUG: Successfully converted to image")
            logger.info(f"📸 DEBUG: Image path: {img_path}")
            logger.info(f"📸 DEBUG: Image size: {os.path.getsize(img_path) if os.path.exists(img_path) else 'N/A'} bytes")
            logger.info(f"📸 DEBUG: Converting to base64 for vision API...")"""
    ),
]

# Apply all debug additions
for old_line, new_lines in debug_additions:
    if old_line in content:
        content = content.replace(old_line, new_lines)
        print(f"✅ Added debug after: {old_line[:50]}...")
    else:
        print(f"⚠️  Could not find: {old_line[:50]}...")

# Save the debugged version
with open('app/services/universal_viz_explainer.py', 'w') as f:
    f.write(content)

print("\n✅ Debug logging added to universal_viz_explainer.py")
print("Now the service will log detailed information about:")
print("- LLM Manager type and methods")
print("- Image capture success")
print("- Vision API calls")
print("- Explanation results")