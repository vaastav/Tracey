import nltk
from nltk import CFG

class TraceQueryParser:
    def __init__(self, grammar):
        parsed_grammar = CFG.fromstring(grammar)
        self.parser = nltk.RecursiveDescentParser(parsed_grammar)

    def get_sql_query(self, nl_query):
        """
        nl_query (str): A natural language query to be converted into a sql query
        """

        split_query = nl_query.split()
        for p in self.parser.parse(split_query):
            print(p)