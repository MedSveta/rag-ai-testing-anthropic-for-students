from app.rag_service import RAGService


def main() -> None:
    service = RAGService()
    count = service.index_knowledge_base(replace=True)
    print(f"Indexed {count} chunks into ChromaDB.")


if __name__ == "__main__":
    main()
