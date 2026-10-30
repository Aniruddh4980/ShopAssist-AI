"""Dispatch a user query to the chain selected by the semantic router."""

UNKNOWN_RESPONSE = (
    "Sorry, I couldn't quite catch that. Could you try rephrasing or asking "
    "about products or store policies?"
)


def ask(query: str) -> tuple[str, str]:
    """Return the response text and the name of the chain that answered."""
    # Import on demand so dispatch can be tested without loading model clients.
    from router import router
    from faq import faq_chain
    from sql import sql_chain

    route = router(query).name
    if route == "faq":
        return faq_chain(query), "faq"
    if route == "sql":
        return sql_chain(query), "sql"
    return UNKNOWN_RESPONSE, "unknown"
