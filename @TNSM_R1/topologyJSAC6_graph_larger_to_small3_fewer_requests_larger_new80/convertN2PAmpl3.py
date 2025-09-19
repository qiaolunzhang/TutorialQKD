# importing element tree
# under the alias of ET
from itertools import count
import xml.etree.ElementTree as ET
import networkx as nx
import os
from pathlib import Path
import random
from writeAmplSet import *
from networkx.classes.function import path_weight

def getNxGraph(net2PlanDataFile=""):
    # Passing the path of the
    # xml document to enable the
    # parsing process
    tree = ET.parse(net2PlanDataFile)
    
    # getting the parent tag of
    # the xml document
    root = tree.getroot()
    
    # printing the root (parent) tag
    # of the xml document, along with
    # its memory location
    #print(root)
    
    # printing the attributes of the
    # first tag from the parent
    #print(root[0].attrib)
    
    # printing the text contained within
    # first subtag of the 5th tag from
    # the parent
    # print(root[5][0].text)

    DG = nx.DiGraph()

    for type_tag in root.findall('node'):
        value = type_tag.get('id')
        #print(value)
        DG.add_node(int(value)-1)

    for type_tag in root.findall('layer/link'):
        originNodeId = type_tag.get('originNodeId')
        destinationNodeId = type_tag.get('destinationNodeId')
        lengthInKm = type_tag.get('lengthInKm')
        #print(originNodeId, destinationNodeId, lengthInKm)
        DG.add_edge(int(originNodeId)-1, int(destinationNodeId)-1, weight=float(lengthInKm))

    return DG


def getNodesEdgeLength(DG:nx.DiGraph):
    UG = DG.to_undirected()
    print(UG.nodes)
    print(UG.edges)

    nodes_list = list(DG.nodes)
    edge_dg_list = list(DG.edges)
    edge_ug_list = list(UG.edges)
    length_list = []
    for edge in edge_dg_list:
        length_list.append(DG.edges[edge[0], edge[1]]['weight'])
    print(nodes_list)
    print(edge_dg_list)
    print(length_list)
    length_list = [int(length) for length in length_list]
    return nodes_list, edge_ug_list, edge_dg_list, length_list


def write_param_two_indexOneByOne(f, identifier, two_index_list_num, data_list):
    f.write("param " + identifier + " :=\n")
    index = 0
    for elem in two_index_list_num:
        f.write(str(elem[0]))
        f.write(" ")
        f.write(str(elem[1]))
        f.write(" ")
        f.write(str(data_list[index]))
        index = index + 1
        f.write("\n")
    f.write(";\n")


def write_param_path_seg_reg(f, identifier, path_seg_list:list, path_num_list:list):
    f.write("param " + identifier + " :=\n")
    index = 0
    # print("\n**********************************\n")
    # print(path_edges_list)
    for path_segs_lengths in path_seg_list:
        path = path_num_list[index]
        # print(path_edges)
        for path_segs_index in range(len(path_segs_lengths)):
            f.write(str(path))
            f.write(" ")
            f.write(str(path_segs_index+1))
            f.write(" ")
            f.write(str(path_segs_lengths[path_segs_index]))
            f.write(" ")
            f.write("\n")
        index = index + 1
    f.write(";\n")
    f.write(";\n")


def write_param_paths(f, identifier, path_edges_list:list, path_num_list:list):
    f.write("param " + identifier + " :=\n")
    index = 0
    # print("\n**********************************\n")
    # print(path_edges_list)
    for path_edges in path_edges_list:
        path = path_num_list[index]
        # print(path_edges)
        for edge in path_edges:
            f.write(str(edge[0]))
            f.write(" ")
            f.write(str(edge[1]))
            f.write(" ")
            f.write(str(path))
            f.write(" ")
            f.write("1")
            f.write(" ")
            f.write("\n")
        index = index + 1
    f.write(";\n")

