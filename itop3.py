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


from heapq import merge
import os
import re
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms.threshold import shortest_path_length
from networkx.classes.graph import Graph
from pandas_ods_reader import read_ods
from termcolor import colored
import sys




# ******************************************************************************************************************#
#                                                                                                                   #
#                                               Virtual topology methods                                            #
#                                                                                                                   #
# ******************************************************************************************************************#



def read_trace(folder_path, network_public_ip, host1, host2):
    global monitors
    path = []

    pattern = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
    file_name = "{}traceroutes/{}/{}-{}".format(folder_path, network_public_ip, host1, host2)
    # file_name = '/home/simone/Scrivania/monitors/{}-{}.txt'.format(host1, host2)
    try:
        f = open(file_name)
    except:
        print("File {} not found".format(file_name))
    lines = f.readlines()

    for i in range(0, len(lines)):
        ip = None
        if pattern.search(lines[i]) != None:
            ip = pattern.search(lines[i])[0]
        if i == 0:
            if ip != None:
                if ip not in monitors:
                    monitors.append(ip)
                router = {
                    "type": "R",
                    "ip": host1
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

def create_path(folder_path, network_public_ip, host1, host2, distance):
    path = read_trace(folder_path, network_public_ip, host1, host2)
    path = trace_to_path(path)

    block = blocking_index(path)
    if block == -1:
        path = change_labels(path)
        return path
    else:
        inverse = read_trace(folder_path, network_public_ip, host2, host1)
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

def save_graph(folder_path, network_public_ip, G, name):
    plt.clf()
    pos = nx.circular_layout(G)
    nx.draw(G, pos, with_labels = True)

    file_name = folder_path + "results/" + network_public_ip + "/" + name
    try:
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
    except Exception as e:
        print(e)

    plt.savefig(file_name)





# ******************************************************************************************************************#
#                                                                                                                   #
#                                               Merge topology methods                                              #
#                                                                                                                   #
# ******************************************************************************************************************#



def get_matrix(file_name):
    df = read_ods(file_name)
    return df

def get_edge_type(e):
    t = ""
    t1 = ""
    t2 = ""
    if "." in e[0]:
        t1 = "R"
    elif "A" in e[0]:
        t1 = "A"
    elif "B" in e[0]:
        t1 = "B"
    elif "NC" in e[0]:
        t1 = "NC"
    elif "HID" in e[0]:
        t1 = "HID"

    if "." in e[1]:
        t2 = "R"
    elif "A" in e[1]:
        t2 = "A"
    elif "B" in e[1]:
        t2 = "B"
    elif "NC" in e[1]:
        t2 = "NC"
    elif "HID" in e[1]:
        t2 = "HID"

    t = "{}-{}".format(t1, t2)
    return t


def get_compatibility(link1, link2):

    association = {}

    association[link1[0]] = []
    association[link1[1]] = []
    association[link2[0]] = []
    association[link2[1]] = []

    assess_types(association, link1, link2)
    assess_types(association, link1, reverse(link2))
    assess_types(association, reverse(link1), link2)
    assess_types(association, reverse(link1), reverse(link2))

    if len(association[link1[0]]) == 0:
        return None
    return association


def assess_types(association, link1, link2):
    HID = 0
    NC = 1
    R = 1
    A = 2
    B = 2

    t1 = node_type(link1[0])
    t2 = node_type(link1[1])
    t3 = node_type(link2[0])
    t4 = node_type(link2[1])

    v1 = eval(t1)
    v2 = eval(t2)
    v3 = eval(t3)
    v4 = eval(t4)


    # Se il primo link è R-R può essere unito solo con HID HID
    if t1 == "R" and t2 == "R" and (t3 != "HID" or t4 != "HID"):
        return association
    
    # Se hanno lo stesso valore devono avere lo stesso tipo
    if v1 == v3 and t1 != t3 or v2 == v4 and t2 != t4:
        return association

    # Se hanno lo stesso valore e lo stesso tipo ma sono R, devono avere anche lo stesso IP
    if t1 == "R" and t3 == "R" and link1[0] != link2[0] or t2 == "R" and t4 == "R" and link1[1] != link2[1] or t1 == "R" and t4 == "R" and link1[0] != link2[0] or t2 == "R" and t3 == "R" and link1[1] != link2[1]:
        return association

    if v1 >= v3 and v2 >= v4:
        if link1[0] not in association[link1[0]]:
            association[link1[0]].append(link1[0])
        if link1[1] not in association[link1[1]]:
            association[link1[1]].append(link1[1])
        if link1[0] not in association[link2[0]]:
            association[link2[0]].append(link1[0])
        if link1[1] not in association[link2[1]]:
            association[link2[1]].append(link1[1])

    elif v1 >= v3 and v2 <= v4:
        if link1[0] not in association[link1[0]]:
            association[link1[0]].append(link1[0])
        if link2[1] not in association[link1[1]]:
            association[link1[1]].append(link2[1])
        if link1[0] not in association[link2[0]]:
            association[link2[0]].append(link1[0])
        if link2[1] not in association[link2[1]]:
            association[link2[1]].append(link2[1])

    elif v1 <= v3 and v2 >= v4:
        if link2[0] not in association[link1[0]]:
            association[link1[0]].append(link2[0])
        if link1[1] not in association[link1[1]]:
            association[link1[1]].append(link1[1])
        if link2[0] not in association[link2[0]]:
            association[link2[0]].append(link2[0])
        if link1[1] not in association[link2[1]]:
            association[link2[1]].append(link1[1])

    elif v1 <= v3 and v2 <= v4:
        if link2[0] not in association[link1[0]]:
            association[link1[0]].append(link2[0])
        if link2[1] not in association[link1[1]]:
            association[link1[1]].append(link2[1])
        if link2[0] not in association[link2[0]]:
            association[link2[0]].append(link2[0])
        if link2[1] not in association[link2[1]]:
            association[link2[1]].append(link2[1])

    return association




def trace_preservation(G: Graph, link1, link2):
    for m1 in monitors:
        for m2 in monitors:
            if m1 != m2:
                m1m2 = nx.shortest_path(G, m1, m2)
                if link1[0] in m1m2 and link1[1]  in m1m2 and link2[0]in m1m2 and link2[1]in m1m2:
                    return False
    return True


def distance_preservation(distances, new_G):
    for m1 in monitors:
        for m2 in monitors:
            if m1 != m2:
                key = "{}-{}".format(m1, m2)
                if key in distances:
                    if nx.shortest_path_length(new_G, m1, m2) != distances[key]:
                        return False
    return True


def node_type(node):
    if "." in node:
        return "R"
    elif "NC" in node:
        return "NC"
    elif "A" in node:
        return "A"
    elif "B" in node:
        return "B"
    elif "HID" in node:
        return "HID"
    else:
        sys.exit("Error node type in {}".format(node))



def merged_link(link1, link2):
    global a_counter, b_counter, nc_counter, hid_counter
    association = get_compatibility(link1, link2)
    r1 = None
    r2 = None
    alternatives = []


    if association == None:
        print("Association = None")
    else:
        for i in range(len(association[link1[0]])):
            r1 = association[link1[0]][i]
            r2 = association[link1[1]][i]
            alternatives.append((r1,r2))

    return alternatives


def path_coherence(old_path, new_path):
    HID = 0
    NC = 1
    R = 1
    A = 2
    B = 2

    if len(old_path) != len(new_path):
        return False

    for i in range(len(old_path)):

        old_type = node_type(old_path[i])
        new_type = node_type(new_path[i])

        # If they are R they have to be the same router with the same IP
        if "." in old_path[i] and "." in new_path[i] and old_path[i] != new_path[i]:
            return False
        # If there was a responding router, it has to be
        elif "." in old_path[i] and "." not in new_path[i] != "R":
            return False

        elif eval(old_type) > eval(new_type):
            return False
        elif eval(old_type) == eval(new_type) and old_type != new_type:
            return False

    for i in range(len(old_path) - 1):
        if node_type(old_path[i]) == "NC" and node_type(old_path[i+1]) == "HID":
            if node_type(new_path[i]) != "NC" and node_type(new_path[i+1]) == "HID":
                return False

    return True



def merge_links_in_graph(G: Graph, link1, link2, new_link):

    G1 = substitute_edge(G, link1, link2, new_link)
    check = False

    for m1 in monitors:
        for m2 in monitors:
            if m1 != m2:
                old_m1m2 = nx.shortest_path(G, m1, m2)
                m1m2 = nx.all_shortest_paths(G1, m1, m2)
                for path in m1m2:
                    if path_coherence(old_m1m2, path):
                        check = True

    if check == True:
        return G1
    else:
        check = False
        reverse = (new_link[1], new_link[0])
        G2 = substitute_edge(G, link1, link2, reverse)
        for m1 in monitors:
            for m2 in monitors:
                if m1 != m2:
                    old_m1m2 = nx.shortest_path(G, m1, m2)
                    m1m2 = nx.all_shortest_paths(G1, m1, m2)
                    for path in m1m2:
                        if path_coherence(old_m1m2, path):
                            check = True

        if check:
            return G2
        else:
            return None


def substitute_edge(G, link1, link2, new_link):
    copy = G.copy()
    
    adj1 = copy.adj[link1[0]]
    adj2 = copy.adj[link1[1]]
    adj3 = copy.adj[link2[0]]
    adj4 = copy.adj[link2[1]]

    if link1[0] in copy.nodes:
        copy.remove_node(link1[0])
    if link1[1] in copy.nodes:
        copy.remove_node(link1[1])
    if link2[0] in copy.nodes:
        copy.remove_node(link2[0])
    if link2[1] in copy.nodes:
        copy.remove_node(link2[1])

    copy.add_node(new_link[0])
    copy.add_node(new_link[1])
    copy.add_edge(new_link[0], new_link[1])

    for e in adj1:
        if e != link1[0] and e != link1[1] and e != link2[0] and e != link2[1]:
            copy.add_edge(new_link[0], e)
    for e in adj3:
        if e != link1[0] and e != link1[1] and e != link2[0] and e != link2[1]:
            copy.add_edge(new_link[0], e)
    for e in adj2:
        if e != link1[0] and e != link1[1] and e != link2[0] and e != link2[1]:
            copy.add_edge(new_link[1], e)
    for e in adj4:
        if e != link1[0] and e != link1[1] and e != link2[0] and e != link2[1]:
            copy.add_edge(new_link[1], e)

    return copy

def reverse(edge):
    return (edge[1], edge[0])


def create_merge_options(distances, G: Graph):
    options = {}

    for e1 in G.edges:
        for e2 in G.edges:
            if e1 != e2 and reverse(e1) != e2:
                if get_compatibility(e1, e2) != None:
                    if trace_preservation(G, e1, e2):
                        alternatives = merged_link(e1, e2)
                        for merged in alternatives:
                            G2 = merge_links_in_graph(G, e1, e2, merged)
                            if G2 != None and distance_preservation(distances, G2):
                                if e1 not in options:
                                    options[e1] = []
                                if e2 not in options[e1]:
                                    options[e1].append(e2)
                                if e2 not in options:
                                    options[e2] = []
                                if e1 not in options[e2]:
                                    options[e2].append(e1)
    return options

def option_intersection(options, e1, e2):
    l = []
    for e in options[e1]:
        if e in options[e2] and e != e1 and e != e2:
            l.append(e)

    return l

def remove_option(option_list, e):
    if e in option_list:
        option_list.remove(e)
    elif reverse(e) in option_list:
        option_list.remove(e)

    return option_list

def update_merge_options(options, e1, e2, merged, association):
    copy = {}
    intersection = option_intersection(options, e1, e2)

    for k in options:
        l = []
        if k != e1 and k != e2 and k != reverse(e1) and k != reverse(e2):
            for op in options[k]:
                l.append(op)
            count = 0
            if e1 in l or reverse(e1) in l:
                l = remove_option(l, e1)
                count += 1
            if e2 in l or reverse(e2) in l:
                l = remove_option(l, e2)
                count += 1

            if count == 2:
                l.append(merged)

            for i in range(len(l)):
                new_e = []
                if l[i][0] in association or l[i][1] in association:
                    if l[i][0] in association:
                        new_e.append(association[l[i][0]][0])
                    else:
                        new_e.append(l[i][0])
                    if l[i][1] in association:
                        new_e.append(association[l[i][1]][0])
                    else:
                        new_e.append(l[i][1])
                    l[i] = tuple(new_e)

            if l != []:
                new_k = []
                if k[0] in association:
                    new_k.append(association[k[0]][0])
                else:
                    new_k.append(k[0])
                if k[1] in association:
                    new_k.append(association[k[1]][0])
                else:
                    new_k.append(k[1])
                copy[tuple(new_k)] = l

            
    if intersection != []:
        copy[merged] = intersection       

    return copy

def remove_failed_option(options, e1, e2):
    options[e1].remove(e2)
    options[e2].remove(e1)
    if options[e1] == []:
        options.pop(e1)
    if options[e2] == []:
        options.pop(e2)
    return options



def get_edge_with_min_options(options):
    min = 100000
    key = None
    for k in options:
        if len(options[k]) < min:
            min = len(options[k])
            key = k

    if min != 100000:
        return key
    else:
        sys.exit("Error get_edge_with_min_options")

def get_option_with_min_options(options, e):
    min = 100000
    key = None
    for k in options[e]:
        if len(options[k]) < min:
            min = len(options[k])
            key = k
    if min != 100000:
        return key
    else:
        sys.exit("Error get_option_with_min_options")

def print_options(options):
    print("Options = ")
    for opt in options:
        print("\t{} = {}".format(opt, options[opt]))




hid_counter = 1
b_counter = 1
a_counter = 1
nc_counter = 1

monitors = []
distances = {}


def get_distances(folder_path, network_public_ip):
    global distances
    distance_path = folder_path + "/distances/" + network_public_ip + "/"
    for file in os.listdir(distance_path):
        f = open(distance_path + file, "r")
        lines = f.readlines()
        for line in lines:
            distances["{}-{}".format(file, line.split(" ")[0])] = int(line.split(" ")[1])
    return distances

def create_virtual_topology(folder_path, network_public_ip):

    global distances
    distances = get_distances(folder_path, network_public_ip)

    paths = []
    done = []
    traceroutes_path = folder_path + "/traceroutes/" + network_public_ip + "/"
    for file in os.listdir(traceroutes_path):
        if ".txt" in file:
            file = file.replace(".txt", "")
        host1 = file.split("-")[0]
        host2 = file.split("-")[1]
        if "{}-{}".format(host1, host2) not in done and "{}-{}".format(host2, host1) not in done:
            distance = distances["{}-{}".format(host1, host2)]
            paths.append(create_path(folder_path, network_public_ip, host1, host2, distance))
            done.append("{}-{}".format(host1, host2))

    return paths



def iTop(compatibility_matrix_path, folder_path, network_public_ip):
    paths = create_virtual_topology(folder_path, network_public_ip)
    print("[+] Virtual Topology saved in {}".format(folder_path + "results/"))
    M = get_matrix(compatibility_matrix_path)

    G = create_graph(paths)
    # draw_graph(G)
    save_graph(folder_path, network_public_ip, G, "1) VT")



    i = 1
    sync = i
    while True and sync == i:
        options = create_merge_options(distances, G)
        # print_options(options)
        sync += 1
        while options != {}:
            i += 1
            sync = i

            e1 = get_edge_with_min_options(options)
            e2 = get_option_with_min_options(options, e1)
            merge_alternatives = merged_link(e1, e2)
            merged = None
            if len(merge_alternatives) == 1:
                merged = merge_alternatives[0]
                association = get_compatibility(e1, e2)
                # print("\tMerging {} with {} in {}".format(e1, e2, merged))
                G2 = merge_links_in_graph(G, e1, e2, merged)
                if G2 != None:
                    G = G2
                    options = update_merge_options(options, e1, e2, merged, association)
                else:
                    options = remove_failed_option(options, e1, e2)


    # draw_graph(G)
    save_graph(folder_path, network_public_ip, G, "2) MT")
    print("[+] Merged Topology saved in {}".format(folder_path + "results/"))

# compatibility_matrix_path = "/home/simone/Scrivania/Matrice.ods"
# network_public_ip = "79.41.25.238"
# folder_path = "/home/simone/Scrivania/monitors/"

# iTop(compatibility_matrix_path, folder_path, network_public_ip)




# Vedere solo IP
# sudo tcpdump  -n -c 5 ip | awk '{ print gensub(/(.*)\..*/,"\\1","g",$3), $4, gensub(/(.*)\..*/,"\\1","g",$5) }'
