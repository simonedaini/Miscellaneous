# "/home/simone/Scrivania/traceroute.txt"


# importing the module
from hashlib import new
from os import path
import re
import networkx as nx
import matplotlib.pyplot as plt
from numpy import e
from pandas_ods_reader import read_ods
from termcolor import colored
import ast
import sys
import random

hid_counter = 1
b_counter = 1
a_counter = 1
nc_counter = 1
monitors = []



A = "1.1.1.1"
E = "2.2.2.2"
F = "3.3.3.3"
G = "4.4.4.4"
I = "5.5.5.5"
C = "6.6.6.6"



def read_trace(host1, host2):
    global monitors
    path = []

    pattern = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

    file_name = '/home/simone/Scrivania/monitors/{}-{}.txt'.format(host1, host2)
    f = open(file_name)
    lines = f.readlines()

    for i in range(0, len(lines)):
        ip = None
        if pattern.search(lines[i]) != None:
            ip = pattern.search(lines[i])[0]
        if i == 0:
            if ip != None:
                monitors.append(ip)
                router = {
                    "type": "R",
                    "ip": eval(host1)
                }
                path.append(router)
        else:
            if ip != None:
                router = {
                    "type": "R",
                    "ip": ip
                }
                path.append(router)
            else:
                router = {
                    "type": "A",
                    "ip": "A"
                }
                path.append(router)
    return path

def blocking_index(path):
    for i in range(len(path)):
        if path[i]["type"] == "B":
            return i
    return -1

def trace_to_path(path: list):

    start = None
    for i, p in enumerate(path):
        if p["type"] == "A" and start == None:
            start = i
        if start != None and p["type"] == "R":
            start = None

    if start != None:
        router = {
            "type": "B",
            "ip": "B"
        }
        path.insert(start, router)

    if start != None:
        for i in range(len(path)):
            if i > start:
                path.pop()
    return path  

def change_labels(path: list):

    global a_counter, hid_counter, b_counter, nc_counter

    nc = 0
    for p in path:
        if p["type"] == "B":
            nc += 1

    for p in path:
        if p["type"] == "A":
            p["ip"] = "A{}".format(a_counter)
            a_counter += 1
        elif p["type"] == "B" and nc != 2:
            p["ip"] = "B{}".format(b_counter)
            b_counter += 1
        elif p["type"] == "B" and nc == 2:
            p["type"] = "NC"
            p["ip"] = "NC{}".format(nc_counter)
            nc_counter += 1
        elif p["type"] == "HID":
            p["ip"] = "HID{}".format(hid_counter)
            hid_counter += 1

    return path

def create_path(host1, host2, distance):
    path = read_trace(host1, host2)
    path = trace_to_path(path)

    block = blocking_index(path)
    if block == -1:
        path = change_labels(path)
        return path
    else:
        inverse = read_trace(host2, host1)
        inverse = trace_to_path(inverse)

        for i in range(distance + 1 - len(path) - len(inverse)):
            router = {
                "type": "HID",
                "ip": "HID"
            }
            path.append(router)

        remaining = -(distance + 1 - len(path))
        inverse = inverse[::-1]
        path = path + inverse[remaining:]

        path = change_labels(path)
        return path

def print_paths(paths):
    print("PATHS:")
    for p in paths:
        print("\t{}".format(p))
    print("\n")



def create_graph(paths):
    g = nx.Graph()
    for path in paths:
        for i, p in enumerate(path):
            g.add_node(p["ip"])
            if i > 0:
                g.add_edge(path[i-1]["ip"], p["ip"])
    return g

def draw_graph(G):
    plt.clf()
    pos = nx.circular_layout(G)
    nx.draw(G, pos, with_labels = True)
    plt.show()

def save_graph(G, name):
    plt.clf()
    pos = nx.circular_layout(G)
    nx.draw(G, pos, with_labels = True)
    plt.savefig("/home/simone/Scrivania/monitors/results/{}".format(name))


# A = 1.1.1.1
# E = 2.2.2.2
# F = 3.3.3.3
# G = 4.4.4.4
# I = 5.5.5.5
# C = 6.6.6.6

paths = []
paths.append(create_path("A", "E", 4))
paths.append(create_path("A", "F", 3))
paths.append(create_path("A", "G", 2))
paths.append(create_path("A", "I", 2))
paths.append(create_path("E", "F", 3))
paths.append(create_path("E", "G", 4))
paths.append(create_path("G", "I", 2))