def get_shortest_path_list(DG:nx.DiGraph, k, request_list: list):
    num_path = 0
    path_list = []
    request_path_nums_list = []
    request_path_length_list = []
    request_path_modulations_list = []
    for request in request_list:
        shortestPaths = nx.shortest_simple_paths(DG, request[0], request[1])
        request_path_nums = []
        for counter, path in enumerate(shortestPaths):
            if counter == k:
                break
            num_path = num_path + 1
            request_path_nums.append(num_path)
            tmp = []
            for i in range(0, len(path)-1):
                tmp.append([path[i], path[i+1]])
            path_list.append(tmp)

            tmp = []
            for i in range(0, len(path) - 1):
                tmp.append([path[i], path[i + 1]])
            tmp_length = path_weight(DG, path, weight="weight")
            request_path_length_list.append(tmp_length)
            modulation_list = []
            if tmp_length <= 600:
                modulation_list = [1,2,3,4]
            elif tmp_length <= 1800:
                modulation_list = [2,3,4]
            elif tmp_length <= 3000:
                modulation_list = [3,4]
            else:
                modulation_list = []
            request_path_modulations_list.append(modulation_list)

            # # [1, 2, 3], len([1,2,3]) = 3, 3 // 2 = 1
            # # [1, 2, 3, 4], len([1,2,3,4]) = 4, 4 // 2 = 2
            # # [1, 2], len([1,2]) = 2, 2 // 2 = 1
            # hops_path = len(path)
            # hops_path_first = hops_path // 2
        request_path_nums_list.append(request_path_nums)
    return num_path, path_list, request_path_nums_list, request_path_modulations_list

def get_shortest_path_list_reg(DG:nx.DiGraph, k, request_list: list):
    num_path = 0
    path_list = []
    request_path_nums_list = []
    # each element if the list of length of each segment (seprated by regenerator)
    request_path_reg_seg_list = []
    request_path_modulations_list = []
    for request in request_list:
        shortestPaths = nx.shortest_simple_paths(DG, request[0], request[1])
        request_path_nums = []
        flag = True
        flag2 = True
        for counter, path in enumerate(shortestPaths):
            if counter == k:
                break
            num_path = num_path + 1
            request_path_nums.append(num_path)
            tmp = []
            for i in range(0, len(path)-1):
                tmp.append([path[i], path[i+1]])
            path_list.append(tmp)
            tmp_length = path_weight(DG, path, weight="weight")
            request_path_reg_seg_list.append([tmp_length])
            modulation_list = []
            if tmp_length <= 600:
                modulation_list.append([1, 2, 3, 4])
            elif tmp_length <= 1800:
                modulation_list.append([2, 3, 4])
            elif tmp_length <= 3000:
                modulation_list.append([3, 4])
            else:
                modulation_list.append([])
            request_path_modulations_list.append(modulation_list)

            if flag2 == True and flag == False and tmp_length > 600 and len(path) > 2:
                flag2 = False
                # [1, 2, 3], len([1,2,3]) = 3, 3 // 2 = 1
                # # [1, 2, 3, 4], len([1,2,3,4]) = 4, 4 // 2 = 2
                # # [1, 2], len([1,2]) = 2, 2 // 2 = 1
                # set flag to False==> only generate one regeneration path for each request
                flag = False
                hops_path = len(path)
                modulation_list = []
                tmp_length_list = []
                for i in range(hops_path-1):
                    tmp_length = path_weight(DG, path[i:i+2], weight="weight")
                    tmp_length_list.append(tmp_length)
                    if tmp_length <= 600:
                        modulation_list.append([1, 2, 3, 4])
                    elif tmp_length <= 1800:
                        modulation_list.append([2, 3, 4])
                    elif tmp_length <= 3000:
                        modulation_list.append([3, 4])
                    else:
                        modulation_list.append([])
                    request_path_modulations_list.append(modulation_list)

                num_path = num_path + 1
                request_path_nums.append(num_path)
                tmp = []
                for i in range(0, len(path) - 1):
                    tmp.append([path[i], path[i + 1]])
                path_list.append(tmp)
                request_path_reg_seg_list.append(tmp_length_list)

            if flag and tmp_length > 600 and len(path) > 2:
                # [1, 2, 3], len([1,2,3]) = 3, 3 // 2 = 1
                # # [1, 2, 3, 4], len([1,2,3,4]) = 4, 4 // 2 = 2
                # # [1, 2], len([1,2]) = 2, 2 // 2 = 1
                # set flag to False==> only generate one regeneration path for each request
                flag = False
                hops_path = len(path)

                hops_path_first = hops_path // 2
                tmp_length1 = path_weight(DG, path[0:hops_path_first+1], weight="weight")
                tmp_length2 = path_weight(DG, path[hops_path_first:], weight="weight")
                modulation_list = []
                for tmp_length in [tmp_length1, tmp_length2]:
                    if tmp_length <= 600:
                        modulation_list.append([1, 2, 3, 4])
                    elif tmp_length <= 1800:
                        modulation_list.append([2, 3, 4])
                    elif tmp_length <= 3000:
                        modulation_list.append([3, 4])
                    else:
                        modulation_list.append([])
                    request_path_modulations_list.append(modulation_list)

                num_path = num_path + 1
                request_path_nums.append(num_path)
                tmp = []
                for i in range(0, len(path) - 1):
                    tmp.append([path[i], path[i + 1]])
                path_list.append(tmp)
                request_path_reg_seg_list.append([tmp_length1, tmp_length2])
        request_path_nums_list.append(request_path_nums)
    return num_path, path_list, request_path_nums_list, request_path_reg_seg_list, request_path_modulations_list

