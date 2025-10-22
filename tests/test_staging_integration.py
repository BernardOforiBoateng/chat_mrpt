"""
Integration Tests for Column Sanitization on Staging
Tests the complete end-to-end workflow on the staging server
"""

import pytest
import requests
import pandas as pd
import time
import json
from pathlib import Path

# Staging server configuration
STAGING_URL = "http://3.21.167.170:8080"
STAGING_ALB = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"


class TestStagingIntegration:
    """End-to-end integration tests on staging server."""
    
    @pytest.fixture(scope="class")
    def session_id(self):
        """Generate unique session ID for tests."""
        return f"pytest_{int(time.time())}"
    
    @pytest.fixture(scope="class")
    def test_data_path(self):
        """Path to test data file."""
        return Path("www/adamawa_tpr_cleaned.csv")
    
    @pytest.fixture(scope="class", autouse=True)
    def upload_test_data(self, session_id, test_data_path):
        """Upload test data once for all tests in class."""
        if not test_data_path.exists():
            pytest.skip(f"Test data not found: {test_data_path}")
        
        # Upload the file
        with open(test_data_path, 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f)}
            data = {'session_id': session_id}
            
            response = requests.post(
                f"{STAGING_URL}/api/data-analysis/upload",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code != 200:
                pytest.fail(f"Failed to upload test data: {response.status_code}")
        
        # Wait for processing
        time.sleep(2)
        
        yield
        
        # Cleanup would go here if needed
    
    def test_staging_health_check(self):
        """Test that staging server is healthy."""
        response = requests.get(f"{STAGING_URL}/ping", timeout=5)
        assert response.status_code == 200, "Staging server not healthy"
    
    def test_column_names_query(self, session_id):
        """Test that agent can list column names (sanitized)."""
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "What are the column names in the dataset?",
                "session_id": session_id
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        
        result = response.json()
        message = result.get("message", "").lower()
        
        # Check for sanitized column indicators
        assert "column" in message or "names" in message, "No column information in response"
        
        # Should NOT have special characters in column names
        assert "≥" not in message, "Special character ≥ found in column names"
        assert "<" not in result.get("message", ""), "Special character < found in column names"
    
    def test_data_shape_query(self, session_id):
        """Test basic data shape query."""
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "What is the shape of the data?",
                "session_id": session_id
            },
            timeout=30
        )
        
        assert response.status_code == 200
        
        result = response.json()
        message = result.get("message", "")
        
        # Should mention the correct shape
        assert "10,452" in message or "10452" in message, "Incorrect row count"
        assert "22" in message, "Incorrect column count"
    
    def test_simple_sum_calculation(self, session_id):
        """Test simple sum calculation."""
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "What is the total number of RDT tests for children under 5?",
                "session_id": session_id
            },
            timeout=30
        )
        
        assert response.status_code == 200
        
        result = response.json()
        message = result.get("message", "")
        
        # Should return a number (not an error)
        assert not any(word in message.lower() for word in 
                      ['error', 'trouble', 'issue', 'problem', 'difficulty']), \
                      "Error indicators found in response"
        
        # Should have some numeric result
        assert any(char.isdigit() for char in message), "No numeric result in response"
    
    def test_top_facilities_query(self, session_id):
        """Test the previously failing query - top facilities by testing volume."""
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "Show me the top 10 facilities by total testing volume",
                "session_id": session_id
            },
            timeout=60
        )
        
        assert response.status_code == 200
        
        result = response.json()
        message = result.get("message", "")
        
        # Should NOT have error messages
        assert "difficulty" not in message.lower(), "Still having difficulty accessing columns"
        assert "issue" not in message.lower(), "Still reporting issues"
        
        # Should return actual facility names
        facility_names = [
            "General Hospital", "Primary Health", "Cottage Hospital",
            "Health Centre", "Health Clinic", "Hospital", "Clinic", "Healthcare"
        ]
        
        facilities_found = sum(1 for name in facility_names if name in message)
        assert facilities_found >= 2, f"Only found {facilities_found} facility references"
        
        # Should have numbers (test counts)
        import re
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*', message)
        assert len(numbers) >= 5, f"Only found {len(numbers)} numbers, expected at least 5"
    
    def test_pattern_matching_query(self, session_id):
        """Test that pattern matching works with sanitized columns."""
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "How many columns contain 'rdt' in their name?",
                "session_id": session_id
            },
            timeout=30
        )
        
        assert response.status_code == 200
        
        result = response.json()
        message = result.get("message", "")
        
        # Should find RDT columns (there are 6 in the data)
        assert "6" in message or "six" in message.lower(), \
               "Incorrect count of RDT columns"
    
    def test_groupby_operation(self, session_id):
        """Test groupby operations work with sanitized names."""
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "What is the total number of tests by LGA? Show top 5.",
                "session_id": session_id
            },
            timeout=60
        )
        
        assert response.status_code == 200
        
        result = response.json()
        message = result.get("message", "")
        
        # Should have LGA names
        lga_names = ["Yola", "Girei", "Fufore", "Song", "Demsa", "Numan", "Lamurde"]
        lgas_found = sum(1 for lga in lga_names if lga in message)
        
        assert lgas_found >= 2, f"Only found {lgas_found} LGA names"
        
        # Should not have errors
        assert "error" not in message.lower(), "Error in groupby operation"
    
    def test_complex_aggregation(self, session_id):
        """Test complex multi-column aggregation."""
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "Calculate the test positivity rate for RDT tests by combining all age groups",
                "session_id": session_id
            },
            timeout=60
        )
        
        assert response.status_code == 200
        
        result = response.json()
        message = result.get("message", "")
        
        # Should calculate a percentage
        assert "%" in message or "percent" in message.lower(), \
               "No percentage in TPR calculation"
        
        # Should not have column access errors
        assert "column" not in message.lower() or "found" in message.lower(), \
               "Column access error detected"


