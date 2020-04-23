from flask import Flask, request, jsonify
import json
import sys
import scipy.stats as stats
from networkx import DiGraph
from networkx.algorithms import is_directed_acyclic_graph
from networkx.algorithms.traversal.edgedfs import edge_dfs
#from networkx.algorithms.dag.topological_sort import topological_sort
import networkx as nx
from mysql.connector import Error, connect
import os
import urllib.request
import diff_match_patch as dmp_module
import random
import numpy as np
from timeit import default_timer as timer

api = Flask(__name__)
connection = {}

EVENT_PROB_THRESHOLD=0.25
TASK_PERCENTILE_THRESHOLD_LOW=5.0
TASK_PERCENTILE_THRESHOLD_HIGH=95.0
MISSING_TASK_PEN=5
LABEL_BLACKLIST = ["ThreadLocalBaggage::Branch", "ThreadLocalBaggage::Set", "ThreadLocalBaggage::Swap", "ThreadLocalBaggage::Join", "ThreadLocalBaggage::Delete"]

class SummaryPerf:
    def __init__(self,data_load_time,summary_generation_time):
        self.load_time = data_load_time
        self.gen_time = summary_generation_time
        self.total_time = data_load_time + summary_generation_time

    def __str__(self):
        return str(self.load_time) + "," + str(self.gen_time) + "," + str(self.total_time)

def get_overview(trace_id):
    global connection
    cursor = connection.cursor()
    query = ("SELECT overview.duration, overview.doc, tags.tag FROM overview, tags WHERE overview.trace_id=%s AND tags.trace_id=%s")
    cursor.execute(query, (trace_id, trace_id))
    overview = {}
    tags = []
    trace_dur = 0
    trace_doc = ""
    for (duration, doc, tag) in cursor:
        tags += [tag]
        trace_dur = duration
        trace_doc = doc
    overview["tags"] = tags
    overview["duration"] = trace_dur
    overview["timestamp"] = trace_doc
    cursor.close()
    return overview

def get_all_traces():
    global connection
    cursor = connection.cursor()
    query = "SELECT DISTINCT trace_id FROM overview"
    cursor.execute(query)
    traces = []
    for (trace_id) in cursor:
        traces += [trace_id[0]]
    cursor.close()
    return traces

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

