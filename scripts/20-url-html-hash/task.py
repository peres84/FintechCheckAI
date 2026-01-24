import tower
import hashlib
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import pyarrow as pa


def fetch_html(url: str) -> str:
    """
    Fetch HTML content from a URL.
    
    Args:
        url: The URL to fetch HTML from
        
    Returns:
        The HTML content as a string
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    request = Request(url, headers=headers)
    
    with urlopen(request, timeout=30) as response:
        return response.read().decode('utf-8', errors='replace')


def calculate_hash(content: str) -> str:
    """
    Calculate SHA-256 hash of content.
    
    Args:
        content: The string content to hash
        
    Returns:
        The hexadecimal hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def main():
    url = os.getenv("URL", "")
    
    if url == "":
        print("URL parameter is required")
        return
    
    print(f"Fetching HTML from: {url}")
    
    # Step 1: Fetch HTML content from URL
    try:
        html_content = fetch_html(url)
        print(f"Successfully fetched {len(html_content)} characters")
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return
    
    # Step 2: Calculate hash of HTML content
    content_hash = calculate_hash(html_content)
    print(f"Content hash: {content_hash}")
    
    # Step 3: Prepare data for storage
    timestamp = datetime.utcnow().isoformat()
    
    data = pa.Table.from_pylist([{
        'url': url,
        'html_content': html_content,
        'content_hash': content_hash,
        'fetched_at': timestamp,
        'content_length': len(html_content)
    }])
    
    # Step 4: Get a reference to the table in Tower. Create if it doesn't exist.
    SCHEMA = pa.schema([
        ("url", pa.string()),
        ("html_content", pa.large_string()),  # large_string for potentially large HTML
        ("content_hash", pa.string()),
        ("fetched_at", pa.string()),
        ("content_length", pa.int64()),
    ])
    
    table = tower.tables("url_html_snapshots").create_if_not_exists(SCHEMA)
    
    # Step 5: Upsert data into the table (using url and content_hash as join columns
    # to avoid duplicates if same content is fetched again)
    table = table.upsert(data, join_cols=['url', 'content_hash'])
    
    print(f"Successfully stored HTML snapshot for {url}")
    print(f"Table: url_html_snapshots in default catalog")


if __name__ == "__main__":
    main()
