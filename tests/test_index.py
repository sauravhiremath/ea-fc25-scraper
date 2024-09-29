import types

import aiohttp
import pytest
import json
import os
import gzip
from aioresponses import aioresponses
from unittest.mock import patch

from ea_fc25_scraper.index import (
    fetch_page, fetch_all_pages, save_json, compress_json, decompress_json, main,
    BASE_URL, OUTPUT_FILE, COMPRESSED_OUTPUT_FILE
)

@pytest.fixture
def mock_json_response():
    return {
        "items": [
            {"id": 1, "name": "Player 1"},
            {"id": 2, "name": "Player 2"}
        ]
    }

@pytest.mark.asyncio
async def test_fetch_page(mock_json_response):
    with aioresponses() as m:
        m.get(f"{BASE_URL}?locale=en&limit=100&offset=0", payload=mock_json_response)
        
        async with aiohttp.ClientSession() as session:
            result = await fetch_page(session, 0)
        
        assert result == mock_json_response

@pytest.mark.asyncio
async def test_fetch_page_error():
    with aioresponses() as m:
        m.get(f"{BASE_URL}?locale=en&limit=100&offset=0", status=404)
        
        with pytest.raises(aiohttp.ClientResponseError):
            async with aiohttp.ClientSession() as session:
                await fetch_page(session, 0)

@pytest.mark.asyncio
async def test_fetch_all_pages_no_cache(mock_json_response, tmp_path):
    with aioresponses() as m:
        m.get(f"{BASE_URL}?locale=en&limit=100&offset=0", payload=mock_json_response)
        m.get(f"{BASE_URL}?locale=en&limit=100&offset=100", payload={"items": []})
        
        with patch("ea_fc25_scraper.index.CACHE_DIR", str(tmp_path)):
            results = await fetch_all_pages(skip_cache=True)

    assert results == mock_json_response["items"]
    
    # Check that the cache file was created
    cache_file = os.path.join(str(tmp_path), "page_0.json")
    assert os.path.exists(cache_file)
    
    # Verify cache file contents
    with open(cache_file, 'r') as f:
        cached_data = json.load(f)
    assert cached_data == mock_json_response

@pytest.mark.asyncio
async def test_fetch_all_pages_with_cache(tmp_path):
    cache_data = {
        "items": [
            {"id": 3, "name": "Cached Player"}
        ]
    }
    cache_file = tmp_path / "page_0.json"
    cache_file.write_text(json.dumps(cache_data))

    with patch("ea_fc25_scraper.index.CACHE_DIR", str(tmp_path)):
        results = await fetch_all_pages(skip_cache=False)

    assert results == cache_data["items"]

@pytest.mark.asyncio
async def test_fetch_all_pages_multiple_pages():
    responses = [
        {"items": [{"id": i} for i in range(100)]},
        {"items": [{"id": i} for i in range(100, 150)]},
        {"items": []}
    ]
    
    with aioresponses() as m:
        for i, resp in enumerate(responses):
            m.get(f"{BASE_URL}?locale=en&limit=100&offset={i*100}", payload=resp)
        
        results = await fetch_all_pages(skip_cache=True)

    assert len(results) == 150

def test_save_json(tmp_path):
    data = [{"id": 1, "name": "Test Player"}]
    filename = tmp_path / "test_output.json"
    
    save_json(data, str(filename))
    
    assert filename.exists()
    with open(filename, "r") as f:
        saved_data = json.load(f)
    assert saved_data == data

def test_compress_json(tmp_path):
    input_data = [{"id": 1, "name": "Test Player"}]
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json.gz"
    
    with open(input_file, "w") as f:
        json.dump(input_data, f)
    
    compress_json(str(input_file), str(output_file))
    
    assert output_file.exists()
    with gzip.open(output_file, "rb") as f:
        compressed_data = json.loads(f.read().decode("utf-8"))
    assert compressed_data == input_data

def test_decompress_json(tmp_path):
    input_data = [{"id": 1, "name": "Test Player"}]
    input_file = tmp_path / "input.json.gz"
    output_file = tmp_path / "output.json"
    
    with gzip.open(input_file, "wb") as f:
        f.write(json.dumps(input_data).encode("utf-8"))
    
    decompress_json(str(input_file), str(output_file))
    
    assert output_file.exists()
    with open(output_file, "r") as f:
        decompressed_data = json.load(f)
    assert decompressed_data == input_data

@pytest.mark.asyncio
async def test_main(tmp_path):
    mock_data = [{"id": 1, "name": "Test Player"}]
    
    with patch("ea_fc25_scraper.index.fetch_all_pages", return_value=mock_data), \
         patch("ea_fc25_scraper.index.save_json") as mock_save, \
         patch("ea_fc25_scraper.index.compress_json") as mock_compress, \
         patch("ea_fc25_scraper.index.OUTPUT_FILE", str(tmp_path / OUTPUT_FILE)), \
         patch("ea_fc25_scraper.index.COMPRESSED_OUTPUT_FILE", str(tmp_path / COMPRESSED_OUTPUT_FILE)):
        
        await main(skip_cache=True)
        
        mock_save.assert_called_once_with(mock_data, str(tmp_path / OUTPUT_FILE))
        mock_compress.assert_called_once_with(str(tmp_path / OUTPUT_FILE), str(tmp_path / COMPRESSED_OUTPUT_FILE))

@pytest.mark.asyncio
async def test_main_with_error(capsys):
    with patch("ea_fc25_scraper.index.fetch_all_pages", side_effect=Exception("Test error")):
        with pytest.raises(Exception):
            await main(skip_cache=True)
