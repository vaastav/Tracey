from os import listdir
from os.path import isfile, join
import sys
import os
from networkx import DiGraph
from networkx.algorithms import is_directed_acyclic_graph
import networkx as nx

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

dir = sys.argv[1]

summary = get_aggregate_summary("../../preprocessed/scalability/" + dir)

with open("graphResults/" + str(dir) + "summary.txt", "w+") as summfile:
    summfile.write(summary)
