# rational_onion/services/nlp_service.py

import os
import spacy
import requests
from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple
from collections import Counter

nlp = spacy.load("en_core_web_md")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def enhance_argument_with_nlp(text: str) -> List[str]:
    """
    Enhances an argument component using NLP-based reformulation, lexical diversity, etc.
    """
    doc = nlp(text)
    suggestions = []
    token_freq = Counter([token.lemma_ for token in doc if token.is_alpha])

    for token in doc:
        if token.pos_ in ["NOUN", "VERB"] and token.dep_ not in ["aux", "det"]:
            if token_freq[token.lemma_] > 1:
                suggestions.append(f"Consider using synonyms for '{token.text}' to improve lexical diversity.")
            else:
                suggestions.append(f"Ensure '{token.text}' is well-supported by evidence.")

    if len(doc) < 10:
        suggestions.append("Consider expanding the argument for better clarity and depth.")

    return suggestions if suggestions else ["Ensure clarity, logical consistency, and sufficient support for claims."]

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Computes the cosine similarity between two text embeddings.
    """
    embedding1 = embedding_model.encode(text1, convert_to_tensor=True)
    embedding2 = embedding_model.encode(text2, convert_to_tensor=True)
    return util.pytorch_cos_sim(embedding1, embedding2).item()

async def rank_references_with_embeddings(query: str) -> List[Tuple[str, float, int, str]]:
    """
    Placeholder for reference ranking logic using embeddings, citation count, etc.
    Returns List of (title, citationCount, year, URL).
    """
    # Here you'd expand your query, fetch references, then rank them
    # We'll just return a placeholder
    return [("Placeholder Title", 0.8, 2023, "http://example.com")]