# def getShortestPathRequest(DG:nx.DiGraph, R:list):
def getShortestPathRequest(DG:nx.DiGraph):
    shortestPaths = nx.shortest_simple_paths(DG, 1, 2)
    print(shortestPaths)
    k = 5
    for counter, path in enumerate(shortestPaths):
        print(path)
        print(counter)
        if counter == k-1:
            break

def write_all_path_edges_reg(DG: nx.DiGraph, k_shortest_path, num_physical_nodes, file_dir):
    all_edges_list_num = []
    for i in range(1, num_physical_nodes):
        for j in range(i + 1, num_physical_nodes + 1):
            # print(str(i) + " " + str(j))
            all_edges_list_num.append([i, j])
            all_edges_list_num.append([j, i])
    request_edge_list_num = all_edges_list_num
    num_path, path_edges_list, request_path_nums_list, request_path_reg_seg_list, request_path_modulations_list = \
        get_shortest_path_list_reg(DG, k_shortest_path, request_edge_list_num)
    datafile_all_path = os.path.join(file_dir, "all_path_reg.dat")
    with open(datafile_all_path, "w") as f:
        f.write("data;\n\n")
        # set Nlog{V} within Nl;
        # set Nlog[vn1] := vn1_1 vn1_2 vn1_3 vn1_4 vn1_5 vn1_6;
        for i in range(len(request_edge_list_num)):
            request_edge = request_edge_list_num[i]
            request_path_nums = request_path_nums_list[i]
            request_path_nums = [str(tmp) for tmp in request_path_nums]
            set_name = "K_a_bar[" + str(request_edge[0]) + "," + str(request_edge[1]) + "]"
            write_set(f, request_path_nums, set_name)
        f.write("\n")

        for i in range(len(request_path_reg_seg_list)):
            set_name = "Q[" + str(i+1) + "]"
            set_data_list = [str(tmp+1) for tmp in range(len(request_path_reg_seg_list[i]))]
            write_set(f, set_data_list, set_name)
        f.write("\n")

        # physical_nodes_list = [str(e) for e in physical_nodes_list]
        # write_set(f, physical_nodes_list, "Np")
        # f.write("\n")

        num_path_list = list(range(1, num_path + 1))
        num_path_list = [str(tmp) for tmp in num_path_list]
        f.write("# set of all paths\n")
        write_set(f, num_path_list, "K_a")
        f.write("\n")

        #for i in range(len(request_path_reg_seg_list)):
        tmp_path_num_list = [tmp+1 for tmp in range(len(request_path_reg_seg_list))]
        write_param_path_seg_reg(f, "l_seg", request_path_reg_seg_list, tmp_path_num_list)

        f.write("param phi_seg :=\n")
        for i in range(len(request_edge_list_num)):
            # request_edge = request_edge_list_num[i]
            request_path_nums = request_path_nums_list[i]
            for request_path in request_path_nums:
                modulations_segs_list = request_path_modulations_list[request_path - 1]
                for j in range(len(modulations_segs_list)):
                    modulations_list = modulations_segs_list[j]
                    for modulation in modulations_list:
                        f.write(str(request_path) + " " + str(modulation) + " " +  str(j+1) + " 1\n")
        f.write(";\n\n")

        write_param_paths(f, "A_a", path_edges_list, num_path_list)


        # write the intersected paths
        path_inter_list = []
        path_edges_list_str = []
        for path_edges_tmp in path_edges_list:
            path_edges_str = ["(" + str(tmp[0]) + "," + str(tmp[1]) + ")" for tmp in path_edges_tmp]
            path_edges_list_str.append(path_edges_str)
        for i in range(0, len(path_edges_list) - 1):
            path_inter_list.append([num_path_list[i], num_path_list[i]])
            for j in range(i + 1, len(path_edges_list)):
                if list(set(path_edges_list_str[i]).intersection(path_edges_list_str[j])):
                    path_inter_list.append([num_path_list[i], num_path_list[j]])
        path_inter_list_str = [
            "(" + str(elem[0]) + "," + str(elem[1]) + ")" for elem in path_inter_list]
        write_set(f, path_inter_list_str, "K_inter")
        f.write("\n")

