from flask import Flask, request
import json
import sys
from networkx import DiGraph
from networkx.algorithms import is_directed_acyclic_graph
from networkx.algorithms.traversal.edgedfs import edge_dfs
from mysql.connector import Error, connect
import urllib.request

api = Flask(__name__)
connection = {}

@api.route("/summary/", methods=['GET'])
def summary():
    trace_id = request.args.get("query")
    with urllib.request.urlopen("http://198.162.52.119:9000/traces/" + trace_id) as url:
        events = json.loads(url.read().decode())
    
    eventInfo = {}
    eventGraph = DiGraph()

    for event in events:
        eventInfo[event["EventID"]] = event
        eventGraph.add_node(event["EventID"])
        if(event["ParentEventID"] != None):
            for parentID in event["ParentEventID"]:
                eventGraph.add_edge(''.join(event["ParentEventID"]), event["EventID"])
    if(is_directed_acyclic_graph(eventGraph)):
       dfsResult = edge_dfs(eventGraph)
       print(list(dfsResult))
       return("done")
    else:
        return "This was not a DAG, check your input data"

def main():
    global connection
    if len(sys.argv) != 2:
        print("Usage: python tracey.py <config_file>")
        sys.exit(1)
    config_file = sys.argv[1]
    with open(config_file, 'r+') as inf:
        config = json.load(inf)
        db_host = config["db_host"]
        database = config["db"]
        user = config["username"]
        password = config["pwd"]
        try:
            connection = connect(host=db_host, database=database, user=user, password=password)
            if connection.is_connected():
                print("Connected to MySQL server")
        except Error as e:
            print("Error while connecting to database", e)
            sys.exit(1)
    api.run(host=config["host"], port=config["port"])

if __name__ == '__main__':
    main()
