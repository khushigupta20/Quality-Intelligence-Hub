"""
Test script to verify 5 WHYs and preventive measures generation
"""

import sys
import io
sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.utils.analyzer import DefectAnalyzer
import json

# Create a simple test CSV
test_data = """Id,Summary,Status,Severity,Module
DEF-001,Login button not working,Open,High,Login
DEF-002,Login timeout after 30 seconds,Open,High,Login
DEF-003,Password reset email not sent,Open,Critical,Auth
DEF-004,Authentication token expired,Open,High,Auth
DEF-005,Session timeout too short,Open,Medium,Session"""

# Write test file
with open('test_defects.csv', 'w') as f:
    f.write(test_data)

print("=" * 60)
print("Testing Defect Analyzer with 5 WHYs")
print("=" * 60)

# Run analyzer
analyzer = DefectAnalyzer('test_defects.csv')
if analyzer.load_data():
    print("✅ Data loaded successfully")
    results = analyzer.run_analysis()
    
    print(f"\n📊 Total defects: {results['total_defects']}")
    print(f"📊 RCA candidates: {len(results.get('rca_candidates', []))}")
    
    # Check preventive measures
    measures = results.get('preventive_measures', [])
    print(f"\n🛡️ Preventive measures generated: {len(measures)}")
    
    if measures:
        print("\n" + "=" * 60)
        print("PREVENTIVE MEASURES DETAILS:")
        print("=" * 60)
        
        for i, measure in enumerate(measures, 1):
            print(f"\n{i}. {measure.get('category', 'Unknown')}")
            print(f"   Icon: {measure.get('icon', 'N/A')}")
            
            # Check for 5 WHYs
            if 'five_whys' in measure:
                print("   ✅ Has 5 WHYs analysis")
                five_whys = measure['five_whys']
                print(f"      - Why 1: {five_whys.get('why1', 'N/A')[:50]}...")
                print(f"      - Root Cause: {five_whys.get('root_cause', 'N/A')[:60]}...")
            else:
                print("   ❌ Missing 5 WHYs analysis")
            
            # Check for immediate actions
            if 'immediate_actions' in measure:
                print(f"   ✅ Has {len(measure['immediate_actions'])} immediate actions")
            else:
                print("   ❌ Missing immediate actions")
            
            # Check for long-term prevention
            if 'long_term_prevention' in measure:
                print(f"   ✅ Has {len(measure['long_term_prevention'])} long-term prevention items")
            else:
                print("   ❌ Missing long-term prevention")
            
            # Check for measures
            if 'measures' in measure:
                print(f"   ✅ Has {len(measure['measures'])} general measures")
    else:
        print("\n❌ NO PREVENTIVE MEASURES GENERATED!")
        print("This is the problem - measures array is empty")
    
    # Save full results for inspection
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n💾 Full results saved to test_results.json")
    
else:
    print("❌ Failed to load data")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)

# Made with Bob
