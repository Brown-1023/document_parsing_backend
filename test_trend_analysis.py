"""
Test script for Lake Assessment trend analysis feature
Tests with real lake reports from the document folder
"""

import requests
import json
import time
from pathlib import Path

# Server configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_trend_analysis():
    """Test the Lake Assessment feature with multiple reports from the same lake"""
    
    print("=" * 80)
    print("LAKE ASSESSMENT TREND ANALYSIS TEST")
    print("=" * 80)
    
    # Select test files - using PLEON TWCWC reports (2019, 2021, 2022)
    # These are good test candidates as they span 3 different years
    test_files = [
        r"E:\upwork\Documet parsing\document\PLEON_TWCWC_2019_report_FINAL (1).pdf",
        r"E:\upwork\Documet parsing\document\PLEON_TWCWC_2021_report.pdf",
        r"E:\upwork\Documet parsing\document\PLEON_TWCWC_2022_report (2).pdf"
    ]
    
    # Alternative test set - Fiddle Lake reports (all from 2020, but multiple surveys)
    # test_files = [
    #     r"E:\upwork\Documet parsing\document\Fiddle Lake  071620 survey report (1).pdf",
    #     r"E:\upwork\Documet parsing\document\Fiddle Lake  081220 survey report.pdf",
    #     r"E:\upwork\Documet parsing\document\Fiddle Lake  091520 survey report.pdf"
    # ]
    
    # Check if files exist
    print("\n1. CHECKING TEST FILES")
    print("-" * 40)
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"   [OK] {Path(file_path).name}")
        else:
            print(f"   [ERROR] File not found: {file_path}")
            return
    
    # Prepare upload data
    contact_info = {
        "name": "Test User",
        "email": "test@example.com",
        "organization": "Test Organization",
        "documentType": "report"  # These are lake reports with data
    }
    
    print("\n2. UPLOADING REPORTS")
    print("-" * 40)
    
    # Prepare files for upload
    files = []
    for file_path in test_files:
        files.append(
            ('files', (Path(file_path).name, open(file_path, 'rb'), 'application/pdf'))
        )
    
    # Prepare form data
    data = {
        'contact_info': json.dumps(contact_info)
    }
    
    # Upload files
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/upload",
            files=files,
            data=data
        )
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"   [OK] Upload successful!")
            print(f"   Submission ID: {result.get('submission_id')}")
            print(f"   Analysis IDs: {result.get('analysis_ids')}")
            print(f"   Files processed: {result.get('files_processed')}")
            
            submission_id = result.get('submission_id')
            analysis_ids = result.get('analysis_ids', [])
        else:
            print(f"   [ERROR] Upload failed: {response.status_code}")
            print(f"   {response.text}")
            return
    except Exception as e:
        print(f"   [ERROR] Upload exception: {e}")
        return
    
    print("\n3. WAITING FOR ANALYSIS TO COMPLETE")
    print("-" * 40)
    print("   Checking analysis status...")
    
    # Wait for individual analyses to complete (max 2 minutes)
    max_wait = 120
    check_interval = 5
    elapsed = 0
    
    while elapsed < max_wait:
        all_complete = True
        for analysis_id in analysis_ids:
            try:
                response = requests.get(f"{BASE_URL}{API_PREFIX}/analyze/{analysis_id}")
                if response.status_code == 200:
                    analysis_data = response.json()
                    status = analysis_data.get('status', 'unknown')
                    if status != 'complete':
                        all_complete = False
                        print(f"   Analysis {analysis_id[:8]}... Status: {status}")
            except:
                all_complete = False
        
        if all_complete:
            print("   [OK] All analyses complete!")
            break
        
        time.sleep(check_interval)
        elapsed += check_interval
    
    if elapsed >= max_wait:
        print("   [WARNING] Timeout waiting for analyses to complete")
    
    print("\n4. CHECKING LAKE ASSESSMENT STATUS")
    print("-" * 40)
    
    # Check if Lake Assessment was triggered
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/meta-analysis/{submission_id}/status")
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Total reports: {status_data.get('total_reports')}")
            print(f"   Completed analyses: {status_data.get('completed_analyses')}")
            print(f"   Assessment complete: {status_data.get('assessment_complete')}")
            print(f"   Can perform assessment: {status_data.get('can_perform_assessment')}")
            
            if status_data.get('assessment_reports'):
                print("\n   Assessment Reports Generated:")
                for lake_name, report_path in status_data['assessment_reports'].items():
                    print(f"     - {lake_name}: {Path(report_path).name}")
        else:
            print(f"   [ERROR] Failed to get status: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"   [ERROR] Status check exception: {e}")
    
    print("\n5. MANUALLY TRIGGERING LAKE ASSESSMENT (if needed)")
    print("-" * 40)
    
    # Try to manually trigger assessment
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/meta-analysis/trend",
            params={"submission_id": submission_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   [OK] Lake Assessment triggered successfully!")
                print(f"   Lakes analyzed: {result.get('lakes_analyzed')}")
                print(f"   Assessment reports: {result.get('assessment_reports')}")
                
                # Download assessment report
                if result.get('assessment_reports'):
                    for lake_name in result['lakes_analyzed']:
                        print(f"\n   Downloading report for {lake_name}...")
                        download_assessment_report(submission_id, lake_name)
            else:
                print(f"   [INFO] {result.get('message')}")
        else:
            print(f"   [ERROR] Failed to trigger assessment: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"   [ERROR] Assessment trigger exception: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

def download_assessment_report(submission_id: str, lake_name: str):
    """Download a Lake Assessment report"""
    try:
        # URL encode the lake name
        import urllib.parse
        encoded_lake_name = urllib.parse.quote(lake_name.lower())
        
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/meta-analysis/{submission_id}/report/{encoded_lake_name}"
        )
        
        if response.status_code == 200:
            # Save the report
            output_path = f"Lake_Assessment_{lake_name.replace(' ', '_')}.docx"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"   [OK] Report saved as: {output_path}")
        else:
            print(f"   [ERROR] Failed to download report: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Download exception: {e}")

def test_with_different_lakes():
    """Test with multiple different lake sets"""
    
    print("\n" + "=" * 80)
    print("TESTING MULTIPLE LAKE SETS")
    print("=" * 80)
    
    lake_sets = {
        "Lake Monticello": [
            r"E:\upwork\Documet parsing\document\2022_10 Lake Monticello Water Testing Laboratory Report.pdf",
            r"E:\upwork\Documet parsing\document\2023_05 Lake Monticello Water Testing Algae and Water Baseline.pdf",
            r"E:\upwork\Documet parsing\document\Lake Monticello SeSCRIPT Algae and Water Quality Baseline Plus 20230504 (1).pdf"
        ],
        "Solitude Lake": [
            r"E:\upwork\Documet parsing\document\Solitude Lake Survey Report 04282020.pdf",
            r"E:\upwork\Documet parsing\document\Solitude Lake Survey Report 05212020.pdf",
            r"E:\upwork\Documet parsing\document\Solitude Lake Survey Report 062520.pdf"
        ]
    }
    
    for lake_name, files in lake_sets.items():
        print(f"\nTesting {lake_name}...")
        print("-" * 40)
        
        # Check if we have enough files
        existing_files = [f for f in files if Path(f).exists()]
        if len(existing_files) >= 3:
            print(f"   Found {len(existing_files)} reports for {lake_name}")
            # You could call the upload process here for each set
        else:
            print(f"   Insufficient files for {lake_name}")

if __name__ == "__main__":
    # Make sure the server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("Server is running and healthy!")
        else:
            print("Server health check failed!")
            exit(1)
    except:
        print("ERROR: Server is not running!")
        print("Please start the server first: python main.py")
        exit(1)
    
    # Run the main test
    test_trend_analysis()
    
    # Optionally test other lake sets
    # test_with_different_lakes()
