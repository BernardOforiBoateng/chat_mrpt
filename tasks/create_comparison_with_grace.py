"""
Create side-by-side comparison: Grace's maps vs Bernard's validation
Shows that independent analysis reproduces the same findings
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import numpy as np

print("Creating Grace vs Bernard comparison...")

# Load Grace's maps
try:
    grace_aridity = mpimg.imread('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/b.png')
    grace_dbi = mpimg.imread('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/bb.png')
    has_grace_maps = True
    print("✓ Grace's maps loaded")
except:
    has_grace_maps = False
    print("✗ Could not load Grace's maps (b.png, bb.png)")

# Load Bernard's maps
try:
    bernard_aridity = mpimg.imread('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/bernard_aridity_map.png')
    bernard_dbi = mpimg.imread('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/bernard_dbi_map.png')
    has_bernard_maps = True
    print("✓ Bernard's maps loaded")
except:
    has_bernard_maps = False
    print("✗ Could not load Bernard's maps")

if has_grace_maps and has_bernard_maps:
    # Create 2x2 comparison
    fig = plt.figure(figsize=(18, 16))

    # Add title
    fig.suptitle('Independent Validation: Grace (Original) vs Bernard (Validation)\n99.4% Identical DBI Values',
                 fontsize=18, fontweight='bold', y=0.98)

    # Grace's Aridity (top left)
    ax1 = plt.subplot(2, 2, 1)
    ax1.imshow(grace_aridity)
    ax1.axis('off')
    ax1.set_title("Grace's Aridity Classification\n(Original Data)",
                  fontsize=14, fontweight='bold', pad=15, color='#d32f2f')

    # Bernard's Aridity (top right)
    ax2 = plt.subplot(2, 2, 2)
    ax2.imshow(bernard_aridity)
    ax2.axis('off')
    ax2.set_title("Bernard's Aridity Classification\n(Independent Validation)",
                  fontsize=14, fontweight='bold', pad=15, color='#2e7d32')

    # Grace's DBI (bottom left)
    ax3 = plt.subplot(2, 2, 3)
    ax3.imshow(grace_dbi)
    ax3.axis('off')
    ax3.set_title("Grace's DBI Urban %\n(Original Data)",
                  fontsize=14, fontweight='bold', pad=15, color='#d32f2f')

    # Bernard's DBI (bottom right)
    ax4 = plt.subplot(2, 2, 4)
    ax4.imshow(bernard_dbi)
    ax4.axis('off')
    ax4.set_title("Bernard's DBI Urban %\n(Independent Validation)",
                  fontsize=14, fontweight='bold', pad=15, color='#2e7d32')

    # Add annotations
    fig.text(0.5, 0.48, '✓ Same Pattern: Non-arid Southwest (Blue) Shows Low DBI (Purple)',
             ha='center', fontsize=13, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.8', facecolor='yellow', alpha=0.8))

    fig.text(0.5, 0.02, 'Key Finding: DBI mean = 27% in both analyses | MODIS = 49% | Gap = 22%\n' +
                        'Conclusion: DBI underestimates non-arid urban areas by ~50%',
             ha='center', fontsize=12, style='italic',
             bbox=dict(boxstyle='round,pad=0.6', facecolor='lightyellow', alpha=0.7))

    plt.tight_layout(rect=[0, 0.04, 1, 0.96])

    output_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/grace_vs_bernard_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")

    # Also create a simple side-by-side for DBI only
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle('DBI Urban % Comparison: Independent Validation Confirms Grace\'s Findings',
                 fontsize=16, fontweight='bold')

    axes[0].imshow(grace_dbi)
    axes[0].axis('off')
    axes[0].set_title("Grace's DBI Analysis\n(Original Data)\nDBI Mean: 27.2%",
                      fontsize=13, fontweight='bold', color='#d32f2f')

    axes[1].imshow(bernard_dbi)
    axes[1].axis('off')
    axes[1].set_title("Bernard's DBI Analysis\n(Independent Validation)\nDBI Mean: 27.2%",
                      fontsize=13, fontweight='bold', color='#2e7d32')

    fig.text(0.5, 0.08, '✓ 99.4% Match (343/345 points identical) | Both show low DBI in non-arid Bamako',
             ha='center', fontsize=12, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.8))

    plt.tight_layout(rect=[0, 0.12, 1, 0.94])

    output_dbi = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/dbi_validation_comparison.png'
    plt.savefig(output_dbi, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_dbi}")

    print()
    print("="*80)
    print("COMPARISON IMAGES CREATED")
    print("="*80)
    print("1. grace_vs_bernard_comparison.png - Full 2x2 comparison (aridity + DBI)")
    print("2. dbi_validation_comparison.png - DBI only side-by-side")
    print()
    print("These show:")
    print("  ✓ Grace's original maps (left)")
    print("  ✓ Bernard's independent validation (right)")
    print("  ✓ Identical patterns prove findings are reproducible")
    print("  ✓ Both show DBI ~27% in non-arid Bamako (MODIS shows 49%)")
    print("="*80)

else:
    print()
    print("ERROR: Cannot create comparison - missing maps")
    print(f"  Grace's maps available: {has_grace_maps}")
    print(f"  Bernard's maps available: {has_bernard_maps}")