def generate_trace_summary(events, tasks, overview):
    summary = "Done boss!"

    # Content Planner
    percentile_scores = {}
    concurrent_tasks = {}
    task_name = {}
    task_events = {}
    num_tasks_percentile_high = 0
    num_tasks_percentile_low = 0
    max_task_contention = 0
    max_task_contention_id = ""
    for task in tasks:
        task_id = task['ProcessName'] + str(task['ProcessID']) + str(task['ThreadID'])
        task_name[task_id] = task['Operation']
        # For each task calculate it's percentile score w.r.t to the distribution
        percentile = stats.percentileofscore(task['Data'], task['Duration'])
        percentile_scores[task_id] = percentile
        if percentile > TASK_PERCENTILE_THRESHOLD_HIGH:
            num_tasks_percentile_high += 1
        if percentile < TASK_PERCENTILE_THRESHOLD_LOW:
            num_tasks_percentile_low += 1
        # For each task figure out how many other consequent tasks are being run
        # Approximate this by figuring out how many concurrent tasks there were during
        # the full duration of the task. 
        num_tasks = 0
        if task['MolehillData'] is not None:
            num_tasks = len(task['MolehillData'])
        if num_tasks > max_task_contention:
            max_task_contention = num_tasks
            max_task_contention_id = task_id
        concurrent_tasks[task_id] = num_tasks
        # Initialize the events array for each task
        task_events[task_id] = []

    eventInfo = {}
    eventGraph = DiGraph()
    anomalous_events_set = set()
    # Process events, find anomalous events, and group events by task 
    for event in events:
        eventInfo[event["EventID"]] = event
        eventGraph.add_node(event["EventID"])
        if(event["ParentEventID"] != None):
            for parentID in event["ParentEventID"]:
                eventGraph.add_edge(parentID, event["EventID"])
        # Get all the anomalous events
        if event["Probability"] < EVENT_PROB_THRESHOLD:
            anomalous_events_set.add(event['EventID'])
        # Put the events in each task
        task_id = event['ProcessName'] + str(event['ProcessID']) + str(event['ThreadID'])
        task_events[task_id] += [event['EventID']]

    # Sentence Planner
    # Based on the above data, generate a templated summary for the trace
    template_summary = ""
    # Overview of the trace
    template_summary += "The trace was created on " + str(overview["timestamp"].strftime("%d %b, %Y")) + " and it took around " + str(int(overview["duration"]/1e6)) + " seconds to complete."
    template_summary += "The trace was associated with the following tags: " + ''.join(overview["tags"]) + ". "
    # Number of anomalous events. 
    template_summary += "The trace had " + str(len(events)) + " events, out of which " + str(len(anomalous_events_set)) + " events had less than " + str(EVENT_PROB_THRESHOLD * 100) + "% chance of occurring."
    # Tasks Overview
    template_summary += " The execution of the request was performed by " + str(len(task_name)) + " tasks." 
    if num_tasks_percentile_high > 0:
        template_summary += " " + str(num_tasks_percentile_high) + " tasks had latency that ranked higher than the " + str(int(TASK_PERCENTILE_THRESHOLD_HIGH)) + "th percentile of the latency distribution for the respective task."
    if num_tasks_percentile_low < 0:
        template_summary += " " + str(num_tasks_percentile_low) + " tasks had latency that ranked lower than the " + str(int(TASK_PERCENTILE_THRESHOLD_LOW)) + "th percentile of the latency distribution for the respective task."
    # Contention Overview
    if max_task_contention > 0:
        template_summary += " Task performing the operation " + task_name[max_task_contention_id] + " had the maximum amount of contention with " + str(max_task_contention) + " other tasks performing the same operation at the same time for different requests." 

    # join labels for each task to get summary for each task
    # Surface Realization
    task_summaries = {}
    task_start_times = {}
    for task, events in task_events.items():
        # Sort the events based on timestamp
        # Then join the event labels for a summary of that task
        events_array = [eventInfo[event] for event in events]
        sorted_events = sorted(events_array, key=lambda k : k['HRT'])
        task_summary = ''
        
        # Grab the first event in the task and check its parent to find the task that created 
        # the current one, if it has one. If so add to the summary.
        if(sorted_events[0]["ParentEventID"] is not None):
            # Some of the erroneous traces have events missing! Need to handle that scenario.
            parent_event_id = sorted_events[0]["ParentEventID"][0]
            if parent_event_id in eventInfo:
                parent_event = eventInfo[parent_event_id]
                parent_task_id = parent_event['ProcessName'] + str(parent_event['ProcessID']) + str(parent_event['ThreadID'])
                task_summary += "Task " + task_name[parent_task_id] + " created task " + task_name[task] + ". "
            

        # Only include events that are user-annotated and not anything from the library.
        labels = [event['Label'] if event['Label'] not in LABEL_BLACKLIST else '' for event in sorted_events]
        
        # Append non empty labels to the summary. 
        for l in labels:
            if l != '':
                task_summary += l + ". "
        task_summaries[task] = task_summary
        task_start_times[task] = sorted_events[0]['HRT']

    # Join the individual summaries of each task to get
    # the execution summary of the trace
    execution_summary = ""
    for task, summary in sorted(task_summaries.items(), key=lambda k : task_start_times[k[0]]):
        execution_summary += summary + "\n" 


    return {"template" : template_summary, "execution" :  execution_summary}

@api.route("/summary/<string:trace_id>", methods=['GET'])
def summary(trace_id):
    print("Generating summary for", trace_id)
    overview = get_overview(trace_id)
    # Get list of events for this trace
    events = get_events(trace_id)
    # Get list of tasks for this trace
    tasks = get_tasks(trace_id)
    summary = generate_trace_summary(events, tasks, overview)
    return jsonify(summary)

@api.route("/allsummaries/", methods=['GET'])
def all_summaries():
    print("Getting all traces")
    traces = get_all_traces()
    perf_list = []
    for trace in traces:
        #if os.path.exists(os.path.join("./summary", trace + ".txt")):
        #    continue
        print("Generating summary for trace: ", trace)
        load_start = timer()
        overview = get_overview(trace)
        events = get_events(trace)
        tasks = get_tasks(trace)
        load_end = timer() - load_start
        gen_start = timer()
        summary = generate_trace_summary(events, tasks, overview)
        gen_end = timer() - gen_start
        perf = SummaryPerf(load_end, gen_end)
        perf_list += [perf]
        with open(os.path.join("./summary", trace + ".txt"), 'w+') as outf:
            outf.write(summary['template'] + "\n")
            outf.write(summary['execution'] + "\n")
    with open('summary_time.csv', 'w+') as outf:
        outf.write("Load_Time,Gen_Time,Total_Time\n")
        for perf in perf_list:
            outf.write(str(perf) + "\n")
    return "Done boss\n"

