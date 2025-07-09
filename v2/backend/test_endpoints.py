#!/usr/bin/env python3
"""
Test script to check all endpoints are working properly
"""
import requests
import json
from typing import Dict, Any

def test_endpoint(method: str, url: str, data: Dict[Any, Any] = None, expected_status: int = 200) -> bool:
    """Test an endpoint and return True if successful"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, timeout=10)
        else:
            print(f"❌ {method} {url} - Unsupported method")
            return False

        if response.status_code == expected_status:
            print(f"✅ {method} {url} - Status {response.status_code}")
            return True
        else:
            print(f"❌ {method} {url} - Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {method} {url} - Error: {str(e)}")
        return False

def main():
    """Test all main endpoints"""
    base_url = "http://localhost:8000/api/v1"

    # Test basic endpoints
    tests = [
        # Health check
        ("GET", f"{base_url}/health", None, 200),

        # Scrapers endpoints
        ("GET", f"{base_url}/scrapers/urls", None, 200),

        # Channels endpoints
        ("GET", f"{base_url}/channels/", None, 200),

        # Config endpoints
        ("GET", f"{base_url}/config/all", None, 200),
        ("GET", f"{base_url}/config/base_url", None, 200),
        ("GET", f"{base_url}/config/ace_engine_url", None, 200),

        # EPG endpoints
        ("GET", f"{base_url}/epg/sources", None, 200),

        # TV Channels endpoints
        ("GET", f"{base_url}/tv-channels/", None, 200),

        # Search endpoints
        ("GET", f"{base_url}/search/channels", None, 200),

        # Playlist endpoints
        ("GET", f"{base_url}/playlists/m3u", None, 200),
    ]

    print("Testing all endpoints...")
    print("=" * 50)

    passed = 0
    total = len(tests)

    for method, url, data, expected_status in tests:
        if test_endpoint(method, url, data, expected_status):
            passed += 1

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All endpoints are working correctly!")
        return True
    else:
        print("⚠️  Some endpoints have issues")
        return False

if __name__ == "__main__":
    main()

# This file is disabled because it is a legacy test not compatible with FastAPI.
# Please see MIGRATION_GAPS.md for details.
