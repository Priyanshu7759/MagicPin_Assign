"""
Master Test Runner for magicpin AI Challenge — Vera Assistant
=============================================================
Runs all test suites:
1. Endpoint & Schema Integration Tests
2. 30 Canonical Test Pairs Validation
3. Official Judge Simulator & Groq LLM Tests
"""

import sys
import json
import re
import subprocess
from pathlib import Path

def print_header(title):
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70 + "\n")

def run_test(name, fn):
    try:
        fn()
        print(f"[PASS] {name}")
        return True
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return False

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def test_bot_endpoints():
    print("Running test_bot.py...")
    res = subprocess.run([sys.executable, "test_bot.py"], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr or res.stdout)
    print("  -> Bot REST API endpoints verified 100%")

def test_submission_schema():
    print("Verifying submission.jsonl schema...")
    lines = open("submission.jsonl", encoding="utf-8").readlines()
    assert len(lines) == 30, f"Expected 30 lines, got {len(lines)}"
    
    required_keys = {"test_id", "body", "cta", "send_as", "suppression_key", "rationale"}
    valid_ctas = {"open_ended", "binary_yes_no", "none", "multi_choice"}
    valid_send_as = {"vera", "merchant_on_behalf"}
    
    for idx, line in enumerate(lines, 1):
        data = json.loads(line)
        missing = required_keys - set(data.keys())
        assert not missing, f"Line {idx} missing keys: {missing}"
        assert data["cta"] in valid_ctas, f"Line {idx} invalid cta: {data['cta']}"
        assert data["send_as"] in valid_send_as, f"Line {idx} invalid send_as: {data['send_as']}"
        assert len(data["body"].strip()) > 10, f"Line {idx} body too short"
        assert len(data["rationale"].strip()) > 5, f"Line {idx} rationale missing"
    print("  -> 30 canonical test records verified 100%")

def test_judge_simulator():
    print("Running judge_simulator.py with Groq LLM...")
    res = subprocess.run([sys.executable, "judge_simulator.py"], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr or res.stdout)
    
    clean_stdout = strip_ansi(res.stdout)
    assert "[PASS] warmup" in clean_stdout, f"Warmup scenario missing. Output:\n{clean_stdout}"
    assert "[PASS] auto_reply" in clean_stdout, f"Auto-reply scenario missing. Output:\n{clean_stdout}"
    assert "[PASS] intent" in clean_stdout, f"Intent scenario missing. Output:\n{clean_stdout}"
    assert "[PASS] hostile" in clean_stdout, f"Hostile scenario missing. Output:\n{clean_stdout}"
    print("  -> Judge simulator & Groq LLM scenarios verified 100%")

def main():
    print_header("MAGICPIN AI CHALLENGE — MASTER TEST RUNNER")
    
    results = [
        ("REST API Endpoint Contract Test", test_bot_endpoints),
        ("30-Pair Submission Schema & Content Test", test_submission_schema),
        ("Official Judge Harness & Groq LLM Test", test_judge_simulator),
    ]
    
    passed_all = True
    for name, fn in results:
        success = run_test(name, fn)
        if not success:
            passed_all = False
            
    print_header("FINAL TESTING SUMMARY")
    if passed_all:
        print("[SUCCESS] ALL TEST SUITES PASSED 100%!".center(70))
    else:
        print("[FAILURE] SOME TESTS FAILED!".center(70))
        sys.exit(1)

if __name__ == "__main__":
    main()
