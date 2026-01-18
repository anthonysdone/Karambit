#!/usr/bin/env python3
import subprocess
import os
import sys

# Define expected outputs for each test
TEST_EXPECTATIONS = {
    'arithmetic': {
        'contains': ['Arithmetic tests complete'],
        'description': 'Arithmetic operations (add, subtract, wraparound)'
    },
    'array': {
        'contains': ['Array test complete'],
        'description': 'Array storage and retrieval'
    },
    'comparison': {
        'contains': ['PASS: Equality test', 'PASS: Inequality test', 'Comparison tests complete'],
        'description': 'Equality and inequality comparisons'
    },
    'control': {
        'contains': ['Testing control flow', 'Control flow test complete'],
        'description': 'GOTO and IF...THEN...GOTO control flow'
    },
    'expressions': {
        'contains': ['Expression tests complete'],
        'description': 'Expression evaluation'
    },
    'grid': {
        'contains': ['Grid test complete'],
        'description': 'Grid operations for cellular automata'
    },
    'random': {
        'contains': ['Random test complete'],
        'description': 'Random number generation'
    },
    'screen': {
        'contains': ['Screen test complete'],
        'description': 'Screen buffer and rendering'
    },
    'strings': {
        'contains': ['Hello from BASIC!', 'Multiple strings work', 'String tests complete'],
        'description': 'String printing and handling'
    },
    'variables': {
        'contains': ['Variables A-J assigned', 'Variable test complete'],
        'description': 'Variable assignment and retrieval'
    },
    'integration': {
        'contains': ['Starting integration test', 'Integration test complete'],
        'description': 'Combined feature integration test'
    },
}

tests = sorted([f for f in os.listdir('software/unit') if f.startswith('test_') and f.endswith('.tb')])

print("=" * 80)
print("KARAMBIT UNIT TEST SUITE - WITH OUTPUT VALIDATION")
print("=" * 80)

passed = 0
failed = 0
errors = []

for test in tests:
    test_path = f'software/unit/{test}'
    test_name = test.replace('test_', '').replace('.tb', '')
    
    try:
        result = subprocess.run(['python3', 'run.py', test_path], 
                              capture_output=True, text=True, timeout=3)
        
        output = result.stdout
        
        # Check if test ran without error
        if result.returncode != 0:
            print(f"\n✗ FAIL: {test_name:20s} - Runtime Error")
            failed += 1
            errors.append((test_name, f"Exit code {result.returncode}: {result.stderr[:200]}"))
            continue
        
        # Check expected outputs
        test_config = TEST_EXPECTATIONS.get(test_name)
        if test_config is None:
            print(f"\n⚠ SKIP: {test_name:20s} - No test definition")
            continue
        
        expected = test_config.get('contains', [])
        missing = []
        for expected_str in expected:
            if expected_str not in output:
                missing.append(expected_str)
        
        if not missing:
            print(f"\n✓ PASS: {test_name:20s}")
            print(f"         {test_config['description']}")
            passed += 1
        else:
            print(f"\n✗ FAIL: {test_name:20s}")
            print(f"         {test_config['description']}")
            failed += 1
            error_msg = f"Missing expected output(s):\n"
            for m in missing:
                error_msg += f"  - '{m}'\n"
            error_msg += f"\nActual output:\n{output[:300]}"
            errors.append((test_name, error_msg))
            
    except subprocess.TimeoutExpired:
        print(f"\n✗ TIMEOUT: {test_name:20s}")
        failed += 1
        errors.append((test_name, "Test timed out after 3 seconds"))
    except Exception as e:
        print(f"\n✗ ERROR: {test_name:20s}")
        failed += 1
        errors.append((test_name, str(e)))

print("\n" + "=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
print("=" * 80)

if errors:
    print("\n" + "FAILED TEST DETAILS".center(80))
    print("=" * 80)
    for name, error in errors:
        print(f"\n{name}:")
        print("-" * 40)
        print(error)

sys.exit(0 if failed == 0 else 1)
