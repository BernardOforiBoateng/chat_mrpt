#\!/usr/bin/env python3
"""Test Data Analysis V3 with OpenAI API locally"""

import os
import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, '.')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_data_analysis():
    """Test the Data Analysis V3 agent with OpenAI"""
    
    # Create test session
    session_id = "test_openai_123"
    
    # Create upload directory with test data
    upload_dir = Path(f"instance/uploads/{session_id}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test CSV file
    test_csv = upload_dir / "data_analysis.csv"
    test_csv.write_text("""State,Population,MalariaRate,Poverty
Kano,15000000,65.2,45.3
Lagos,21000000,42.1,22.7
Abuja,3000000,28.5,15.8
""")
    
    # Create flag file
    flag_file = upload_dir / ".data_analysis_mode"
    flag_file.write_text("data_analysis.csv\n2025-01-09T10:00:00")
    
    try:
        # Import and create agent
        from app.data_analysis_v3.core.agent import DataAnalysisAgent
        
        logger.info(f"Creating Data Analysis V3 agent for session {session_id}")
        agent = DataAnalysisAgent(session_id)
        
        # Test query
        query = "What are the top 2 states by malaria rate?"
        logger.info(f"Testing query: {query}")
        
        result = await agent.analyze(query)
        
        print("\n" + "="*60)
        print("DATA ANALYSIS V3 TEST RESULTS")
        print("="*60)
        print(f"Success: {result.get('success', False)}")
        print(f"Message: {result.get('message', 'No message')[:500]}")
        
        if result.get('visualization_data'):
            print(f"Visualizations created: {len(result['visualization_data'])}")
            
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_data_analysis())
    sys.exit(0 if success else 1)
