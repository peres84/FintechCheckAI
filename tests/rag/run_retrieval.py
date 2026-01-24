import json
from pathlib import Path

from backend.services.rag_service import retrieve_chunks


def main() -> None:
    data = json.loads(Path("parsed_output.json").read_text(encoding="utf-8"))
    query = "revenue growth"
    chunks = [{"content": page.get("text", "")} for page in data.get("pages", [])]
    results = retrieve_chunks(query, chunks, top_k=5)

    for item in results:
        print(f"score={item['score']:.3f} text={item['content'][:160]}")


if __name__ == "__main__":
    main()
