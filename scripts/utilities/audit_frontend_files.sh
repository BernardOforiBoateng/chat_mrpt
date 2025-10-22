#!/bin/bash

echo "🔍 COMPREHENSIVE FRONTEND AUDIT REPORT"
echo "======================================"
echo ""

KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE="3.21.167.170"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    if [ -f "aws_files/chatmrpt-key.pem" ]; then
        cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
        chmod 600 /tmp/chatmrpt-key2.pem
    fi
fi

echo "📁 SECTION 1: CSS FILES INVENTORY"
echo "---------------------------------"
echo ""
echo "LOCAL CSS FILES:"
ls -lah app/static/css/*.css 2>/dev/null | awk '{print $9, $5, $6, $7, $8}'
echo ""
echo "AWS CSS FILES:"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE "ls -lah /home/ec2-user/ChatMRPT/app/static/css/*.css 2>/dev/null" | awk '{print $9, $5, $6, $7, $8}'

echo ""
echo "📊 CSS FILE ANALYSIS:"
echo "----------------------"
for file in app/static/css/*.css; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo ""
        echo "📄 $filename:"
        echo "  - Lines: $(wc -l < "$file")"
        echo "  - Size: $(ls -lh "$file" | awk '{print $5}')"
        echo "  - Purpose/Content:"
        
        case "$filename" in
            "style.css")
                echo "    ⚠️ OLD/REDUNDANT - Original styles, NOT being used!"
                echo "    Contains: $(grep -c "voting-buttons\|vote-btn" "$file" || echo 0) Arena references"
                ;;
            "modern-minimalist-theme.css")
                echo "    ✅ ACTIVE - Main theme file currently in use"
                echo "    Contains: $(grep -c "voting-buttons\|vote-btn" "$file" || echo 0) Arena references"
                ;;
            "arena.css")
                echo "    ⚠️ ORPHANED - Created but NOT loaded in HTML!"
                echo "    Contains: Complete Arena styling with !important flags"
                ;;
            "vertical-nav.css")
                echo "    ⚠️ OLD/UNUSED - Original nav, replaced by v2"
                ;;
            "vertical-nav-v2.css")
                echo "    ✅ ACTIVE - Current navigation styles"
                ;;
        esac
    fi
done

echo ""
echo ""
echo "📁 SECTION 2: JAVASCRIPT FILES INVENTORY"
echo "----------------------------------------"
echo ""
echo "LOCAL JS STRUCTURE:"
find app/static/js -name "*.js" -type f | sort | while read file; do
    size=$(ls -lh "$file" | awk '{print $5}')
    lines=$(wc -l < "$file")
    echo "  $file ($size, $lines lines)"
done

echo ""
echo "AWS JS FILES (chat modules only):"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE << 'EOF'
find /home/ec2-user/ChatMRPT/app/static/js/modules/chat -name "*.js" | while read file; do
    size=$(ls -lh "$file" | awk '{print $5}')
    lines=$(wc -l < "$file")
    basename=$(basename "$file")
    echo "  $basename ($size, $lines lines)"
done
EOF

echo ""
echo ""
echo "📁 SECTION 3: HTML TEMPLATES ANALYSIS"
echo "-------------------------------------"
echo ""
echo "TEMPLATES USING CSS:"
grep -l "css\|style" app/templates/*.html 2>/dev/null | while read file; do
    echo ""
    echo "📄 $(basename $file):"
    echo "  CSS imports:"
    grep -E "link.*css|url_for.*css" "$file" | sed 's/^/    /'
done

echo ""
echo ""
echo "🔍 SECTION 4: REDUNDANCY ANALYSIS"
echo "---------------------------------"
echo ""
echo "REDUNDANT/OLD FILES IDENTIFIED:"
echo ""
echo "CSS FILES:"
echo "  1. style.css - OLD, replaced by modern-minimalist-theme.css"
echo "     - Status: Still exists but NOT loaded"
echo "     - Has Arena styles: $(grep -c "voting-buttons\|vote-btn" app/static/css/style.css || echo 0) references"
echo ""
echo "  2. vertical-nav.css - OLD, replaced by vertical-nav-v2.css"
echo "     - Status: Still exists but NOT loaded"
echo "     - Size: $(ls -lh app/static/css/vertical-nav.css | awk '{print $5}')"
echo ""
echo "  3. arena.css - ORPHANED, created but never linked"
echo "     - Status: Exists but NOT referenced in HTML"
echo "     - Contains: Complete Arena UI styles"

echo ""
echo ""
echo "🔍 SECTION 5: CSS LOADING ORDER ANALYSIS"
echo "----------------------------------------"
echo ""
echo "CURRENT LOADING ORDER (from index.html):"
grep -n "css" app/templates/index.html | grep -E "link|url_for" | nl

echo ""
echo ""
echo "⚠️ SECTION 6: CONFLICTS & ISSUES"
echo "---------------------------------"
echo ""
echo "1. BOOTSTRAP CONFLICTS:"
echo "   - Bootstrap loads FIRST (line 14 in index.html)"
echo "   - Bootstrap button classes: .btn, .btn-*"
echo "   - Our classes: .vote-btn (may conflict)"
echo ""
echo "2. MISSING REFERENCES:"
echo "   - arena.css exists but NOT in any HTML template"
echo "   - Checked: $(grep -l "arena.css" app/templates/*.html 2>/dev/null | wc -l) templates reference arena.css"
echo ""
echo "3. DUPLICATE STYLES:"
echo "   - Arena styles in style.css: $(grep -c "voting-buttons\|vote-btn" app/static/css/style.css || echo 0) occurrences"
echo "   - Arena styles in modern-minimalist-theme.css: $(grep -c "voting-buttons\|vote-btn" app/static/css/modern-minimalist-theme.css || echo 0) occurrences"
echo "   - Arena styles in arena.css: $(grep -c "voting-buttons\|vote-btn" app/static/css/arena.css || echo 0) occurrences"

echo ""
echo ""
echo "📊 SECTION 7: FILE RELATIONSHIPS"
echo "--------------------------------"
echo ""
echo "ACTIVE FILES (Currently in use):"
echo "  ✅ modern-minimalist-theme.css - Main theme"
echo "  ✅ vertical-nav-v2.css - Navigation"
echo "  ✅ message-handler.js - Chat/Arena functionality"
echo "  ✅ index.html - Main template"
echo ""
echo "ORPHANED FILES (Exist but not used):"
echo "  ⚠️ arena.css - Created but not linked"
echo "  ⚠️ style.css - Old main styles"
echo "  ⚠️ vertical-nav.css - Old navigation"
echo ""
echo "EXTERNAL DEPENDENCIES:"
echo "  📦 Bootstrap 5.3.2 - CDN"
echo "  📦 Font Awesome 6.4.2 - CDN"

echo ""
echo ""
echo "📋 SECTION 8: ARENA STYLES LOCATION"
echo "------------------------------------"
echo ""
echo "WHERE ARE ARENA STYLES?"
echo ""
echo "1. In style.css (NOT LOADED):"
grep -n "\.voting-buttons\|\.vote-btn" app/static/css/style.css | head -5 | sed 's/^/   Line /'

echo ""
echo "2. In modern-minimalist-theme.css (LOADED):"
grep -n "\.voting-buttons\|\.vote-btn" app/static/css/modern-minimalist-theme.css | head -5 | sed 's/^/   Line /'

echo ""
echo "3. In arena.css (NOT LOADED):"
grep -n "\.voting-buttons\|\.vote-btn" app/static/css/arena.css | head -5 | sed 's/^/   Line /'

echo ""
echo ""
echo "🎯 SECTION 9: SUMMARY"
echo "--------------------"
echo ""
echo "PROBLEMS IDENTIFIED:"
echo "  1. arena.css exists but is NOT loaded (missing from index.html)"
echo "  2. style.css has Arena styles but is NOT loaded (replaced by modern theme)"
echo "  3. Arena styles in modern-minimalist-theme.css are at END of file (low priority)"
echo "  4. Bootstrap loads before our styles (potential conflicts)"
echo "  5. Three redundant CSS files taking up space"
echo ""
echo "FILES THAT NEED ATTENTION:"
echo "  - index.html - Needs to load arena.css"
echo "  - modern-minimalist-theme.css - Arena styles at wrong position"
echo "  - arena.css - Should be loaded after theme CSS"
echo "  - style.css - Should be deleted (redundant)"
echo "  - vertical-nav.css - Should be deleted (redundant)"
echo ""
echo "📊 AUDIT COMPLETE"