def trace_preservation(paths, link1, link2):
    found1 = False
    found2 = False
    for path in paths:
        for i in range(len(path) - 1):
            if path[i]["ip"] == link1[0]["ip"] and path[i+1]["ip"] == link1[1]["ip"]:
                found1 = True
                if found1 and found2:
                    return False
            if path[i]["ip"] == link2[0]["ip"] and path[i+1]["ip"] == link2[1]["ip"]:
                found2 = True
                if found1 and found2:
                    return False

        found1 = False
        found2 = False
    return True

def distance_preservation(paths: list, monitors, link1, link2):
    old_graph = create_graph(paths)
    new_paths = []
    for path in paths:
        new_paths.append(path.copy())
    
    merge_links(new_paths, link1, link2, True)
    new_graph = create_graph(new_paths)

    old_distances = dict(nx.all_pairs_shortest_path_length(old_graph))
    new_distances = dict(nx.all_pairs_shortest_path_length(new_graph))
    for node in monitors:
        for node2 in monitors:
            if node != node2:
                if node2 in new_distances:
                    if old_distances[node][node2] != new_distances[node][node2]:
                        return False
    return True


def merge_link(link1, link2, debug=False):
    global M
    if isinstance(link1, str):
        link1 = ast.literal_eval(link1)
    if isinstance(link2, str):
        link2 = ast.literal_eval(link2) 

    t = get_compatibility(M, link1, link2)
    type1 = get_edge_type(link1)
    type2 = get_edge_type(link2)
    selected = None

    if type1 == t or type1.split("-") == t.split("-")[::-1]:
        selected = link1
    elif type2 == t or type2.split("-") == t.split("-")[::-1]:
        selected = link2
    elif type1.split("-")[0] in t:
        selected = link1
    elif type2.split("-")[0] in t:
        selected = link2
    elif type1.split("-")[1] in t:
        selected = link1
    elif type2.split("-")[1] in t:
        selected = link2

    while True:
        if selected[0]["type"] == t.split("-")[0] and selected[1]["type"] == t.split("-")[1]:
            if not debug:
                print("\tUpdated edge = {}".format(selected))
            return selected
        elif selected[0]["type"] == t.split("-")[0] and selected[1]["type"] != t.split("-")[1]:
            selected[1]["type"] = t.split("-")[1]
            selected[1]["ip"] = eval("{}_counter".format(t.split("-")[1].lower()))
            eval("{}_counter += 1".format(t.split("-")[1].lower()))
            if not debug:
                print("\tUpdated edge = {}".format(selected))
            return selected
        elif selected[0]["type"] != t.split("-")[0] and selected[1]["type"] == t.split("-")[1]:
            selected[0]["type"] = t.split("-")[0]
            selected[0]["ip"] = eval("{}_counter".format(t.split("-")[1].lower()))
            eval("{}_counter += 1".format(t.split("-")[1].lower()))
            if not debug:
                print("\tUpdated edge = {}".format(selected))
            return selected
        else:
            t = t[::-1]

        


def merge_links(paths, link1, link2, debug=False):
    global M

    if isinstance(link1, str):
        link1 = ast.literal_eval(link1)
    if isinstance(link2, str):
        link2 = ast.literal_eval(link2) 

    t = get_compatibility(M, link1, link2)
    types = t.split("-")
    if t == "-":
        print("Cannot merge {} and {}, incompatible types".format(link1, link2))

    new_link = merge_link(link1, link2, debug)
    for path in paths:
        for i in range(len(path) - 1):
            if path[i] == link2[0] and path[i+1] == link2[1] or path[i] == link1[0] and path[i+1] == link1[1]:
                path[i] = new_link[0]
                path[i+1] = new_link[1]
    return paths


def get_matrix(file_name):
    df = read_ods(file_name)
    return df

def get_edge_type(link):
    t = ""

    if isinstance(link, str):
        link = ast.literal_eval(link)
    try:
        t = link[0]["type"] + "-" + link[1]["type"]
    except:
        print("Cannot read type of {}".format(link))
        print(type(link))
    
    return t

    
def reverse_type(t):
    s = t.split("-")
    n = s[1] + "-" + s[0]
    return n


