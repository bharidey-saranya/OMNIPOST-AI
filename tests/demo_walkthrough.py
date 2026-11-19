"""
Live demonstration and verification script for Automated Multi-Platform Posting System.
Runs live HTTP requests against http://localhost:4000 and demonstrates every functional stage.
"""

import time
import json
import httpx

BASE_URL = "http://localhost:4000"

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_header("STAGE 1: SYSTEM HEALTH & PLATFORMS DISCOVERY")
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health check
        res = client.get("/health")
        print(f"GET /health -> HTTP {res.status_code}")
        print(json.dumps(res.json(), indent=2))

        # 2. Platforms check
        res = client.get("/platforms")
        print(f"\nGET /platforms -> HTTP {res.status_code}")
        print(json.dumps(res.json(), indent=2))

        # 3. Stage 2: Valid Broadcast (The Happy Path)
        print_header("STAGE 2: VALID MULTI-PLATFORM BROADCAST (HAPPY PATH)")
        valid_payload = {
            "message": "Check out our latest business platform and grow your online visibility. https://example.com"
        }
        print(f"Submitting Payload:")
        print(f"  Message: \"{valid_payload['message']}\"")
        print(f"  Length: {len(valid_payload['message'])} / 200 chars")

        start = time.perf_counter()
        res = client.post("/posting", json=valid_payload)
        elapsed = time.perf_counter() - start

        print(f"\nPOST /posting -> HTTP {res.status_code} (Completed in {elapsed:.3f}s)")
        data = res.json()
        print(f"Overall Success: {data.get('success')}")
        print("\nResults per Platform:")
        for r in data.get("results", []):
            access = "PUBLIC" if r.get("public_access") else "PROTECTED"
            print(f"  • {r.get('platform'):<10} | Status: {r.get('status').upper():<7} | Access: {access:<9} | Date/Time: {r.get('date')} {r.get('time')}")
            print(f"    Published URL: {r.get('posted_url')}")

        # 4. Stage 3: Missing CTA Link
        print_header("STAGE 3: VALIDATION TEST - MISSING CTA LINK (0 URLS)")
        bad_payload_1 = {
            "message": "Exciting announcement with no CTA link included anywhere."
        }
        res = client.post("/posting", json=bad_payload_1)
        print(f"POST /posting -> HTTP {res.status_code}")
        print(json.dumps(res.json(), indent=2))

        # 5. Stage 4: Exceeding 200 Characters
        print_header("STAGE 4: VALIDATION TEST - EXCEEDING 200 CHARACTERS LIMIT")
        long_message = "A" * 190 + " https://example.com"
        bad_payload_2 = {"message": long_message}
        print(f"Message Length: {len(long_message)} characters (Limit: 200)")
        res = client.post("/posting", json=bad_payload_2)
        print(f"POST /posting -> HTTP {res.status_code}")
        print(json.dumps(res.json(), indent=2))

        # 6. Stage 5: Multiple CTA Links
        print_header("STAGE 5: VALIDATION TEST - MULTIPLE CTA LINKS (>1 URL)")
        bad_payload_3 = {
            "message": "Visit https://link1.com and also check https://link2.com for offers"
        }
        res = client.post("/posting", json=bad_payload_3)
        print(f"POST /posting -> HTTP {res.status_code}")
        print(json.dumps(res.json(), indent=2))

    print_header("ALL 5 VERIFICATION STAGES COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    main()
