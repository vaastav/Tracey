def get_default_grammar():
    rules = """
        % start S
        S[SEM=(?int + ?term)] -> Int[SEM=?int] Term[SEM=?term]
        Int[SEM='SELECT'] -> "What" | "Where"
        Int[SEM=('SELECT' + ?qual)] -> "How" Qual[SEM=?qual]
        Term[SEM=''] -> "?"
        Qual[SEM='COUNT(*)'] -> "much" | "many"
    """
    return rules