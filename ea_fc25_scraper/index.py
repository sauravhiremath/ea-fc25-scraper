import asyncio
import aiohttp
import json
import os
import argparse
import gzip
from typing import Dict, List, Any

BASE_URL = "https://drop-api.ea.com/rating/ea-sports-fc"
CACHE_DIR = "cache"
OUTPUT_FILE = "players_data.json"
COMPRESSED_OUTPUT_FILE = "players_data.json.gz"

async def fetch_page(session: aiohttp.ClientSession, offset: int) -> Dict[str, Any]:
    params = {
        "locale": "en",
        "limit": 100,
        "offset": offset
    }
    async with session.get(BASE_URL, params=params) as response:
        response.raise_for_status()
        return await response.json()

async def fetch_all_pages(skip_cache: bool) -> List[Dict[str, Any]]:
    all_data = []
    offset = 0
    
    async with aiohttp.ClientSession() as session:
        while True:
            cache_file = os.path.join(CACHE_DIR, f"page_{offset}.json")
            
            if not skip_cache and os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    page_data = json.load(f)
            else:
                try:
                    page_data = await fetch_page(session, offset)
                    os.makedirs(CACHE_DIR, exist_ok=True)
                    with open(cache_file, "w") as f:
                        json.dump(page_data, f)
                except aiohttp.ClientError as e:
                    print(f"Error fetching page at offset {offset}: {e}")
                    break

            all_data.extend(page_data["items"])
            
            if len(page_data["items"]) < 100:
                break
            
            offset += 100
    
    return all_data

def save_json(data: List[Dict[str, Any]], filename: str):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def compress_json(input_file: str, output_file: str):
    with open(input_file, "rb") as f_in:
        with gzip.open(output_file, "wb") as f_out:
            f_out.writelines(f_in)

def decompress_json(input_file: str, output_file: str):
    with gzip.open(input_file, "rb") as f_in:
        with open(output_file, "wb") as f_out:
            f_out.writelines(f_in)

async def main(skip_cache: bool):
    print("Fetching player data...")
    all_data = await fetch_all_pages(skip_cache)
    
    print(f"Total players fetched: {len(all_data)}")
    
    print(f"Saving data to {OUTPUT_FILE}...")
    save_json(all_data, OUTPUT_FILE)
    
    print(f"Compressing data to {COMPRESSED_OUTPUT_FILE}...")
    compress_json(OUTPUT_FILE, COMPRESSED_OUTPUT_FILE)
    
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EA Sports FC Player Data Crawler")
    parser.add_argument("--skip-cache", action="store_true", help="Skip using cached data")
    args = parser.parse_args()

    asyncio.run(main(skip_cache=args.skip_cache if args.skip_cache else False))