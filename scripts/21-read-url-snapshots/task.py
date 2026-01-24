import tower
import polars as pl


def main():
    """
    Read and display contents from the url_html_snapshots table.
    """
    
    # Step 1: Get a reference to the table and read it
    print("Loading table: url_html_snapshots from default catalog...")
    
    try:
        df = tower.tables("url_html_snapshots").load().read()
    except Exception as e:
        print(f"Error loading table: {e}")
        print("Make sure the table exists by running the url-html-hash app first.")
        return
    
    # Step 2: Print summary statistics
    print(f"\n{'='*60}")
    print(f"Table: url_html_snapshots")
    print(f"Total rows: {len(df)}")
    print(f"{'='*60}\n")
    
    # Step 3: Print each row (truncating HTML content for readability)
    for i, row in enumerate(df.iter_rows(named=True)):
        print(f"--- Record {i + 1} ---")
        print(f"URL: {row['url']}")
        print(f"Content Hash: {row['content_hash']}")
        print(f"Fetched At: {row['fetched_at']}")
        print(f"Content Length: {row['content_length']} characters")
        
        # Truncate HTML content for display
        html_content = row['html_content'] or ""
        html_preview = html_content[:200]
        if len(html_content) > 200:
            html_preview += "..."
        print(f"HTML Preview: {html_preview}")
        print()
    
    # Step 4: Print schema info
    print(f"{'='*60}")
    print("Schema:")
    print(df.schema)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
