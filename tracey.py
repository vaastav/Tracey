from flask import Flask, request
import json
import sys
import scipy.stats
from networkx import DiGraph
from networkx.algorithms import is_directed_acyclic_graph
from networkx.algorithms.traversal.edgedfs import edge_dfs
from mysql.connector import Error, connect
import urllib.request

api = Flask(__name__)
connection = {}

def get_events(trace_id):
    events = []
    with urllib.request.urlopen("http://198.162.52.119:9000/traces/" + trace_id) as url:
        events = json.loads(url.read().decode())
    return events

def get_tasks(trace_id):
    tasks = []
    with urllib.request.urlopen("http://198.162.52.119:9000/tasks/" + trace_id) as url:
        tasks = json.loads(url.read().decode())
    return tasks

def generate_trace_summary(events, tasks):
    summary = ""
    anomalous_events_set = {}

    percentile_scores = {}
    concurrent_tasks = {}
    task_name = {}
    task_events = {}
    for task in tasks:
        task_id = task['ProcessName'] + str(task['ProcessID']) + str(task['ThreadID'])
        task_name[task_id] = task['Operation']
        # For each task calculate it's percentile score w.r.t to the distribution
        percentile = stats.percentileofscore(task['Data'], task['Duration'])
        percentile_scores[task_id] = percentile
        # For each task figure out how many other consequent tasks are being run
        # Approximate this by figuring out how many concurrent tasks there were during
        # the full duration of the task. 
        num_tasks = len(task['MolehillData'])
        concurrent_tasks[task_id] = num_tasks
        # Initialize the events array for each task
        task_events[task_id] = []

    eventInfo = {}
    eventGraph = DiGraph()
    # Group events by task, and 
    # Then shomehow concatenate the summaries from the tasks based on the graph structure
    for event in events:
        eventInfo[event["EventID"]] = event
        eventGraph.add_node(event["EventID"])
        if(event["ParentEventID"] != None):
            for parentID in event["ParentEventID"]:
                eventGraph.add_edge(''.join(event["ParentEventID"]), event["EventID"])
        # Get all the anomalous events
        if event["Probability"] < 0.25:
            anomalous_events_set.add(event['EventID'])
        # Put the events in each task
        task_id = event['ProcessName'] + str(event['ProcessID']) + str(event['ThreadID'])
        task_events[task_id] += [event['EventID']]

    # TODO: Based on the above data, generate a templated summary for the trace

    # join labels for each task to get summary for each task
    task_summaries = {}
    for task, events in task_events.items():
        # Sort the events based on timestamp
        # Then join the event labels for a summary of that task
        events_array = [eventInfo[event] for event in events]
        sorted_events = sorted(events_array, key=lambda k : k['HRT'])
        labels = [event['Label'] for event in sorted_events]
        task_summary = '\n'.join(labels)
        task_summaries[task] = task_summary

    # Not sure if we need this?
    #if(is_directed_acyclic_graph(eventGraph)):
    #   dfsResult = edge_dfs(eventGraph)
    #   print(list(dfsResult))

    return summary

@api.route("/summary/", methods=['GET'])
def summary():
    trace_id = request.args.get("query")
    # Get list of events for this trace
    events = get_events(trace_id)
    # Get list of tasks for this trace
    tasks = get_tasks(trace_id)
    summary = generate_trace_summary(events, tasks)
    return summary

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
