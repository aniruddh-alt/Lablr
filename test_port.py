#!/usr/bin/env python3
import asyncio
import aiohttp
import sys

async def test_health():
    """Test the health check endpoint."""
    print("🔍 Testing health check on port 8001...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/health") as response:
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

async def main():
    await test_health()

if __name__ == "__main__":
    asyncio.run(main())
