#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test HTML Cleaner - Verify HTML cleaning"""

import sys
import io
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.html_cleaner import HTMLCleaner

TEST_CASES = [
    {"name": "Simple paragraph", "input": "<p>Hello <b>World</b></p>", "contains": ["Hello", "World"]},
    {"name": "Multiple paragraphs", "input": "<p>First</p><p>Second</p>", "contains": ["First", "Second"]},
    {"name": "HTML entities", "input": "<p>Hello &nbsp; World &amp; Test</p>", "contains": ["Hello", "World", "Test"]},
    {"name": "Script removed", "input": "<p>Text</p><script>alert('hi')</script><p>More</p>", "contains": ["Text", "More"], "not_contains": ["alert"]},
    {"name": "Style removed", "input": "<p>Text</p><style>.c{color:red}</style><p>More</p>", "contains": ["Text", "More"], "not_contains": ["color"]},
    {"name": "Image removed", "input": "<p>Check image:</p><img src='t.jpg'><p>Nice!</p>", "contains": ["Check", "Nice"], "not_contains": ["img"]},
    {"name": "Links cleaned", "input": '<p>Visit <a href="http://ex.com">site</a></p>', "contains": ["Visit", "site"]},
    {"name": "Verge content", "input": '<figure><img src="test.png"/></figure><p>Article content here</p>', "contains": ["Article content"], "not_contains": ["figure", "img"]},
]

def test():
    print("\n" + "=" * 70)
    print("HTML Cleaner Tests")
    print("=" * 70 + "\n")

    passed = failed = 0
    for tc in TEST_CASES:
        result = HTMLCleaner.clean(tc["input"])
        ok = True
        errors = []

        for exp in tc.get("contains", []):
            if exp not in result:
                ok = False
                errors.append(f"  Missing: {exp}")

        for exp in tc.get("not_contains", []):
            if exp in result:
                ok = False
                errors.append(f"  Should not have: {exp}")

        status = "[OK]" if ok else "[FAIL]"
        print(f"{status} {tc['name']}")

        if not ok:
            print(f"  Input:  {tc['input'][:60]}")
            print(f"  Output: {result[:70]}")
            for err in errors:
                print(err)
            failed += 1
        else:
            passed += 1
        print()

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    return failed == 0

if __name__ == "__main__":
    success = test()
    sys.exit(0 if success else 1)