def get_compatibility(M, link1, link2):
    if isinstance(link1, str):
        link1 = ast.literal_eval(link1)
    if isinstance(link2, str):
        link2 = ast.literal_eval(link2)

    row = []
    for i in range(1, len(M.columns)):
        row.append(M.axes[1][i])
    
    type1 = get_edge_type(link1)
    type2 = get_edge_type(link2)

    if "R" in type1 and "R" in type2:
        ip1 = None
        ip2 = None
        if link1[0]["type"] == "R":
            ip1 = link1[0]["ip"]
        else:
            ip1 = link1[1]["ip"]

        if link2[0]["type"] == "R":
            ip2 = link2[0]["ip"]
        else:
            ip2 = link2[1]["ip"]

        if ip1 == None or ip2 == None or ip1 != ip2:
            return "-"


    t = ""
    for i in range(8):
        try:
            t = M[type1][row.index(type2)]
        except:
            if i % 4 == 0:
                type1 = type1.split("-")[1] + "-" + type1.split("-")[0]
            if i % 4 == 1:
                type2 = type2.split("-")[1] + "-" + type2.split("-")[0]
            if i % 4 == 2:
                type1 = type1.split("-")[1] + "-" + type1.split("-")[0]
                type2 = type2.split("-")[1] + "-" + type2.split("-")[0]
            if i % 4 == 3:
                aux = type1
                type1 = type2
                type2 = aux
        
        if t != None and t != "" and t != "-":
            return t

    return "-"




# Trace Preservation: 2 links cannot appear in the same path
# Distance Preservation: Distance between 2 monitors is consistent after the merge
# Link Endpoint Compatibility: Check the table to see if two links have compatible type (care reversed and type R)

# 1) Identify all the valid merge options for each link, according to the 3 rules above
# 2) Select Ei with the fewest merging options and then Ej which has the fewest merging options out of the links with witch Ei can be merged
# 3) Check compatibility again because it might be changed by previous merges
# 4) Check each path containing one of the two links to make sure it will be coherent after the merge.
# 5) Merging Ej into Ei:
#       - All paths containing Ej are modified to contain Ei
#       - The set of link merging options for Ei are changed as the intersection between the ones of Ei and the ones of Ej
#       - Any link that could have been merged with both Ei and Ej retain their merge option with Ei and the merge option with Ej is removed
#       - Any link which had a merge option with either Ei or Ej but not both have that option removed
#       - Change the endpoint classes of Ei according to the table. The link with the most specialized endpoint determines the class of the resulting endpoint

def get_egress_edges(paths, node):
    edges = []
    for path in paths:
        for i in range(len(path) - 1):
            if path[i]["ip"] == node["ip"]:
                edges.append(path[i+1])
    return edges

def get_nodes(paths):
    nodes = []
    for path in paths:
        for i in range(len(path)):
            if path[i] not in nodes:
                nodes.append(path[i])
    return nodes


def create_merge_options(paths):
    global monitors, M
    merge_options = {}
    edges = []
    for path in paths:
        for i in range(len(path)-1):
            edges.append((path[i], path[i+1]))
    for link1 in edges:
        for link2 in edges:
            if link1 != link2:
                compatibility = get_compatibility(M, link1, link2)
                trace = trace_preservation(paths, link1, link2)
                distance = None
                if compatibility != "-" and trace:
                    distance = distance_preservation(paths, monitors, link1, link2)

                if compatibility != "-" and trace and distance:
                    if str(link1) not in merge_options:
                        merge_options[str(link1)] = []
                    if str(link2) not in merge_options:
                        merge_options[str(link2)] = []

                    if link2 not in merge_options[str(link1)]:
                        merge_options[str(link1)].append(link2)
                    if link1 not in merge_options[str(link2)]:
                        merge_options[str(link2)].append(link1)

    return merge_options

def get_min_key(merge_options: dict):
    
    min = get_min_options(merge_options)
    if min != 1000:
        for key in merge_options:
            if len(merge_options[key]) == min:
                return key
    else:
        print("Error in get_min_key")
        sys.exit()

def get_min_options(merge_options: dict):
    min = 1000
    for options in merge_options:
        if len(merge_options[options]) < min:
            min = len(merge_options[options])
    return min

def option_intersection(merge_options, link1, link2):

    if isinstance(link1, str):
        link1 = ast.literal_eval(link1)
    if isinstance(link2, str):
        link2 = ast.literal_eval(link2)

    op1 = None
    op2 = None

    if str(link1) in merge_options:
        op1 = merge_options[str(link1)]
    else:
        print("\nCurrent Merge options")
        print_merge_options(merge_options)
        sys.exit("Error in option_intersection: {} not in merge options".format(str(link1)))

    if str(link2) in merge_options:
        op2 = merge_options[str(link2)]
    else:
        print("\nCurrent Merge options")
        print_merge_options(merge_options)
        sys.exit("Error in option_intersection: {} not in merge options".format(str(link2)))

    new_op = []
    for op in op1:
        if op in op2 and op != (link1, link2):
            new_op.append(op)

    print("\tIntersection = {}".format(new_op))
    return new_op

