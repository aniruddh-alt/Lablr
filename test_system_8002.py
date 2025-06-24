#!/usr/bin/env python3
"""
Modified Lablr System Test Script for port 8002

This script performs basic tests to verify that the Lablr system is working correctly.
Run this after starting the system to ensure everything is configured properly.

Usage:
    python test_system_8002.py
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

class LablrTester:
    """Test the Lablr system functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.test_results = []
    
    async def test_health_check(self):
        """Test the health check endpoint."""
        print("🔍 Testing health check...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Health check passed")
                        print(f"   Status: {data.get('status')}")
                        return True
                    else:
                        print(f"❌ Health check failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_api_documentation(self):
        """Test that API documentation is accessible."""
        print("🔍 Testing API documentation...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/docs") as response:
                    if response.status == 200:
                        print("✅ API documentation accessible")
                        return True
                    else:
                        print(f"❌ API documentation failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ API documentation test failed: {e}")
            return False
    
    async def test_extraction_endpoints(self):
        """Test that extraction endpoints are working."""
        print("🔍 Testing extraction endpoints...")
        try:
            # Test extraction jobs list endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/extraction/jobs") as response:
                    if response.status == 200:
                        print("✅ Extraction jobs endpoint working")
                        return True
                    else:
                        print(f"❌ Extraction jobs endpoint failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Extraction endpoints test failed: {e}")
            return False
    
    async def test_document_endpoints(self):
        """Test document management endpoints."""
        print("🔍 Testing document endpoints...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/documents") as response:
                    if response.status == 200:
                        print("✅ Document endpoints working")
                        return True
                    else:
                        print(f"❌ Document endpoints failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Document endpoints test failed: {e}")
            return False
    
    async def test_mock_extraction_job(self):
        """Test creating a mock extraction job."""
        print("🔍 Testing mock extraction job creation...")
        try:
            job_config = {
                "name": "Test Job",
                "description": "System test job",
                "document_ids": ["test_doc_1"],
                "extraction_type": "structured_data",
                "output_format": "json",
                "prompt": "Extract any available data from the document",
                "batch_size": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/extraction/jobs",
                    json=job_config
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Mock extraction job created successfully")
                        print(f"   Job ID: {data.get('id')}")
                        return True
                    else:
                        text = await response.text()
                        print(f"❌ Mock extraction job failed: HTTP {response.status}")
                        print(f"   Response: {text}")
                        return False
        except Exception as e:
            print(f"❌ Mock extraction job test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all system tests."""
        print("🎯 Running Lablr System Tests")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("API Documentation", self.test_api_documentation),
            ("Document Endpoints", self.test_document_endpoints),
            ("Extraction Endpoints", self.test_extraction_endpoints),
            ("Mock Extraction Job", self.test_mock_extraction_job),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                result = await test_func()
                if result:
                    passed += 1
                self.test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                self.test_results.append((test_name, False))
        
        print("\n" + "=" * 50)
        print("🏁 Test Results Summary")
        print("=" * 50)
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your Lablr system is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the configuration and try again.")
            return False

async def main():
    """Main test runner."""
    tester = LablrTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
