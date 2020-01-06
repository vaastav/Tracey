from tracy.parser import TraceQueryParser
from tracy.grammar import get_default_grammar

def main():
    grammar = get_default_grammar()
    parser = TraceQueryParser('traces.fcfg')
    query = parser.get_sql_query("How much ?")
    print(query)

if __name__ == '__main__':
    main()