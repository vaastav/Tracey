def get_default_grammar():
    rules = """
        S -> Det Term
        Det -> "What" | "How" Qual | "Where"
        Term -> "?"
        Qual -> "much" | "many"
    """
    return rules