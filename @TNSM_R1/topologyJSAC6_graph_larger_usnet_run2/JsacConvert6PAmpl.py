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
#from heuristicTransparentRegIP2 import *
from JsacHeuristic6OBTR import *

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
    print(root)
    
    # printing the attributes of the
    # first tag from the parent
    print(root[0].attrib)
    
    # printing the text contained within
    # first subtag of the 5th tag from
    # the parent
    # print(root[5][0].text)

    DG = nx.DiGraph()

    for type_tag in root.findall('node'):
        value = type_tag.get('id')
        print(value)
        DG.add_node(int(value)-1)

    for type_tag in root.findall('layer/link'):
        originNodeId = type_tag.get('originNodeId')
        destinationNodeId = type_tag.get('destinationNodeId')
        lengthInKm = type_tag.get('lengthInKm')
        print(originNodeId, destinationNodeId, lengthInKm)
        DG.add_edge(int(originNodeId)-1, int(destinationNodeId)-1, weight=float(lengthInKm))

    return DG


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


class WriteDataFile:
    def __init__(self, sub_folder="7_node/7_request4", output_file_name="paper_") -> None:
        self.file_dir = os.path.join("../topology", "data_file")
        if sub_folder != "":
            self.file_dir = os.path.join(self.file_dir, sub_folder)
        Path(self.file_dir).mkdir(parents=True, exist_ok=True)
        self.init_filename = "initial_" + output_file_name + ".dat"
        self.init_filename = os.path.join(self.file_dir, self.init_filename)

        self.noRegPath_filename = "no_reg_path.dat"
        self.noRegPath_filename = os.path.join(self.file_dir, self.noRegPath_filename)

        self.allPath_filename = "all_path.dat"
        self.allPath_filename = os.path.join(self.file_dir, self.allPath_filename)

        self.rwta = NetworkEnvironment()

        self.DG = self.rwta.DG

        self.num_no_reg_path_list = []
        self.num_all_path_list = []
        self.nodes_list = []
        self.edge_ug_list = []
        self.edge_dg_list = []
        self.length_list = []
        self.num_physical_nodes = []

    def assign_network_environment(self, rwta: NetworkEnvironment):
        self.rwta = rwta

    def generate_data(self):
        with open(self.init_filename, "w") as f:
            f.write("data;\n\n")
        self.nodes_list, self.edge_ug_list, self.edge_dg_list, self.length_list = self.getNodesEdgeLength()
        self.num_physical_nodes = len(self.nodes_list)

        self.write_node_edges()
        self.write_request_sets()
        self.write_trusted_node_set()
        self.write_time_slots_set()
        self.write_quantum_channel_set()
        self.write_quantum_modules_param()

        self.write_path_node_pair_set()
        self.write_path_key_rate_param()
        self.write_qkp_keys_params()
        # self.write_reg_file()

    def write_request_sets(self):
        with open(self.init_filename, "a") as f:
            request_edge_list_num = self.rwta.request_node_pair_num_list
            request_edge_list = [
                "(" + str(elem[0]) + "," + str(elem[1]) + ")" for elem in request_edge_list_num
            ]
            write_set(f, request_edge_list, "R")
            f.write("\n")

            traffic_list = []
            for request in request_edge_list_num:
                traffic_list.append(self.rwta.request_key_rate_dic[request[0], request[1]])
            f.write("# Traffic demand of each request\n")
            write_param_two_indexOneByOne(f, "r", request_edge_list_num, traffic_list)
            f.write("\n")

    def write_path_node_pair_set(self):
        self.write_no_reg_path_set()
        self.write_noreg_path_edges()

    def write_quantum_modules_param(self):
        physical_nodes_list = list(self.rwta.DG.nodes)
        physical_nodes_list.sort()
        # physical_nodes_list_num = physical_nodes_list
        physical_nodes_list = [str(e) for e in physical_nodes_list]
        with open(self.init_filename, "a") as f:
            f.write("\n")
            f.write("param " + "C" + " :=\n")
            for node in physical_nodes_list:
                f.write(str(node))
                f.write(" ")
                f.write(str(self.rwta.num_qkd_modules))
                f.write(" ")
                f.write("\n")
            f.write(";\n")

    def write_path_key_rate_param(self):
        num_path_list = []
        for key in self.rwta.nodePairPathListDict.keys():
            pathList = self.rwta.nodePairPathListDict[key]
            num_path_list.extend(pathList)
        self.num_no_reg_path_list = num_path_list
        with open(self.init_filename, "a") as f:
            f.write("\n")
            f.write("param " + "h" + " :=\n")
            for path in self.num_no_reg_path_list:
                path_key_rate = self.rwta.get_key_rate_of_path(path)
                f.write(str(path))
                f.write(" ")
                f.write(str(path_key_rate))
                f.write(" ")
                f.write("\n")
            f.write(";\n")

    def write_no_reg_path_set(self):
        # physical_nodes_list = [str(e) for e in physical_nodes_list]
        # write_set(f, physical_nodes_list, "Np")
        # f.write("\n")
        num_path_list = []
        for key in self.rwta.nodePairPathListDict.keys():
            pathList = self.rwta.nodePairPathListDict[key]
            num_path_list.extend(pathList)
        self.num_no_reg_path_list = num_path_list
        with open(self.init_filename, "a") as f:
            num_path_list = [str(tmp) for tmp in num_path_list]
            f.write("# set of all paths\n")
            write_set(f, num_path_list, "PhiSetAll")
            f.write("\n")

            for key in self.rwta.nodePairPathListDict.keys():
                request_path_nums = self.rwta.nodePairPathListDict[key]
                request_path_nums = [str(tmp) for tmp in request_path_nums]
                set_name = "PhiSet[" + str(key[0]) + "," + str(key[1]) + "]"
                write_set(f, request_path_nums, set_name)
            f.write("\n")

    def write_all_path_set(self):
        # physical_nodes_list = [str(e) for e in physical_nodes_list]
        # write_set(f, physical_nodes_list, "Np")
        # f.write("\n")
        num_path_list = []
        for key in self.rwta.nodePairPathListDict.keys():
            pathList = self.rwta.nodePairPathListDict[key]
            num_path_list.extend(pathList)

        self.num_all_path_list = num_path_list

        with open(self.init_filename, "a") as f:
            num_path_list = [str(tmp) for tmp in num_path_list]
            f.write("# set of all paths\n")
            write_set(f, num_path_list, "K_a")
            f.write("\n")

            for key in self.rwta.nodePairPathListDict.keys():
                request_path_nums = self.rwta.nodePairPathListDict[key]
                request_path_nums = [str(tmp) for tmp in request_path_nums]
                set_name = "K_a_bar[" + str(key[0]) + "," + str(key[1]) + "]"
                write_set(f, request_path_nums, set_name)
            f.write("\n")


    def write_noreg_path_edges(self):
        with open(self.init_filename, "a") as f:
            f.write("param " + "delta" + " :=\n")
            for path in self.num_no_reg_path_list:
                path_edges_list = self.rwta.pathEdgesDict[path]
                for edge in path_edges_list:
                    f.write(str(path))
                    f.write(" ")
                    f.write(str(edge[0]))
                    f.write(" ")
                    f.write(str(edge[1]))
                    f.write(" ")
                    f.write("1")
                    f.write(" ")
                    f.write("\n")
            f.write(";\n")


    def write_all_path_edges(self):
        with open(self.allPath_filename, "a") as f:
            f.write("param " + "A_a" + " :=\n")
            for path in self.num_all_path_list:
                path_edges_list = self.rwta.pathEdgesDict[path]
                for edge in path_edges_list:
                    f.write(str(edge[0]))
                    f.write(" ")
                    f.write(str(edge[1]))
                    f.write(" ")
                    f.write(str(path))
                    f.write(" ")
                    f.write("1")
                    f.write(" ")
                    f.write("\n")
            f.write(";\n")

    def getNodesEdgeLength(self):
        UG = self.DG.to_undirected()
        print(UG.nodes)
        print(UG.edges)

        nodes_list = list(self.DG.nodes)
        edge_dg_list = list(self.DG.edges)
        edge_ug_list = list(UG.edges)
        length_list = []
        for edge in edge_dg_list:
            length_list.append(self.DG.edges[edge[0], edge[1]]['length'])
        print(nodes_list)
        print(edge_dg_list)
        print(length_list)
        length_list = [int(length) for length in length_list]
        return nodes_list, edge_ug_list, edge_dg_list, length_list

    def write_node_edges(self):
        with open(self.init_filename, "a") as f:
            # for number of physical nodes
            physical_nodes_list = list(self.rwta.DG.nodes)
            physical_nodes_list.sort()
            # physical_nodes_list_num = physical_nodes_list
            physical_nodes_list = [str(e) for e in physical_nodes_list]
            write_set(f, physical_nodes_list, "Np")
            f.write("\n")

            # physical node is represented as 1, 2, 3, 4,.....
            # logical node is logicalNetworkNumber_logicalNodeNumber
            #physical_edge_list = self.edge_ug_list
            physical_edge_list = self.rwta.edge_ug_list
            #physical_edge_list = edge_dg_list
            print(physical_edge_list)
            print("###############################################")
            physical_edge_list_num = physical_edge_list
            physical_edge_list = [
                "(" + str(elem[0]) + "," + str(elem[1]) + ")" for elem in physical_edge_list]
            write_set(f, physical_edge_list, "Ep_u")
            f.write("\n")

    def write_trusted_node_set(self):
        with open(self.init_filename, "a") as f:
            # for number of physical nodes
            physical_nodes_list = list(self.rwta.DG.nodes)
            physical_nodes_list.sort()

            trusted_nodes_list = physical_nodes_list
            #physical_nodes_list_num = trusted_nodes_list
            trusted_nodes_list = [str(e) for e in trusted_nodes_list]
            write_set(f, trusted_nodes_list, "Nt")
            f.write("\n")

    def write_time_slots_set(self):
        with open(self.init_filename, "a") as f:
            time_slot_list = list(range(self.rwta.num_time_slots))
            # physical_nodes_list_num = trusted_nodes_list
            time_slot_list = [str(e) for e in time_slot_list]
            write_set(f, time_slot_list, "T")
            f.write("\n")

            f.write("param T_max := " + str(self.rwta.num_time_slots-1) + ";\n")

    def write_quantum_channel_set(self):
        with open(self.init_filename, "a") as f:
            quantum_channel_list = list(range(self.rwta.num_total_channels))
            # physical_nodes_list_num = trusted_nodes_list
            quantum_channel_list = [str(e) for e in quantum_channel_list]
            write_set(f, quantum_channel_list, "W")
            f.write("\n")

    def write_num_reg(self):
        with open(self.allPath_filename, "a") as f:
            f.write("\n")
            f.write("param " + "q" + " :=\n")
            for path in self.num_all_path_list:
                f.write(str(path))
                f.write(" ")
                f.write(str(1))
                f.write("\n")
            f.write(";\n")

    def write_qkp_keys_params(self):
        with open(self.init_filename, "a") as f:
            qkp_node_pair_list_num = self.rwta.qkp_pair_num_list

            qkp_current_list = []
            for request in self.rwta.qkp_pair_num_list:
                qkp_current_list.append(self.rwta.qkp_remaining_keys_dic[request[0], request[1]])
            f.write("# Traffic demand of each request\n")
            write_param_two_indexOneByOne(f, "Q0", qkp_node_pair_list_num, qkp_current_list)
            f.write("\n")

            qkp_current_list = []
            for request in self.rwta.qkp_pair_num_list:
                qkp_current_list.append(self.rwta.num_max_qkp)
            f.write("# Traffic demand of each request\n")
            write_param_two_indexOneByOne(f, "Qm", qkp_node_pair_list_num, qkp_current_list)
            f.write("\n")

if __name__ == "__main__":
    writeDataFile = WriteDataFile()
    writeDataFile.generate_data()
