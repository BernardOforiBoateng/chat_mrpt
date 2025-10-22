#!/usr/bin/env python3
"""
Debug script to trace visualization issues after TPR transition
Adds comprehensive logging to understand why visualizations fail
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add ChatMRPT to path
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

def setup_debug_logging():
    """Setup comprehensive debug logging"""
    
    # Create debug directory
    debug_dir = Path('debug_logs')
    debug_dir.mkdir(exist_ok=True)
    
    # Setup logging with detailed format
    log_file = debug_dir / f'viz_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('viz_debug')

def check_session_files(session_id: str, logger):
    """Check what files exist in session directory"""
    
    session_dir = Path(f'instance/uploads/{session_id}')
    logger.info(f"\n{'='*60}")
    logger.info(f"CHECKING SESSION FILES FOR: {session_id}")
    logger.info(f"{'='*60}")
    
    if not session_dir.exists():
        logger.error(f"❌ Session directory does not exist: {session_dir}")
        return {}
    
    files = {}
    critical_files = [
        'raw_data.csv',
        'raw_shapefile.zip',
        'unified_dataset.csv',
        'unified_dataset.geoparquet',
        'analysis_vulnerability_rankings_composite.csv',
        'analysis_vulnerability_rankings_pca.csv',
        'tpr_results.csv',
        '.analysis_complete',
        '.tpr_complete'
    ]
    
    logger.info("Checking critical files:")
    for filename in critical_files:
        filepath = session_dir / filename
        exists = filepath.exists()
        size = filepath.stat().st_size if exists else 0
        files[filename] = {
            'exists': exists,
            'size': size,
            'path': str(filepath)
        }
        
        status = "✅" if exists else "❌"
        size_str = f"({size:,} bytes)" if exists else ""
        logger.info(f"  {status} {filename} {size_str}")
    
    # Check for any HTML files (visualizations)
    html_files = list(session_dir.glob('*.html'))
    logger.info(f"\nHTML files (visualizations) found: {len(html_files)}")
    for html_file in html_files[:10]:  # Show first 10
        size = html_file.stat().st_size
        logger.info(f"  📊 {html_file.name} ({size:,} bytes)")
    
    # Check shapefile directory
    shapefile_dir = session_dir / 'shapefile'
    if shapefile_dir.exists():
        shp_files = list(shapefile_dir.glob('*'))
        logger.info(f"\nShapefile directory contents: {len(shp_files)} files")
        for shp_file in shp_files[:5]:
            logger.info(f"  📁 {shp_file.name}")
    else:
        logger.warning("⚠️ No shapefile directory found")
    
    return files

def test_visualization_tools(session_id: str, logger):
    """Test visualization tools with detailed logging"""
    
    logger.info(f"\n{'='*60}")
    logger.info("TESTING VISUALIZATION TOOLS")
    logger.info(f"{'='*60}")
    
    # Import after setting up logging
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Test 1: Variable Distribution Tool
        logger.info("\n--- Testing VariableDistribution Tool ---")
        try:
            from app.tools.variable_distribution import VariableDistribution
            
            # Test with different variable names
            test_variables = ['evi', 'EVI', 'pfpr', 'TPR', 'housing_quality']
            
            for var_name in test_variables:
                logger.info(f"\nTesting variable: '{var_name}'")
                tool = VariableDistribution(variable_name=var_name)
                
                # Check data loading
                logger.info("Loading data...")
                csv_data, shapefile_data = tool._load_data(session_id)
                
                if csv_data is not None:
                    logger.info(f"  CSV loaded: {len(csv_data)} rows, {len(csv_data.columns)} columns")
                    logger.info(f"  Columns: {list(csv_data.columns)[:10]}...")
                    
                    # Check if variable exists
                    if var_name in csv_data.columns:
                        logger.info(f"  ✅ Variable '{var_name}' found in CSV")
                    else:
                        logger.warning(f"  ❌ Variable '{var_name}' NOT in CSV")
                        # Check case-insensitive
                        matching = [col for col in csv_data.columns if col.lower() == var_name.lower()]
                        if matching:
                            logger.info(f"  💡 Found case-insensitive match: {matching}")
                else:
                    logger.error("  ❌ CSV data is None")
                
                if shapefile_data is not None:
                    logger.info(f"  Shapefile loaded: {len(shapefile_data)} features")
                    logger.info(f"  Shapefile columns: {list(shapefile_data.columns)[:10]}...")
                else:
                    logger.error("  ❌ Shapefile data is None")
                
                # Try to execute
                logger.info("Executing tool...")
                result = tool.execute(session_id)
                logger.info(f"  Success: {result.success}")
                logger.info(f"  Message: {result.message[:200]}...")
                if not result.success:
                    logger.error(f"  Error: {result.error_details}")
                
        except Exception as e:
            logger.error(f"Variable distribution test failed: {e}", exc_info=True)
        
        # Test 2: Vulnerability Map Tool
        logger.info("\n--- Testing CreateVulnerabilityMap Tool ---")
        try:
            from app.tools.visualization_maps_tools import CreateVulnerabilityMap
            
            tool = CreateVulnerabilityMap(
                risk_categories=5,
                classification_method='natural_breaks'
            )
            
            logger.info("Checking for unified dataset...")
            from app.services.tools.get_unified_dataset import _get_unified_dataset
            
            try:
                unified_df = _get_unified_dataset(session_id)
                logger.info(f"  ✅ Unified dataset found: {len(unified_df)} rows")
            except Exception as e:
                logger.error(f"  ❌ Unified dataset not found: {e}")
                
                # Check if we can use raw_data instead
                raw_path = f'instance/uploads/{session_id}/raw_data.csv'
                if os.path.exists(raw_path):
                    logger.info(f"  💡 raw_data.csv exists at {raw_path}")
                    import pandas as pd
                    raw_df = pd.read_csv(raw_path)
                    logger.info(f"     Shape: {raw_df.shape}")
                    logger.info(f"     Columns: {list(raw_df.columns)[:10]}...")
            
            logger.info("Executing vulnerability map tool...")
            result = tool.execute(session_id)
            logger.info(f"  Success: {result.success}")
            logger.info(f"  Message: {result.message[:200]}...")
            if not result.success:
                logger.error(f"  Error: {result.error_details}")
            else:
                if result.data:
                    logger.info(f"  Data keys: {list(result.data.keys())}")
                    if 'web_path' in result.data:
                        logger.info(f"  Web path: {result.data['web_path']}")
                    if 'file_path' in result.data:
                        file_path = result.data['file_path']
                        logger.info(f"  File path: {file_path}")
                        if os.path.exists(file_path):
                            size = os.path.getsize(file_path)
                            logger.info(f"  ✅ File exists ({size:,} bytes)")
                        else:
                            logger.error(f"  ❌ File does NOT exist!")
                
        except Exception as e:
            logger.error(f"Vulnerability map test failed: {e}", exc_info=True)

def trace_tool_execution(session_id: str, message: str, logger):
    """Trace actual tool execution path"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"TRACING TOOL EXECUTION")
    logger.info(f"Message: '{message}'")
    logger.info(f"{'='*60}")
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Set up Flask session
        from flask import session
        session['session_id'] = session_id
        session['csv_loaded'] = True
        session['shapefile_loaded'] = True
        session['data_loaded'] = True
        
        # Import request interpreter
        from app.core.request_interpreter import RequestInterpreter
        
        interpreter = RequestInterpreter()
        
        # Check session context
        logger.info("\nChecking session context...")
        context = interpreter.get_session_context(session_id)
        logger.info(f"Session context: {json.dumps(context, indent=2)}")
        
        # Try to interpret request
        logger.info(f"\nInterpreting request: '{message}'")
        result = interpreter.interpret_request(message, session_id)
        
        logger.info(f"Interpretation result:")
        logger.info(f"  Type: {result.get('type')}")
        logger.info(f"  Tool: {result.get('tool_name')}")
        logger.info(f"  Response: {result.get('response', '')[:200]}...")
        
        if result.get('tool_name'):
            # Try to execute the tool
            logger.info(f"\nExecuting tool: {result['tool_name']}")
            logger.info(f"Parameters: {result.get('parameters')}")
            
            from app.tools import get_tool_function
            tool_func = get_tool_function(result['tool_name'])
            
            if tool_func:
                try:
                    tool_result = tool_func(session_id, **result.get('parameters', {}))
                    logger.info(f"Tool result:")
                    logger.info(f"  Status: {tool_result.get('status')}")
                    logger.info(f"  Message: {tool_result.get('message', '')[:200]}...")
                    if tool_result.get('error_details'):
                        logger.error(f"  Error details: {tool_result['error_details']}")
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}", exc_info=True)
            else:
                logger.error(f"Tool function not found: {result['tool_name']}")

def main():
    """Main debug function"""
    
    logger = setup_debug_logging()
    
    # Use a test session ID or get from command line
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        # Use example session from the logs
        session_id = "847e36e9-ad20-4641-afd5-bda1b5c8225a"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"VISUALIZATION DEBUG SESSION")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"{'='*80}")
    
    # Check what files exist
    files = check_session_files(session_id, logger)
    
    # Test visualization tools
    test_visualization_tools(session_id, logger)
    
    # Trace specific requests
    test_messages = [
        "plot vulnerability map",
        "Plot me the map distribution for the evi variable",
        "show me the vulnerability map"
    ]
    
    for msg in test_messages:
        trace_tool_execution(session_id, msg, logger)
    
    logger.info(f"\n{'='*80}")
    logger.info("DEBUG SESSION COMPLETE")
    logger.info(f"{'='*80}")

if __name__ == "__main__":
    main()