import base64

from openai import OpenAI

from config import NVIDIA_API_KEY, NVIDIA_BASE_URL, VISION_MODEL

# Same OpenAI-compatible client as rag.py, just pointed at NIM.
# The vision model accepts both text and image in the same request.
client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)


def analyze_photo(filepath: str, description_utilisateur: str = "") -> str:
    """
    Send a construction site photo to the NIM vision model and get back
    a detailed French text description ready to be chunked and indexed.

    How it works:
    - The image is read from disk and encoded in base64
      (base64 = standard way to turn binary files into plain text for APIs)
    - We send both the image and a BTP-specific prompt in a single API call
    - The vision model returns a text description of what it sees
    - That text is what gets indexed in Pinecone, just like any other document

    Args:
        filepath: absolute path to the image file (JPG or PNG)
        description_utilisateur: optional short context provided by the user
                                  (e.g. "Coffrage niveau R+2, lot gros-oeuvre")
                                  Helps the model focus its analysis.

    Returns:
        A detailed text description of the photo, in French.
    """

    # Read the image file from disk and encode it in base64
    with open(filepath, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Detect image format from file extension to set the correct MIME type
    # MIME type tells the API what kind of file it is receiving
    extension = filepath.lower().rsplit(".", 1)[-1]
    mime_type = "image/png" if extension == "png" else "image/jpeg"

    # Optionally inject the user's context hint into the prompt
    context_hint = (
        f"\nContexte fourni par l'utilisateur : {description_utilisateur}"
        if description_utilisateur
        else ""
    )

    prompt = (
        "Tu es un expert en chantiers BTP (Bâtiment et Travaux Publics). "
        "Analyse cette photo de chantier en détail.\n"
        "Décris :\n"
        "- Ce que tu vois (type de travaux, matériaux, équipements, structures)\n"
        "- L'état d'avancement apparent des travaux\n"
        "- Toute anomalie, non-conformité ou risque visible\n"
        "- Les conditions générales du chantier (ordre, sécurité, propreté)\n"
        f"{context_hint}\n\n"
        "Sois précis, factuel, et utilise le vocabulaire technique BTP approprié. "
        "Ta description sera indexée dans une base de connaissances et interrogée "
        "par des ingénieurs et chefs de chantier."
    )

    # OpenAI multimodal message format:
    # "content" is a list — first the image, then the text prompt.
    # The model processes both together in a single inference pass.
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            # Data URL format: data:<mime>;base64,<encoded_bytes>
                            "url": f"data:{mime_type};base64,{image_data}"
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
        # Low temperature = factual, deterministic output (less creative invention)
        temperature=0.2,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()