def write_all_path_edges(DG:nx.DiGraph, k_shortest_path, num_physical_nodes, file_dir):
        all_edges_list_num = []
        for i in range(1, num_physical_nodes):
            for j in range(i + 1, num_physical_nodes + 1):
                # print(str(i) + " " + str(j))
                all_edges_list_num.append([i, j])
                all_edges_list_num.append([j, i])
        request_edge_list_num = all_edges_list_num
        num_path, path_edges_list, request_path_nums_list, request_path_modulations_list = \
            get_shortest_path_list(DG, k_shortest_path, request_edge_list_num)
        datafile_all_path = os.path.join(file_dir, "all_path.dat")
        with open(datafile_all_path, "w") as f:
            f.write("data;\n\n")
            # set Nlog{V} within Nl;
            # set Nlog[vn1] := vn1_1 vn1_2 vn1_3 vn1_4 vn1_5 vn1_6;
            for i in range(len(request_edge_list_num)):
                request_edge = request_edge_list_num[i]
                request_path_nums = request_path_nums_list[i]
                request_path_nums = [str(tmp) for tmp in request_path_nums]
                set_name = "K_a_bar[" + str(request_edge[0])+"," + str(request_edge[1]) + "]"
                write_set(f, request_path_nums, set_name)
            f.write("\n")

            # physical_nodes_list = [str(e) for e in physical_nodes_list]
            # write_set(f, physical_nodes_list, "Np")
            # f.write("\n")

            num_path_list = list(range(1, num_path+1))
            num_path_list = [str(tmp) for tmp in num_path_list]
            f.write("# set of all paths\n")
            write_set(f, num_path_list, "K_a")
            f.write("\n")

            f.write("param phi :=\n")
            for i in range(len(request_edge_list_num)):
                #request_edge = request_edge_list_num[i]
                request_path_nums = request_path_nums_list[i]
                for request_path in request_path_nums:
                    modulations_list = request_path_modulations_list[request_path-1]
                    for modulation in modulations_list:
                        f.write(str(request_path) + " " + str(modulation) + " 1\n")
            f.write(";\n")

            write_param_paths(f, "A_a", path_edges_list, num_path_list)

            # write the intersected paths
            path_inter_list = []
            path_edges_list_str = []
            for path_edges_tmp in path_edges_list:
                path_edges_str = ["(" + str(tmp[0]) + "," + str(tmp[1]) + ")" for tmp in path_edges_tmp]
                path_edges_list_str.append(path_edges_str)
            for i in range(0, len(path_edges_list) - 1):
                path_inter_list.append([num_path_list[i], num_path_list[i]])
                for j in range(i + 1, len(path_edges_list)):
                    if list(set(path_edges_list_str[i]).intersection(path_edges_list_str[j])):
                        path_inter_list.append([num_path_list[i], num_path_list[j]])
            path_inter_list_str = [
                "(" + str(elem[0]) + "," + str(elem[1]) + ")" for elem in path_inter_list]
            write_set(f, path_inter_list_str, "K_inter")
            f.write("\n")


