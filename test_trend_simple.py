"""
Simplified test for Lake Assessment trend analysis
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def check_existing_analyses():
    """Check if there are any existing analyses we can use for testing"""
    print("\n" + "=" * 80)
    print("CHECKING EXISTING ANALYSES")
    print("=" * 80)
    
    # Try to get the last submission
    # This is a simple way to test with already processed reports
    print("\nNote: If you have already uploaded reports, you can test with those.")
    print("Otherwise, we'll do a fresh upload.\n")

def simple_trend_test():
    """Simple test using smaller Fiddle Lake reports"""
    
    print("=" * 80)
    print("SIMPLE LAKE ASSESSMENT TEST")
    print("=" * 80)
    
    # Use smaller Fiddle Lake reports for faster processing
    test_files = [
        r"E:\upwork\Documet parsing\document\Fiddle Lake  071620 survey report (1).pdf",
        r"E:\upwork\Documet parsing\document\Fiddle Lake Algae 081220.pdf",
        r"E:\upwork\Documet parsing\document\Fiddle Lake  091520 survey report.pdf"
    ]
    
    print("\n1. UPLOADING SMALL TEST FILES")
    print("-" * 40)
    
    # Check files exist
    for f in test_files:
        if not Path(f).exists():
            print(f"   [ERROR] File not found: {f}")
            return
    
    # Upload without AI analysis for faster testing
    contact_info = {
        "name": "Test User",
        "email": "test@example.com",
        "organization": "Test Organization",
        "documentType": "report"
    }
    
    files = []
    for file_path in test_files:
        files.append(
            ('files', (Path(file_path).name, open(file_path, 'rb'), 'application/pdf'))
        )
    
    data = {'contact_info': json.dumps(contact_info)}
    
    try:
        response = requests.post(f"{BASE_URL}{API_PREFIX}/upload", files=files, data=data)
        
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"   [OK] Uploaded {result.get('files_processed')} files")
            print(f"   Submission ID: {result.get('submission_id')}")
            
            submission_id = result.get('submission_id')
            analysis_ids = result.get('analysis_ids', [])
            
            return submission_id, analysis_ids
        else:
            print(f"   [ERROR] Upload failed: {response.text}")
            return None, []
    except Exception as e:
        print(f"   [ERROR] {e}")
        return None, []

def check_analysis_details(analysis_id):
    """Get detailed analysis results"""
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/analyze/{analysis_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"\n   Analysis ID: {analysis_id[:8]}...")
            print(f"     Status: {data.get('status')}")
            print(f"     Filename: {data.get('filename')}")
            
            # Check if compliance evaluation exists
            if 'compliance_evaluation' in data:
                compliance = data['compliance_evaluation']
                print(f"     Compliance Score: {compliance.get('overall_score', 'N/A')}")
                
                # Check if year was extracted
                if 'extracted_year' in data:
                    print(f"     Year: {data['extracted_year']}")
                
                # Check if lake name was extracted
                if 'lake_name' in data:
                    print(f"     Lake: {data['lake_name']}")
            
            return data
        else:
            print(f"   [ERROR] Failed to get analysis {analysis_id[:8]}: {response.status_code}")
            return None
    except Exception as e:
        print(f"   [ERROR] {e}")
        return None

def wait_for_completion(analysis_ids, max_wait=60):
    """Wait for analyses to complete with simpler logic"""
    print("\n2. WAITING FOR PROCESSING")
    print("-" * 40)
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        all_complete = True
        
        for aid in analysis_ids:
            response = requests.get(f"{BASE_URL}{API_PREFIX}/analyze/{aid}")
            if response.status_code == 200:
                status = response.json().get('status')
                if status != 'complete':
                    all_complete = False
                    print(f"   {aid[:8]}... {status}")
        
        if all_complete:
            print("   [OK] All analyses complete!")
            return True
        
        time.sleep(3)
    
    print("   [TIMEOUT] Processing taking too long")
    return False

def test_assessment_manually():
    """Test Lake Assessment with manual data (no upload needed)"""
    
    print("\n" + "=" * 80)
    print("TESTING LAKE ASSESSMENT WITH MOCK DATA")
    print("=" * 80)
    
    import sys
    sys.path.insert(0, '.')
    from core.lake_assessment import LakeAssessment
    
    # Create test data
    test_reports = [
        {
            "filename": "Test Lake 2021 Report.pdf",
            "text": "Test Lake Annual Report 2021",
            "extracted_year": 2021,
            "lake_name": "Test Lake",
            "metrics": {
                "dissolved_oxygen_min": 4.0,
                "hypoxic_volume": 10000,
                "orthophosphate_max": 0.05
            },
            "compliance_evaluation": {
                "overall_score": 75
            }
        },
        {
            "filename": "Test Lake 2022 Report.pdf",
            "text": "Test Lake Annual Report 2022",
            "extracted_year": 2022,
            "lake_name": "Test Lake",
            "metrics": {
                "dissolved_oxygen_min": 3.5,
                "hypoxic_volume": 12000,
                "orthophosphate_max": 0.06
            },
            "compliance_evaluation": {
                "overall_score": 70
            }
        },
        {
            "filename": "Test Lake 2023 Report.pdf",
            "text": "Test Lake Annual Report 2023",
            "extracted_year": 2023,
            "lake_name": "Test Lake",
            "metrics": {
                "dissolved_oxygen_min": 3.0,
                "hypoxic_volume": 15000,
                "orthophosphate_max": 0.08
            },
            "compliance_evaluation": {
                "overall_score": 65
            }
        }
    ]
    
    # Test Lake Assessment
    lake_assessment = LakeAssessment()
    
    # Test extraction
    print("\n1. Testing year/lake extraction:")
    for report in test_reports:
        lake, year = lake_assessment.extract_lake_name_and_year(report)
        print(f"   {report['filename']}: Lake={lake}, Year={year}")
    
    # Test grouping
    print("\n2. Testing report grouping:")
    groups = lake_assessment.group_reports_by_lake(test_reports)
    for lake_name, reports in groups.items():
        print(f"   {lake_name}: {len(reports)} reports")
    
    # Test trend analysis
    print("\n3. Testing trend analysis:")
    if lake_assessment.should_perform_assessment(test_reports):
        assessments = lake_assessment.perform_assessment(test_reports)
        
        for lake_name, assessment_data in assessments.items():
            trend = assessment_data['trend_analysis']
            print(f"   Lake: {lake_name}")
            print(f"   Trajectory: {trend['overall_trajectory']}")
            print(f"   Years: {trend['years']}")
            
            # Show parameter trends
            print("   Parameter Trends:")
            for param, trend_data in trend['parameters'].items():
                if trend_data.get('direction'):
                    print(f"     - {param}: {trend_data['direction']}")
    else:
        print("   [INFO] Not enough data for assessment")

if __name__ == "__main__":
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("Server not healthy!")
            exit(1)
    except:
        print("Server not running! Start with: python main.py")
        exit(1)
    
    print("Server is running!\n")
    
    # Option 1: Test with real upload (may be slow)
    print("Option 1: Testing with real file upload")
    submission_id, analysis_ids = simple_trend_test()
    
    if submission_id and analysis_ids:
        # Wait a bit for processing
        if wait_for_completion(analysis_ids):
            # Check each analysis
            print("\n3. ANALYSIS RESULTS")
            print("-" * 40)
            for aid in analysis_ids:
                check_analysis_details(aid)
            
            # Try to trigger assessment
            print("\n4. TRIGGERING LAKE ASSESSMENT")
            print("-" * 40)
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/meta-analysis/trend",
                params={"submission_id": submission_id}
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result.get('success')}")
                print(f"   Message: {result.get('message')}")
                if result.get('lakes_analyzed'):
                    print(f"   Lakes: {result.get('lakes_analyzed')}")
    
    # Option 2: Test with mock data (instant)
    print("\nOption 2: Testing with mock data (no upload needed)")
    test_assessment_manually()
