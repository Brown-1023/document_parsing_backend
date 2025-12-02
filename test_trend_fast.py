"""
Fast test for Lake Assessment - skips AI analysis for quick testing
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_trend_analysis_fast():
    """Test Lake Assessment with smaller files for faster processing"""
    
    print("=" * 80)
    print("FAST LAKE ASSESSMENT TEST (No AI Analysis)")
    print("=" * 80)
    print("\nNOTE: Make sure skip_ai_analysis=True in config.py")
    print("      Then restart the server before running this test.\n")
    
    # Use smaller Fiddle Lake reports for faster processing
    test_files = [
        r"E:\upwork\Documet parsing\document\Fiddle Lake  071620 survey report (1).pdf",
        r"E:\upwork\Documet parsing\document\Fiddle Lake  081220 survey report.pdf",
        r"E:\upwork\Documet parsing\document\Fiddle Lake  091520 survey report.pdf"
    ]
    
    # Check files exist
    print("1. CHECKING FILES")
    print("-" * 40)
    for f in test_files:
        if Path(f).exists():
            size = Path(f).stat().st_size / 1024  # KB
            print(f"   [OK] {Path(f).name} ({size:.1f} KB)")
        else:
            print(f"   [ERROR] {f} not found!")
            return
    
    # Upload
    print("\n2. UPLOADING FILES")
    print("-" * 40)
    
    contact_info = {
        "name": "Test User",
        "email": "test@example.com",
        "organization": "Test Org",
        "documentType": "report"
    }
    
    files = []
    for file_path in test_files:
        files.append(
            ('files', (Path(file_path).name, open(file_path, 'rb'), 'application/pdf'))
        )
    
    data = {'contact_info': json.dumps(contact_info)}
    
    response = requests.post(f"{BASE_URL}{API_PREFIX}/upload", files=files, data=data)
    
    for _, file_tuple in files:
        file_tuple[1].close()
    
    if response.status_code != 200:
        print(f"   [ERROR] Upload failed: {response.text}")
        return
    
    result = response.json()
    submission_id = result.get('submission_id')
    analysis_ids = result.get('analysis_ids', [])
    
    print(f"   [OK] Uploaded {len(analysis_ids)} files")
    print(f"   Submission ID: {submission_id}")
    
    # Wait for completion (should be fast without AI)
    print("\n3. WAITING FOR ANALYSIS (should be fast without AI)")
    print("-" * 40)
    
    max_wait = 60  # 60 seconds should be enough without AI
    start = time.time()
    
    while time.time() - start < max_wait:
        all_complete = True
        for aid in analysis_ids:
            resp = requests.get(f"{BASE_URL}{API_PREFIX}/analyze/{aid}")
            if resp.status_code == 200:
                status = resp.json().get('status')
                if status != 'complete':
                    all_complete = False
                    print(f"   {aid[:8]}... {status}")
            else:
                all_complete = False
        
        if all_complete:
            print("   [OK] All analyses complete!")
            break
        
        time.sleep(2)
    
    elapsed = time.time() - start
    print(f"   Completed in {elapsed:.1f} seconds")
    
    # Check individual results
    print("\n4. ANALYSIS RESULTS")
    print("-" * 40)
    
    completed_count = 0
    for aid in analysis_ids:
        resp = requests.get(f"{BASE_URL}{API_PREFIX}/analyze/{aid}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'complete':
                completed_count += 1
                print(f"   {data.get('filename', 'Unknown')[:40]}: Complete")
                score = data.get('compliance_evaluation', {}).get('overall_score')
                if score:
                    print(f"     - Compliance Score: {score:.1f}%")
    
    print(f"\n   Completed: {completed_count}/{len(analysis_ids)}")
    
    # Try Lake Assessment
    print("\n5. LAKE ASSESSMENT")
    print("-" * 40)
    
    if completed_count >= 3:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/meta-analysis/trend",
            params={"submission_id": submission_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   [OK] Lake Assessment completed!")
                print(f"   Lakes analyzed: {result.get('lakes_analyzed')}")
                print(f"   Reports: {result.get('assessment_reports')}")
            else:
                print(f"   [INFO] {result.get('message')}")
        else:
            print(f"   [ERROR] {response.text}")
    else:
        print(f"   [SKIP] Only {completed_count} analyses complete (need 3)")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    # Check server
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code != 200:
            print("Server not running!")
            exit(1)
    except:
        print("ERROR: Server not running!")
        print("Start with: python main.py")
        exit(1)
    
    print("Server is running!")
    test_trend_analysis_fast()
