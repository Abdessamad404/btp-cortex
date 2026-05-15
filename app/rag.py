from openai import OpenAI
from app.embedder import embed
from app.vector_store import search
from config import NVIDIA_API_KEY, NVIDIA_BASE_URL, LLM_MODEL, TOP_K

_client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)


def _get_client():
    return _client


def ask(question: str, projet: str = None) -> dict:
    """
    Full RAG pipeline — takes a question, returns an answer with sources.
    Optionally filter results to a specific project.
    """

    # Handle greetings and small talk before hitting Pinecone
    greetings = ["hi", "hello", "bonjour", "salut", "hey", "salam", "bonsoir"]
    if question.lower().strip().rstrip("!?.") in greetings:
        return {
            "answer": "Bonjour ! Je suis votre assistant BTP. Posez-moi une question sur vos documents et je vous répondrai avec précision.",
            "sources": [],
        }

    # Step 1 — embed the question into a vector
    question_vector = embed([question], input_type="query")[0]

    # Step 2 — find the most relevant chunks in Pinecone
    filter = {"projet": projet} if projet else None
    chunks = search(question_vector, top_k=TOP_K, filter=filter)

    if not chunks:
        return {
            "answer": "Je n'ai trouvé aucun document indexé pour répondre à cette question. Commencez par importer vos fichiers BTP via la page Upload, puis reposez votre question.",
            "sources": [],
        }

    # Step 3 — build the context block from retrieved chunks
    context = "\n\n---\n\n".join(
        f"[Source: {c.get('filename', 'inconnu')}]\n{c.get('text', '')}" for c in chunks
    )

    # Step 4 — build the prompt
    prompt = f"""Tu es un assistant expert en projets BTP (Bâtiment et Travaux Publics).
    Réponds à la question en utilisant UNIQUEMENT le contexte fourni ci-dessous.
    Si le contexte ne contient AUCUNE information pertinente pour répondre à la question, commence ta réponse OBLIGATOIREMENT par [INSUFFISANT]. Sinon, réponds avec ce que tu as, même si c'est partiel — ne invente rien.
    Cite toujours le(s) document(s) source(s) que tu as utilisé(s).

    Contexte:
    {context}

    Question: {question}

    Réponse:"""

    # Step 5 — call the LLM
    response = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # low temperature = more factual, less creative
        max_tokens=1024,
    )
    answer = response.choices[0].message.content

    # Only show sources if the LLM actually used them to answer
    used_sources = not answer.strip().startswith("[INSUFFISANT]")
    clean_answer = answer.strip().removeprefix("[INSUFFISANT]").strip()
    sources = (
        list({c.get("filename", "inconnu") for c in chunks}) if used_sources else []
    )

    return {"answer": clean_answer, "sources": sources}
