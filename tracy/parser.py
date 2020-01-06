import nltk

def traverse_tree(tree):
    print("tree:", tree)
    print(tree.label())
    for subtree in tree.subtrees():
        if subtree == tree:
            continue
        if type(subtree) == nltk.tree.Tree:
            traverse_tree(subtree)

class TraceQueryParser:
    def __init__(self, grammar):
        self.parser = nltk.load_parser(grammar)

    def get_parsed_tree_object(self, nl_query):
        split_query = nl_query.split()
        trees = []
        for tree in self.parser.parse(split_query):
            trees += [tree]
        return trees[0]

    def get_sql_query(self, nl_query):
        """
        nl_query (str): A natural language query to be converted into a sql query
        """

        tree = self.get_parsed_tree_object(nl_query)
        query = tree.label()['SEM']
        query = [s for s in query if s]
        query = ' '.join(query) + ';'
        return query