def write_transponder_data_file(file_dir=""):
    datafile_long_haul = os.path.join(file_dir, "long_haul.dat")
    with open(datafile_long_haul, "w") as f:
        f.write("data;\n\n")
        row_name = list(range(1,10))
        row_name_str = [str(tmp) for tmp in row_name]
        write_set(f, row_name_str, "H")
        f.write("\n")
        row_name = [str(row) for row in row_name]
        data_rate_list = [800, 700, 600, 500, 400, 300, 300, 200, 100]
        data_rate_list = [str(data_rate) for data_rate in data_rate_list]
        write_param_one_index(f, row_name, data_rate_list, "c")
        spectral_width_list = [2, 2, 2, 2, 2, 2, 1, 1, 1]
        spectral_width_list = [str(spectral_width) for spectral_width in spectral_width_list]
        write_param_one_index(f, row_name, spectral_width_list, "w")
        reach_list = [150, 400, 700, 1300, 2500, 4700, 100, 900, 3000]
        reach_list = [str(reach) for reach in reach_list]
        write_param_one_index(f, row_name, reach_list, "l_bar")

    datafile_zr = os.path.join(file_dir, "zr.dat")
    with open(datafile_zr, "w") as f:
        f.write("data;\n\n")
        row_name = list(range(1,5))
        row_name = [str(row) for row in row_name]
        row_name_str = [str(tmp) for tmp in row_name]
        write_set(f, row_name_str, "H")
        f.write("\n")
        data_rate_list = [400, 300, 200, 100]
        data_rate_list = [str(data_rate) for data_rate in data_rate_list]
        write_param_one_index(f, row_name, data_rate_list, "c")
        spectral_width_list = [3, 3, 3, 3]
        spectral_width_list = [str(spectral_width) for spectral_width in spectral_width_list]
        write_param_one_index(f, row_name, spectral_width_list, "w")
        reach_list = [600, 1800, 3000, 3000]
        reach_list = [str(reach) for reach in reach_list]
        write_param_one_index(f, row_name, reach_list, "l_bar")

