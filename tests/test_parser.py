from tracy.parser import TraceQueryParser
from tracy.grammar import get_default_grammar

def test_default_grammar():
    grammar = get_default_grammar()
    parser = TraceQueryParser(grammar)
    parser.get_sql_query("How much ?")

def test_sample_grammar():
    grammar = """
        S -> NP VP
        VP -> V NP | V NP PP
        V -> "saw" | "ate"
        NP -> "John" | "Mary" | "Bob" | Det N | Det N PP
        Det -> "a" | "an" | "the" | "my"
        N -> "dog" | "cat" | "cookie" | "park"
        PP -> P NP
        P -> "in" | "on" | "by" | "with"
    """
    parser = TraceQueryParser(grammar)
    parser.get_sql_query("Mary saw Bob")