@api.route("/dataset_info/", methods=['GET'])
def dataset_info():
    global connection
    cursor = connection.cursor()
    query = "SELECT COUNT(*) FROM events GROUP BY trace_id"
    cursor.execute(query)
    num_events = []
    for (event_count) in cursor:
        num_events += [event_count[0]]
    cursor.close()
    cursor = connection.cursor()
    query = "SELECT COUNT(*) FROM tasks GROUP BY trace_id"
    cursor.execute(query)
    num_tasks = []
    for (task_count) in cursor:
        num_tasks += [task_count[0]]
    cursor.close()
    with open('num_events.csv', 'w+') as outf:
        outf.write("Num_Events\n")
        for e in num_events:
            outf.write(str(e) + "\n")
    with open('num_tasks.csv', 'w+') as outf:
        outf.write("Num_Tasks\n")
        for t in num_tasks:
            outf.write(str(t) + "\n")
    return "Done boss\n"

def compute_distance(task_diffs, unmatched_tasks):
    dmp = dmp_module.diff_match_patch()
    distance = 0.0
    for d in task_diffs:
        distance += dmp.diff_levenshtein(d)
    for u in unmatched_tasks:
        distance += MISSING_TASK_PEN * len(u.split('.'))
    return distance

def get_trace_diff(trace1, trace2):
    diff = ""
    trace1_summary = open(os.path.join("./summary", trace1 + ".txt"), 'r+').readlines()
    trace2_summary = open(os.path.join("./summary", trace2 + ".txt"), 'r+').readlines()
    dmp = dmp_module.diff_match_patch()
    html = ""
    matched_lines_t2 = set()
    unmatched_lines_t1 = set()
    # We want to compare summaries at the granularity of task
    task_execution_diffs = []
    for i in range(len(trace1_summary)):
        line1 = trace1_summary[i]
        match_found = False
        for j in range(len(trace2_summary)):
            if match_found:
                break
            line2 = trace2_summary[j]
            # The first line in the summary are the templated overview so they are comparable
            if i == 0 and j == 0:
                diff = dmp.diff_main(line1, line2)
                dmp.diff_cleanupSemantic(diff)
                html += dmp.diff_prettyHtml(diff) + "\n"
                matched_lines_t2.add(j)
                match_found = True
            if j in matched_lines_t2:
                continue
            l1_tokens = line1.split('.')
            l2_tokens = line2.split('.')
            # Two lines are of the same task if their 1st sentences match
            if l1_tokens[0] == l2_tokens[0]:
                match_found =  True
                diff = dmp.diff_main(line1, line2)
                dmp.diff_cleanupSemantic(diff)
                html += dmp.diff_prettyHtml(diff) + "\n"
                matched_lines_t2.add(j)
                task_execution_diffs += [diff]
        if not match_found:
            unmatched_lines_t1.add(i)
    all_unmatched_lines = []
    for i in range(len(trace1_summary)):
        if i in unmatched_lines_t1:
            diff = dmp.diff_main(trace1_summary[i], "")
            dmp.diff_cleanupSemantic(diff)
            html += dmp.diff_prettyHtml(diff) + "\n"
            all_unmatched_lines += [trace1_summary[i]]
    for j in range(len(trace2_summary)):
        if j not in matched_lines_t2:
            diff = dmp.diff_main("", trace2_summary[j])
            dmp.diff_cleanupSemantic(diff)
            html += dmp.diff_prettyHtml(diff) + "\n"
            all_unmatched_lines += [trace2_summary[j]]
    # Calculate distance using all_unmatched_lines and task_execution_diffs 
    distance = compute_distance(task_execution_diffs, all_unmatched_lines)
    return distance, html

@api.route("/compare/<string:trace1>/<string:trace2>", methods=['GET'])
def compare(trace1, trace2):
    start = timer()
    dist, html = get_trace_diff(trace1, trace2)
    end = timer() - start
    print("Distance is ",dist)
    print("Time taken is ", end, " seconds")
    return html