def generate_data(k_shortest_path = 3, request_percentage=0.5, net2PlanDataFile="",sub_folder="", output_file_name="", 
                    specified_topology="USnet"):
    if specified_topology == "Poliqi":
        num_physical_nodes = 5
        num_physical_links = 5
    if specified_topology == "NSFNET":
        num_physical_nodes = 14
        num_physical_links = 21
    elif specified_topology == "USnet":
        num_physical_nodes = 24
        num_physical_links = 43
    file_dir = os.path.join(".", "data_file")
    if sub_folder != "":
        file_dir = os.path.join(file_dir, sub_folder)
    Path(file_dir).mkdir(parents=True, exist_ok=True)
    
    DG = getNxGraph(net2PlanDataFile)
    nodes_list, edge_ug_list, edge_dg_list, length_list = getNodesEdgeLength(DG)
    num_physical_nodes = len(nodes_list)

    init_filename = "initial_" + str(num_physical_nodes) + "_node_" + output_file_name + ".dat"
    init_filename = os.path.join(file_dir, init_filename)
    # stage_list is the list of 0,1,...,max_stage
    # stage_generate_list represent the stage for data file to write
    print("*****************************")


    with open(init_filename, "w") as f:
        f.write("data;\n\n")

        # for number of physical nodes
        physical_nodes_list = nodes_list
        physical_nodes_list_num = physical_nodes_list
        physical_nodes_list = [str(e) for e in physical_nodes_list]
        write_set(f, physical_nodes_list, "Np")
        f.write("\n")

        # physical node is represented as 1, 2, 3, 4,.....
        # logical node is logicalNetworkNumber_logicalNodeNumber
        physical_edge_list = edge_ug_list
        print(physical_edge_list)
        physical_edge_list_num = physical_edge_list
        physical_edge_list = [
            "(" + str(elem[0]) + "," + str(elem[1]) + ")" for elem in physical_edge_list]
        write_set(f, physical_edge_list, "Ep_u")
        f.write("\n")

        f.write("# Request node pair: (1,2), (1,3)\n")
        all_edges_list_num = []
        for i in range(1, num_physical_nodes):
            for j in range(i + 1, num_physical_nodes + 1):
                # print(str(i) + " " + str(j))
                all_edges_list_num.append([i, j])
        # sorted_sample = [
        #     mylist[i] for i in sorted(random.sample(range(len(mylist)), sample_size))
        # ]
        sample_size = int(request_percentage * len(all_edges_list_num))
        request_edge_list_num = [
            all_edges_list_num[i] for i in sorted(random.sample(range(len(all_edges_list_num)), sample_size))
        ]
        # random.shuffle(all_edges_list)
        # request_edge_list_num = all_edges_list[0:int(request_percentage * len(all_edges_list))]
        request_edge_list = [
            "(" + str(elem[0]) + "," + str(elem[1]) + ")" for elem in request_edge_list_num
        ]
        write_set(f, request_edge_list, "R")
        f.write("\n")

        num_path, path_edges_list, request_path_nums_list, request_path_modulations_list = \
            get_shortest_path_list(DG, k_shortest_path, request_edge_list_num)

        # set Nlog{V} within Nl;
        # set Nlog[vn1] := vn1_1 vn1_2 vn1_3 vn1_4 vn1_5 vn1_6;
        for i in range(len(request_edge_list_num)):
            request_edge = request_edge_list_num[i]
            request_path_nums = request_path_nums_list[i]
            request_path_nums = [str(tmp) for tmp in request_path_nums]
            set_name = "K_bar[" + str(request_edge[0])+"," + str(request_edge[1]) + "]"
            write_set(f, request_path_nums, set_name)
        f.write("\n")

        # physical_nodes_list = [str(e) for e in physical_nodes_list]
        # write_set(f, physical_nodes_list, "Np")
        # f.write("\n")

        num_path_list = list(range(1, num_path+1))
        num_path_list = [str(tmp) for tmp in num_path_list]
        f.write("# set of all paths\n")
        write_set(f, num_path_list, "K")
        f.write("\n")

        write_all_path_edges_reg(DG, k_shortest_path, num_physical_nodes , file_dir)
        write_all_path_edges(DG, k_shortest_path, num_physical_nodes , file_dir)

        f.write("# spectrum-related sets and parameters")
        write_transponder_data_file(file_dir)
        f.write("\n")

        f.write("# Length of links\n")
        write_param_two_indexOneByOne(f, "l", edge_dg_list, length_list)
        f.write("\n")

        traffic_list = []
        for _ in request_edge_list_num:
            traffic_list.append(random.choice([100, 200, 300, 400]))
        f.write("# Traffic demand of each request\n")
        write_param_two_indexOneByOne(f, "t", request_edge_list_num, traffic_list)
        f.write("\n")

        f.write("# equals to 1 if the kth path contains the link\n")
        write_param_paths(f, "A", path_edges_list, num_path_list)

        path_inter_list = []
        path_edges_list_str = []
        for path_edges_tmp in path_edges_list:
            path_edges_str = ["("+str(tmp[0])+","+str(tmp[1])+")" for tmp in path_edges_tmp]
            path_edges_list_str.append(path_edges_str)
        for i in range(0, len(path_edges_list)-1):
            path_inter_list.append([num_path_list[i], num_path_list[i]])
            for j in range(i+1, len(path_edges_list)):
                if list(set(path_edges_list_str[i]).intersection(path_edges_list_str[j])):
                    path_inter_list.append([num_path_list[i], num_path_list[j]])
        path_inter_list_str = [
            "(" + str(elem[0]) + "," + str(elem[1]) + ")" for elem in path_inter_list]
        write_set(f, path_inter_list_str, "K_inter")
        f.write("\n")
        # write_path_inter_set(f, "P_in", path_edges_list, num_path_list)
        # getShortestPathRequest(DG)


if __name__ == "__main__":
    # Poliqi
    # for i in range(8):
    #     generate_data(sub_folder="7_node/5_request", output_file_name="paper_"+str(i))

    # generate_data(k_shortest_path=3, net2PlanDataFile='Net2PlanTopology/example7nodes.n2p', request_percentage=1,
    #                 sub_folder="7_node/7_request2", output_file_name="paper_")
    generate_data(k_shortest_path=3, net2PlanDataFile='Net2PlanTopology/example7nodes.n2p', request_percentage=1,
                    sub_folder="14_node/full_request", output_file_name="paper_")
