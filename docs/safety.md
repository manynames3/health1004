# Safety Notes

This project is a document search and education system. It is not a clinical product.

The backend prompt requires the model to:

- Use only retrieved context.
- Avoid invented facts.
- Cite factual claims with document metadata.
- State when the corpus does not contain enough support.
- Avoid diagnosis, prescriptions, medication advice, and personal treatment plans.
- Encourage consulting a qualified professional for personal medical decisions.

The frontend displays a persistent disclaimer:

> This system summarizes uploaded documents and is not medical advice. Consult a qualified professional for medical decisions.

Recommended production additions:

- Log answer request ids, not full personal medical questions, if privacy requirements are strict.
- Add authentication if the corpus is private.
- Add review workflows for OCR low-confidence files.
- Add human evaluation for citation faithfulness before public use.