@api.route("/comparison_test/", methods=['GET'])
def comparison_test():
    traces = get_all_traces()
    perf_list = []
    for trace in traces:
        if len(perf_list) > 100:
            break
        # Select a random trace to compare against from the trace list
        choice = random.choice(traces)
        start = timer()
        dist, html = get_trace_diff(trace, choice)
        end = timer() - start
        perf_list += [end]
    return "Average time taken for 100 random trace comparisons was " + str(np.mean(perf_list) * 1000) + " milliseconds\n"


def load_tasks_for_traces(rootdir):
    # For each task build the graph from the traces
    tasks = {}
    for subdir, dirs, files in os.walk(rootdir):
        # Each subdirectory in the root directory corresponds to a task.
        # Each file in the subdirectory is the instance of a task
        if subdir == rootdir:
            continue
        if subdir not in tasks:
            # Initialize the Sentence Graph for each trace
            tasks[subdir] = DiGraph()
        graph = tasks[subdir]
        for file in files:
            with open(os.path.join(subdir, file), 'r+') as inf:
                lines = inf.readlines()
                sentences = lines[0].strip().split('.')
                duplicates_counter = {}
                prev_sentence = ''
                prefix = ''
                for s in sentences:
                    # Add each sentence as a separate node. Connect the edges between the nodes.
                    # Need to make sure that sentences with same labels but different positions are different nodes!
                    # Use the prefix to do that
                    current_label = s + '#' + prefix
                    # Update prefix for next iteration
                    prefix += s + '.'
                    #if s in duplicates_counter:
                    #    # This is a label we hae seen in this paragraph before
                    #    current_label = s + '#' + str(duplicates_counter[s])
                    #    duplicates_counter[s] += 1
                    #else:
                    #    duplicates_counter[s] = 1
                    if not graph.has_node(current_label):
                        graph.add_node(current_label)
                    if prev_sentence != '':
                        # Check if edge (prev_sentence, current_label) exists.
                        # Add the edge to graph if it doesn't.
                        # If it does then increase the edge count.
                        if graph.has_edge(prev_sentence, current_label):
                            graph[prev_sentence][current_label]['count'] += 1
                        else:
                            graph.add_edge(prev_sentence, current_label)
                            graph[prev_sentence][current_label]['count'] = 1
                    prev_sentence = current_label
        tasks[subdir] = graph

    return tasks

def convert_graphs_to_text(graphs):
    # For each graph convert it into a paragraph
    paragraphs = {}
    for key, graph in graphs.items():
        # Implement graph to text
        summary = ""
        if not is_directed_acyclic_graph(graph):
            print("Graph is not a DAG for ", key)
            #print(graph.edges)
            #for e in graph.edges:
            #    print(e)
            #print(len(list(nx.simple_cycles(graph))), " cycles for ", key)
            max_len = 10000000
            smallest_cycle = []
            for c in nx.simple_cycles(graph):
                if len(c) < max_len:
                    max_len = len(c)
                    smallest_cycle = c
            for v in smallest_cycle:
                print(v)    
            #continue
        topo_sorted_vertices = nx.topological_sort(graph)
        i = 0
        for vertex in topo_sorted_vertices:
            i += 1
            tokens = vertex.split('#')
            summary += tokens[0]
            if i != graph.number_of_nodes():
                # Prevent an extra '.' from appearing at the end
                summary += '.'
        paragraphs[key] = summary

    return paragraphs

def get_aggregate_summary(root_dir):
    # Build the sentence graph for each task
    graphs = load_tasks_for_traces(root_dir)
    # Convert each graph into a paragraph for that task
    paragraphs = convert_graphs_to_text(graphs)
    summary = ""
    for p, val in paragraphs.items():
        summary += val + '\n'
    return summary

@api.route("/summarize_aggregate/", methods=['GET'])
def summarize_aggregate():
    result = ''
    dirs = ['5', '10', '25', '100', '1000', '10000', '22290']
    for dir in dirs:
        start = timer()
        summary = get_aggregate_summary("./summary/preprocessed/scalability/" + dir)
        end = timer() - start
        result_str = "Aggregation " + dir + " traces took " + str(end) + " seconds."
        print(result_str)
        result += result_str + '\n'

    return result

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