def update_merge_options(merge_options, link1, link2):
    if isinstance(link1, str):
        link1 = ast.literal_eval(link1)
    if isinstance(link2, str):
        link2 = ast.literal_eval(link2)


    if merge_options == None:
        print("Inizio merge_option_list")
        sys.exit()

    new_options = {}
    new_link = merge_link(link1, link2, True)

    for key in merge_options:
        if str(key) != str(link1) and key != str(link2):
            if link1 in merge_options[key] and link2 in merge_options[key]:
                print("\tKey {} has both {} and {}".format(key, link1, link2))
                options = merge_options[key].copy()
                options.remove(link2)
                options.remove(link1)
                options.append(new_link)
                if options != []:
                    print("\t\tRemoving {}".format(link2))
                    print("\t\tSobstituting {} -> {}".format(link1, new_link))
                    new_options[key] = options
                    print("\t\tFinal Options = {}\n".format(new_options[key]))
                else:
                    print("\t\tPOP key {}, empty options\n".format(key))
            else:
                print("\tKey {} does NOT have both {} and {}".format(key, link1, link2))
                if link1 in merge_options[key]:
                    options = merge_options[key].copy()
                    options.remove(link1)
                    if options != []:
                        print("\t\tRemoving {}".format(link1))
                        new_options[key] = options
                        print("\t\tFinal Options = {}\n".format(new_options[key]))
                    else:
                        print("\t\tPOP key {}, empty options\n".format(key))
                if link2 in merge_options[key]:
                    options = merge_options[key].copy()
                    options.remove(link2)
                    if options != []:
                        new_options[key] = options
                        print("\t\tRemoving {} -> {}".format(key, link2))
                        print("\t\tFinal Options = {}\n".format(new_options[key]))
                    else:
                        print("\t\tPOP key {}, empty options\n".format(key))
                else:
                    print("\tKey {} has NOT either {} or {}".format(key, link1, link2))
                    options = merge_options[key].copy()
                    if options != []:
                        new_options[key] = options



    intersection = option_intersection(merge_options, link1, link2)
    if intersection != []:
        new_options[str(link1)] = intersection

    if new_options == None:
        print("Fine merge_option_list")

    return new_options



def print_merge_options(merge_options):
    print("MERGE OPTIONS:")
    if merge_options == None:
        print("MERGE OPTIONS None")
        return
    for node in merge_options:
        print("\t{} --> {}".format(node, merge_options[node]))
    print("\n")



def check_consistency(paths):
    global nc_counter

    update = []

    for path in paths:
        for i in range(len(path) - 1):
            if path[i]["type"] == "B" and path[i+1]["type"] == "HID":
                print("Found inconsistency between {} and {}".format(path[i], path[i+1]))
                update = path[i]["ip"]

    new_paths = []
    for path in paths:
        p = []
        for i in range(len(path)):
            if path[i]["ip"] in update:
                r = {
                    "type": "NC",
                    "ip": "NC{}".format(nc_counter)
                }
                nc_counter += 1
                p.append(r)
            else:
                p.append(path[i])
        new_paths.append(p)
    return new_paths

M = get_matrix("/home/simone/Scrivania/Matrice.ods")
merge_options = create_merge_options(paths)
print_merge_options(merge_options)

G = create_graph(paths)
draw_graph(G)
save_graph(G, "VT")

i = 1
sync = i
while True and sync == i:
    merge_options = create_merge_options(paths)
    sync += 1
    while merge_options:
        print("Iteration {}".format(i))
        i += 1

        link1 = get_min_key(merge_options)
        link2 = merge_options[link1][0]
        print("\tMerging {} with {}".format(link1, link2))
        print("\tCompatibility = {}".format(get_compatibility(M, link1,  link2)))    
        paths = merge_links(paths, link1, link2)
        merge_options = update_merge_options(merge_options, link1, link2)
        print_merge_options(merge_options)
    paths = check_consistency(paths)

G = create_graph(paths)
draw_graph(G)
save_graph(G, "MT")
