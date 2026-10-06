import argparse

from app.rag_service import RAGService


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect RAG retrieval without calling Claude.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    service = RAGService()
    contexts = service.retrieve(args.question, args.top_k)
    if not contexts:
        print("No contexts passed the relevance threshold.")
        return

    for i, item in enumerate(contexts, start=1):
        score = "n/a" if item.score is None else f"{item.score:.4f}"
        print(f"\n#{i} score={score} section={item.section}")
        print(f"IDs: {', '.join(item.requirement_ids) or '-'}")
        print(item.text[:800])


if __name__ == "__main__":
    main()