class TestAlternativeServer:
    """Test on alternative staging instance."""
    
    def test_alternative_instance(self):
        """Test that the second staging instance also works."""
        alt_url = "http://18.220.103.20:8080"
        
        response = requests.get(f"{alt_url}/ping", timeout=5)
        assert response.status_code == 200, "Alternative instance not healthy"


class TestErrorHandling:
    """Test error handling with problematic data."""
    
    def test_nonexistent_column(self):
        """Test handling of nonexistent column queries."""
        session_id = f"test_error_{int(time.time())}"
        
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "What is the sum of the 'nonexistent_column'?",
                "session_id": session_id
            },
            timeout=30
        )
        
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400], "Unexpected status code"
    
    def test_empty_session(self):
        """Test queries without uploaded data."""
        session_id = f"test_empty_{int(time.time())}"
        
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                "message": "Show me the data",
                "session_id": session_id
            },
            timeout=30
        )
        
        assert response.status_code == 200
        
        result = response.json()
        message = result.get("message", "").lower()
        
        # Should indicate no data
        assert any(word in message for word in 
                  ['no data', 'upload', 'not found', 'first upload']), \
                  "Doesn't indicate missing data"


@pytest.mark.parametrize("query,expected_keywords", [
    ("List 5 health facilities", ["health", "facility", "clinic", "hospital"]),
    ("What columns relate to testing?", ["test", "rdt", "microscopy"]),
    ("Show unique ward names", ["ward", "unique", "distinct"]),
    ("Calculate total LLIN distributed", ["llin", "total", "distributed"]),
])
def test_various_queries(query, expected_keywords):
    """Test various query types."""
    session_id = f"test_param_{int(time.time())}"
    
    # Upload data first
    with open("www/adamawa_tpr_cleaned.csv", 'rb') as f:
        files = {'file': ('test.csv', f)}
        data = {'session_id': session_id}
        upload_resp = requests.post(
            f"{STAGING_URL}/api/data-analysis/upload",
            files=files,
            data=data,
            timeout=30
        )
        
        if upload_resp.status_code != 200:
            pytest.skip("Could not upload data")
    
    time.sleep(2)
    
    # Test query
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": query,
            "session_id": session_id
        },
        timeout=30
    )
    
    assert response.status_code == 200
    
    result = response.json()
    message = result.get("message", "").lower()
    
    # Check for expected keywords
    found_keywords = [kw for kw in expected_keywords if kw in message]
    assert len(found_keywords) >= 1, \
           f"Expected keywords {expected_keywords}, found {found_keywords}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-s"])