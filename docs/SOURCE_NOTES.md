# Source Notes — PhoneBook SRS 2.0

These notes are **not indexed into the RAG knowledge base**. They document source-quality observations for instructors and students without contaminating retrieval/evaluation data.

The source SRS contains wording inconsistencies or apparent typos. The product knowledge in `knowledge/requirements.md` preserves the source requirements rather than silently inventing corrections.

Examples:

1. Requirements **T49–T53** are absent.
2. The Login module contains an unclear Manager description referring to customer registration.
3. **T37** is under Contact Address but says "Contact name must have minimum 1 symbol".
4. **T38** says "Phone Number address is required".
5. Functional requirements **F10–F14** repeatedly mention saving invalid data to the "name field", even for last name, email, phone, and address validation.
6. Password requirement **T10** can be read ambiguously when compared with T9 and T13.

## Training rule

When the source is missing or ambiguous, the application should not invent a requirement. Test/evaluation prompts must not be added to the knowledge base.
