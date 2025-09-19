import math
import pickle
from itertools import count
import xml.etree.ElementTree as ET
import networkx as nx
import os
from pathlib import Path
import random
from writeAmplSet import *
from networkx.classes.function import path_weight
import matplotlib.pyplot as plt
from convertN2PAmpl3 import *
import numpy as np
import copy
import statistics

reaches_list = [10, 20, 30, 40, 50]
# the key rate with WDM multiplexing
reaches_key_rate_list = [23, 13, 7, 3.5, 1.9]
# the key rate without WDM multiplexing
#key_rate_list = [74, 41, 22, 12, 6.6]

class NetworkEnvironment:
    def __init__(self, topology="", num_total_channels=5,
                 num_max_qkp=50, num_qkd_modules=3,
                 num_time_slots=3, length_one_time_slot=1, num_time_slot_frame=3,
                 num_shortest_path=1,
                 qkp_key_rate_list=[3, 0, 0, 0, 0], qkp_rate_perc_list=[1, 0, 0, 0, 0],
                 qkp_storing_file_name="storedKeys/storedKeys.pkl", load_qkp_keys_flag=False,
                 request_file_name="requests/requests.pkl",
                 load_request_flag=False, load_request_pair_flag=True,
                 request_percentage=1.0, results_file="results/results.txt", key_rate_list=[],
                 key_rate_perc_list=[], length_factor=1,
                 request_node_pair_name=""):

        self.DG = None
        self.num_total_channels = num_total_channels
        self.num_max_qkp = num_max_qkp
        self.num_qkd_modules = num_qkd_modules
        self.num_time_slots = num_time_slots
        self.length_one_time_slot = length_one_time_slot
        self.num_time_slot_frame = num_time_slot_frame

        # the keys stored in the QKP
        self.qkp_key_rate_list = qkp_key_rate_list
        self.qkp_rate_perc_list = qkp_rate_perc_list

        self.nodePairsList = []
        # Ep_u: so it only contains one direction of one edge
        self.edge_ug_list = []
        self.load_topology(dataFileName='Net2PlanTopology/example7nodes.n2p', topology=topology,
                           length_factor=length_factor)

        # the subpath without regeneration for a node pair: (node i, node j): [list of subpaths]
        self.nodePairPathListDict = {}
        self.pathLengthDic = {}
        # path edge dict: path: [(edge), (edge)]
        self.pathEdgesDict = {}
        # path nodes dict: path: [node, node]
        self.pathNodesDict = {}
        self.numPath = 0
        self.generateAllPaths(k=num_shortest_path)

        self.nodePairsPathThresholdNumEdgesDic = {}
        k_threshold = 1
        for node_pair in self.nodePairsList:
            self.nodePairsPathThresholdNumEdgesDic[node_pair[0], node_pair[1]] = 0
            node_pair_path_list = self.nodePairPathListDict[node_pair[0], node_pair[1]]
            for path_index in range(0, k_threshold):
                path_num_edges = len(self.pathEdgesDict[node_pair_path_list[path_index]])
                if self.nodePairsPathThresholdNumEdgesDic[node_pair[0], node_pair[1]] < path_num_edges:
                    self.nodePairsPathThresholdNumEdgesDic[node_pair[0], node_pair[1]] = path_num_edges

        # assigned path for requests: [(p, [[time-slot, dataRate], [time-slot, dataRate], time-slot, dataRate), ()]
        # [[current channels, dataRate], [previous channels, dataRate], [QKP, dataRate]]
        self.pathOfRequestsDict = {}
        # remaining data rate dict: (subpath, channel): available data rate
        self.remainingDataRateDict = {}
        # number of channels
        self.pathNumChannelsDict = {}
        for i in self.pathNodesDict.keys():
            self.pathNumChannelsDict[i] = 0
        # assigned requests: (subpath, channel): [list of requests]
        self.subpathAssignedRequestsDict = {}
        self.subpathAssignedSlotsDict = {}

        # Deepcopy -- The default behavior is a "deepcopy" where the graph structure as well as all data attributes and
        # any objects they might contain are copied. The entire graph object is new so that changes in the copy do not
        # affect the original object.
        self.DG_compute = copy.deepcopy(self.DG)

        # this is the node pair for request
        self.request_node_pair_num_list = []
        self.request_percentage = request_percentage
        # self.get_request(request_file_name=request_file_name, load_flag=load_request_flag)
        if load_request_pair_flag and request_node_pair_name != "":
            self.get_request(request_file_name=request_node_pair_name, load_flag=load_request_pair_flag)
        else:
            self.get_request(request_file_name=request_file_name, load_flag=load_request_pair_flag)

        self.request_key_rate_dic = {}
        self.assign_request_keyrate(keyRate=12, multiBitrateFlag=True, unidirectionalFlag=False,
                                    request_file_name=request_file_name,
                                    load_flag=load_request_flag,
                                    key_rate_list=key_rate_list, data_rate_perc_list=key_rate_perc_list)

        self.request_key_rate_remaining_dic = copy.deepcopy(self.request_key_rate_dic)

        # Actually I also use the key rate to represent the keys stored in QKP here
        self.qkp_pair_num_list = []
        self.qkp_remaining_keys_dic = {}

        self.assign_qkp_storing_keys(qkp_key_rate=3, multi_key_rate_flag=True,
                                     qkp_storing_file_name=qkp_storing_file_name, load_flag=load_qkp_keys_flag)

        self.qkp_remaining_keys_original_dic = copy.deepcopy(self.qkp_remaining_keys_dic)

        self.requestLightpathIndexListDict = {}
        for request in self.request_node_pair_num_list:
            self.requestLightpathIndexListDict[request[0], request[1]] = []

        self.results_file = results_file
        self.unused_channel_dic = {}
        for pair in self.qkp_remaining_keys_dic.keys():
            for time_slot in range(self.num_time_slots):
                self.unused_channel_dic[pair[0], pair[1], time_slot] = list(range(self.num_total_channels))

        self.time_auxiliary_graph = nx.DiGraph()
        # todo: add this part to improve the efficiency
        self.time_physical_to_auxiliary_edge_list_dic = {}

        self.request_physical_hops_list_dic = {}
        self.request_virtual_hops_list_dic = {}
        self.request_qkd_modules_list_dic = {}

        self.num_max_qkp_node = self.num_max_qkp * (len(list(self.DG.nodes)) - 1)

    def get_japan_topology(self):
        DG = nx.DiGraph()
        edge_list = [[1,2], [1,3], [2,4], [3,4], [4,5], [4,6],[5,6], [5,7], [5,9], [6,8], [7,8], [7,12], [8,10], [9,12], [9,14], [10,11], [10,12], [11,12], [11,13], [12,13], [12,14], [13, 14]]
        self.edge_ug_list = edge_list
        length_list = [160, 240, 240, 240, 80, 40, 40, 80, 240, 160, 80, 240, 160, 240, 240, 40, 40, 40, 320, 320, 240, 160]
        for index in range(len(edge_list)):
            edge = edge_list[index]
            length = length_list[index]
            DG.add_edge(edge[0], edge[1], weight=length)
            DG.add_edge(edge[1], edge[0], weight=length)

        return DG

    def get_german_topology(self):
        DG = nx.DiGraph()
        # edge_list = [[1,7], [1,8], [1,11], [2,7], [2,8], [2,14], [3,5], [3,8], [3,10], [3,14]]
        edge_list = [[1,7], [1,8], [1,11], [2,7], [2,8], [2,14], [3,5], [3,8], [3,10], [3,14], [4,5], [4,10],
                     [6,8], [6,10], [6,11], [6,12], [6,15], [7,8], [8,11], [9,12], [9,16], [11,15], [13,15], [13,17],
                     [15,16], [16,17]]
        self.edge_ug_list = edge_list
        length_list = [306, 298, 174, 114, 120, 144, 37, 208, 88, 278, 36, 41,
                       316, 182, 353, 85, 224, 157, 258, 64, 74, 275, 179, 143, 187, 86]
        length_list = [int(item / (max(length_list) / 10)) for item in length_list]
        for index in range(len(edge_list)):
            edge = edge_list[index]
            length = length_list[index]
            DG.add_edge(edge[0], edge[1], weight=length)
            DG.add_edge(edge[1], edge[0], weight=length)

        return DG

    def get_poliqi_topology(self):
        DG = nx.DiGraph()
        # edge_list = [[1,7], [1,8], [1,11], [2,7], [2,8], [2,14], [3,5], [3,8], [3,10], [3,14]]
        edge_list = [[1,2], [1,5], [2,3], [3,4], [4,5]]
        self.edge_ug_list = edge_list
        # leo->army barracks->administration district
        # length_list = [6, 6, 6, 6, 6]
        # length_list = [5, 5, 5, 5, 5]
        # length_list = [6, 6, 5, 5, 5]
        length_list = [6, 6, 5, 5, 5]
        # length_list = [8, 2, 6, 4, 5]
        for index in range(len(edge_list)):
            edge = edge_list[index]
            length = length_list[index]
            DG.add_edge(edge[0], edge[1], weight=length)
            DG.add_edge(edge[1], edge[0], weight=length)

        return DG

    def get_usnet_topology(self):
        DG = nx.DiGraph()
        # edge_list = [[1,7], [1,8], [1,11], [2,7], [2,8], [2,14], [3,5], [3,8], [3,10], [3,14]]
        edge_list = [[1,2], [1,6], [2,3], [2,6], [3,4], [3,5], [3,7], [4,5], [4,7], [5,8], [6,7], [6,9],
                     [6,11], [7,8], [7,9], [8,10], [9,10], [9,11], [9,12], [10,13], [10,14], [11,12], [11,15], [11,19],
                     [12,13], [12,16], [13,14], [13,17], [14,18], [15,16], [15,20], [16,17], [16,21], [16,22], [17,18],
                     [17,22], [17,23], [18,24], [19,20], [20,21], [21,22], [22,23], [23,24]]
        self.edge_ug_list = edge_list
        # length_list = [306, 298, 174, 114, 120, 144, 37, 208, 88, 278, 36, 41,
        #                316, 182, 353, 85, 224, 157, 258, 64, 74, 275, 179, 143, 187, 86]
        # length_list = []
        # for _ in edge_list:
        #     length_list.append(random.choice([2, 3, 4, 5, 6, 7, 8]))
        length_list = [4, 5, 6, 2, 5, 4, 7, 7, 4, 7, 5, 7, 5, 7, 5, 6, 6, 2, 7, 4, 7, 3, 2, 3, 7, 7, 4, 7, 5, 8, 7, 7, 2, 7, 4, 5, 5, 3, 2, 5, 2, 2, 6]
        for index in range(len(edge_list)):
            edge = edge_list[index]
            length = length_list[index]
            DG.add_edge(edge[0], edge[1], weight=length)
            DG.add_edge(edge[1], edge[0], weight=length)

        return DG

    def load_topology(self, dataFileName='Net2PlanTopology/example7nodes.n2p', topology="",
                      length_factor=1):
        net2PlanDataFile=dataFileName
        self.DG = getNxGraph(net2PlanDataFile)
        if topology == "japan":
            self.DG = self.get_japan_topology()
        elif topology == "german":
            self.DG = self.get_german_topology()
        elif topology == "poliqi":
            self.DG = self.get_poliqi_topology()
        elif topology == "usnet":
            self.DG = self.get_usnet_topology()
        else:
            UG = self.DG.to_undirected()
            # print(UG.nodes)
            # print(UG.edges)

            nodes_list = list(self.DG.nodes)
            edge_dg_list = list(self.DG.edges)
            edge_ug_list = list(UG.edges)
            self.edge_ug_list = edge_ug_list

        # the maximum transmission distance is 50, so if the distance of a link is more than 50, we shrink it to 30
        for edge in self.DG.edges:
            if self.DG.edges[edge]['weight'] * length_factor <= 50:
                self.DG.edges[edge]['weight'] = length_factor * self.DG.edges[edge]['weight']
            # comment the following because we only want to remove the one that lenth is not ok
            else:
                self.DG.edges[edge]['weight'] = 50

        for node in self.DG.nodes:
            self.DG.nodes[node]['qkd-modules-dic'] = {}
            for i in range(self.num_time_slots):
                self.DG.nodes[node]['qkd-modules-dic'][i] = self.num_qkd_modules

        for edge in self.DG.edges:
            # self.DG.edges[edge[0], edge[1]]['channels'] = list(range(30))
            self.DG.edges[edge]['channels'] = [0 for i in range(self.num_total_channels)]
            self.DG.edges[edge]['channels-dic'] = {}
            for i in range(self.num_time_slots):
                self.DG.edges[edge]['channels-dic'][i] = [0 for i in range(self.num_total_channels)]

            self.DG.edges[edge]['length'] = self.DG.edges[edge]['weight']
            # initialize the weight to 1
            self.DG.edges[edge]['weight'] = 1
            # mark whether it is auxiliary graph
            self.DG.edges[edge]['auxiliary'] = False

            # todo: add the path number related to the physical link (may use multiple physical links)
            self.DG.edges[edge]['pathList'] = []
            # list of modulation format for different paths
            # [[1, 4]]
            # todo: add the edges in the path for the physical link
            # [[[1,2], [2,4]]
            self.DG.edges[edge]['pathEdges'] = []
            # [[1,2,4]]
            self.DG.edges[edge]['pathNodes'] = []

            # list of lists, each element is the list of occuplied slots
            # [[[1,2,3], [4,5,6]]]
            # todo: occupliedSlotsList, may be updated
            # self.DG.edges[edge]['occupliedSlotsList'] = []
            # [[1, 2]]
            self.DG.edges[edge]['pathModulationList'] = []
            # list of available bit rate for different paths (maximum - utilized)
            # [[50, 100]]
            self.DG.edges[edge]['availabeBitRateList'] = []
            # print(self.DG.edges[1,3]['channels'])

        nodes_list = list(self.DG.nodes)
        for i in range(len(nodes_list)):
            for j in range(i+1, len(nodes_list)):
                self.nodePairsList.append((nodes_list[i], nodes_list[j]))
                self.nodePairsList.append((nodes_list[j], nodes_list[i]))

    def generateAllPaths(self, k=2):
        for nodePair in self.nodePairsList:
            # generate k shortest paths
            X = nx.shortest_simple_paths(self.DG, nodePair[0], nodePair[1], weight='length')
            shortestKPaths = []
            for counter, path in enumerate(X):
                #print(path)
                shortestKPaths.append(path)
                if counter == k - 1:
                    break
            self.generateRegenerationSubpath(shortestKpaths=shortestKPaths, nodePair=nodePair)

    def generateRegenerationSubpath(self, shortestKpaths:list, nodePair):
        noRegSubpathList = []
        for shortestPath in shortestKpaths:
            lengthPath = path_weight(self.DG, shortestPath, weight='length')
            self.numPath = self.numPath + 1

            noRegSubpathList.append(self.numPath)
            self.pathLengthDic[self.numPath] = lengthPath
            self.pathNodesDict[self.numPath] = shortestPath
            # the edges of the path
            edges_list = []
            for index in range(0, len(shortestPath)-1):
                edges_list.append((shortestPath[index], shortestPath[index+1]))
            self.pathEdgesDict[self.numPath] = edges_list

        if len(noRegSubpathList) > 0:
            self.nodePairPathListDict[nodePair[0], nodePair[1]] = noRegSubpathList

    def get_request(self, request_file_name="requests/requests.pkl", load_flag=False):
        # todo: add the path number related to auxiliary link
        # todo: add the links related to path to the attributes of graph
        if load_flag:
            request_file = open(request_file_name, "rb")
            request_bitrate_list = pickle.load(request_file)
            self.request_node_pair_num_list = []
            for request in request_bitrate_list.keys():
                self.request_node_pair_num_list.append([request[0], request[1]])
            return
        nodes_list, edge_ug_list, edge_dg_list, length_list = getNodesEdgeLength(self.DG)
        num_physical_nodes = len(nodes_list)

        all_edges_list_num = []
        for i in range(1, num_physical_nodes):
            for j in range(i + 1, num_physical_nodes + 1):
                # print(str(i) + " " + str(j))
                # todo: this time, just use one direction
                # todo: remove adjacent node pairs
                if (i, j) in edge_dg_list:
                    continue
                all_edges_list_num.append([i, j])
                #all_edges_list_num.append([j, i])
        edge_ug_list = [[item[0], item[1]] if item[0] < item[1] else [item[1], item[0]] for item in edge_ug_list]
        neighbor_list = random.sample(edge_ug_list, 1)
        all_edges_list_num.extend(neighbor_list)
        # sorted_sample = [
        #     mylist[i] for i in sorted(random.sample(range(len(mylist)), sample_size))
        # ]
        if self.request_percentage < 1:
            sample_size = int(self.request_percentage * len(all_edges_list_num))
            self.request_node_pair_num_list = [
                all_edges_list_num[i] for i in sorted(random.sample(range(len(all_edges_list_num)), sample_size))
            ]
        else:
            self.request_node_pair_num_list = all_edges_list_num

        # todo: check small number of request
        # self.request_edge_list_num = [[2,4], [3,4]]
        # self.request_edge_list_num = [[2,4]]
        #print(self.request_edge_list_num)

    def assign_request_keyrate(self, keyRate=12, multiBitrateFlag=False, unidirectionalFlag=True,
                               request_file_name="requests/requests.pkl", load_flag=False,
                               key_rate_list=[], data_rate_perc_list=[]):
        if load_flag:
            request_file = open(request_file_name, "rb")
            self.request_key_rate_dic = pickle.load(request_file)
            return

        if unidirectionalFlag:
            for i in range(0, len(self.request_node_pair_num_list), 2):
                if multiBitrateFlag:
                    keyRate = random.choice([3, 6, 9, 12])
                nodePair = self.request_node_pair_num_list[i]
                self.request_key_rate_dic[nodePair[0], nodePair[1]] = keyRate
                self.request_key_rate_dic[nodePair[1], nodePair[0]] = keyRate
        else:
            for i in range(len(self.request_node_pair_num_list)):
                if multiBitrateFlag:
                    keyRate = random.choice([3, 6, 9, 12])
                nodePair = self.request_node_pair_num_list[i]
                self.request_key_rate_dic[nodePair[0], nodePair[1]] = keyRate

        if len(key_rate_list) > 0:
            request_index_list = [i for i in range(len(self.request_node_pair_num_list))]
            random.shuffle(request_index_list)
            data_rate_num_list = [int(perc * len(request_index_list)) for perc in data_rate_perc_list]
            data_rate_num_list[-1] = len(request_index_list) - sum(data_rate_num_list[0:-1])
            for i in range(len(data_rate_num_list)):
                start_index = 0
                start_index += sum(data_rate_num_list[0:i])
                end_index = sum(data_rate_num_list[0:i+1])
                for j in range(start_index, end_index):
                    nodePair = self.request_node_pair_num_list[request_index_list[j]]
                    self.request_key_rate_dic[nodePair[0], nodePair[1]] = key_rate_list[i]

        # set the required bit rate
        request_file = open(request_file_name, "wb")
        pickle.dump(self.request_key_rate_dic, request_file)
        request_file.close()

    def get_qkp_pair_storing_maximum(self, node_pair:list, qkp_remaining_keys_dic:dict):
        node_pair_left = node_pair[0]
        node_pair_right = node_pair[1]

        node_pair_left_qkp_current = 0
        node_pair_right_qkp_current = 0

        for qkp_pair in self.qkp_pair_num_list:
            if node_pair_left in qkp_pair:
                node_pair_left_qkp_current += qkp_remaining_keys_dic[qkp_pair[0], qkp_pair[1]]
            if node_pair_right in qkp_pair:
                node_pair_right_qkp_current += qkp_remaining_keys_dic[qkp_pair[0], qkp_pair[1]]

        node_pair_left_qkp_additional_maximum = self.num_max_qkp_node - node_pair_left_qkp_current
        node_pair_right_qkp_additional_maximum = self.num_max_qkp_node - node_pair_right_qkp_current
        qkp_storing_node_additional_maximum = \
            min(node_pair_left_qkp_additional_maximum, node_pair_right_qkp_additional_maximum)
        qkp_storing_node_additional_maximum = max(0, qkp_storing_node_additional_maximum)
        qkp_pair_storing_maximum = \
            qkp_remaining_keys_dic[node_pair_left, node_pair_right] + qkp_storing_node_additional_maximum
        return qkp_pair_storing_maximum

    def assign_qkp_storing_keys(self, qkp_key_rate=12, multi_key_rate_flag=False,
                                qkp_storing_file_name="storedKeys/storedKeys.pkl", load_flag=False):
        # actually hte node pair is already the same
        nodes_list = list(self.DG.nodes)
        nodes_list.sort()
        for i in range(len(nodes_list)):
            for j in range(i+1, len(nodes_list)):
                self.qkp_pair_num_list.append((nodes_list[i], nodes_list[j]))

        if load_flag:
            request_file = open(qkp_storing_file_name, "rb")
            self.qkp_remaining_keys_dic = pickle.load(request_file)
            return

        for i in range(len(self.qkp_pair_num_list)):
            if multi_key_rate_flag:
                qkp_key_rate = random.choice([3, 6, 9, 12])
            node_pair = self.qkp_pair_num_list[i]
            self.qkp_remaining_keys_dic[node_pair[0], node_pair[1]] = qkp_key_rate

        if len(self.qkp_key_rate_list) > 0:
            request_index_list = [i for i in range(len(self.qkp_pair_num_list))]
            random.shuffle(request_index_list)
            qkp_key_rate_num_list = [int(perc * len(request_index_list)) for perc in self.qkp_rate_perc_list]
            qkp_key_rate_num_list[-1] = len(request_index_list) - sum(qkp_key_rate_num_list[0:-1])
            for i in range(len(qkp_key_rate_num_list)):
                start_index = 0
                start_index += sum(qkp_key_rate_num_list[0:i])
                end_index = sum(qkp_key_rate_num_list[0:i+1])
                for j in range(start_index, end_index):
                    node_pair = self.qkp_pair_num_list[request_index_list[j]]
                    self.qkp_remaining_keys_dic[node_pair[0], node_pair[1]] = self.qkp_key_rate_list[i]

        # set the required bit rate
        request_file = open(qkp_storing_file_name, "wb")
        pickle.dump(self.qkp_remaining_keys_dic, request_file)
        request_file.close()


    def initialize_time_auxiliary_graph_tr(self, DG_tmp:nx.DiGraph, start_time_slot_index=0, end_time_slot_index=0,
                                           qkp_remaining_keys_dict={}, reach_index=0, channel_index_selected=0,
                                           request_key_rate=0, storing=False, request=[-1,-1]):
        if DG_tmp is None:
            DG_tmp = self.DG
        if len(qkp_remaining_keys_dict.keys()) == 0:
            qkp_remaining_keys_dict = self.qkp_remaining_keys_original_dic

        self.time_auxiliary_graph.clear()
        nodes_list = list(self.DG.nodes)
        nodes_list.sort()
        for node in nodes_list:
            self.time_auxiliary_graph.add_node(node)
        reach_key_rate = reaches_key_rate_list[reach_index]
        if not storing:
            for i1 in range(0, len(nodes_list)-1):
                for i2 in range(i1+1, len(nodes_list)):
                    node1 = nodes_list[i1]
                    node2 = nodes_list[i2]
                    if (node1, node2) in qkp_remaining_keys_dict.keys():
                        if qkp_remaining_keys_dict[node1, node2] >= reach_key_rate / self.num_time_slots or \
                                qkp_remaining_keys_dict[node1, node2] >= request_key_rate:
                            # edge_key_rate = min(reach_key_rate / self.num_time_slots, qkp_remaining_keys_dict[node1, node2])
                            edge_key_rate = qkp_remaining_keys_dict[node1, node2]
                            # new edge
                            path_nodes_list_tmp = nx.shortest_path(self.DG, node1, node2)
                            num_edges_tmp = len(path_nodes_list_tmp) - 1
                            # self.time_auxiliary_graph.add_edge(node1, node2, weight=6E-6*num_edges_tmp, keyrate=edge_key_rate)
                            # self.time_auxiliary_graph.add_edge(node2, node1, weight=6E-6*num_edges_tmp, keyrate=edge_key_rate)
                            self.time_auxiliary_graph.add_edge(node1, node2, weight=6E6*num_edges_tmp, keyrate=edge_key_rate)
                            self.time_auxiliary_graph.add_edge(node2, node1, weight=6E6*num_edges_tmp, keyrate=edge_key_rate)

                            if str(node1) != str(request[0]) and str(node1) != str(request[1]):
                                for time_slot_index in range(start_time_slot_index, end_time_slot_index+1):
                                    if DG_tmp.nodes[node1]['qkd-modules-dic'][time_slot_index] == 1:
                                        node_from_time_slot_name = str(node1) + "from" + str(time_slot_index)
                                        self.time_auxiliary_graph.add_node(node_from_time_slot_name)
                                        self.time_auxiliary_graph.add_edge(node_from_time_slot_name, node2, weight=6E6 * num_edges_tmp,
                                                                           keyrate=edge_key_rate)

                            if str(node2) != str(request[0]) and str(node2) != str(request[1]):
                                for time_slot_index in range(start_time_slot_index, end_time_slot_index+1):
                                    if DG_tmp.nodes[node2]['qkd-modules-dic'][time_slot_index] == 1:
                                        node_from_time_slot_name = str(node2) + "from" + str(time_slot_index)
                                        self.time_auxiliary_graph.add_node(node_from_time_slot_name)
                                        self.time_auxiliary_graph.add_edge(node_from_time_slot_name, node1, weight=6E6 * num_edges_tmp,
                                                                           keyrate=edge_key_rate)

        for time_slot_index in range(start_time_slot_index, end_time_slot_index+1):
            activated_nodes_list = []
            for node in nodes_list:
                if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index]:
                    activated_nodes_list.append(node)
                    # add the subnode of a node
                    in_node_name = str(time_slot_index) + "-" + str(node) + "-in"
                    out_node_name = str(time_slot_index) + "-" + str(node) + "-out"
                    self.time_auxiliary_graph.add_node(in_node_name)
                    self.time_auxiliary_graph.add_node(out_node_name)
                    # add the edges between the subnodes
                    if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index] > 1:
                        self.time_auxiliary_graph.add_edge(in_node_name, out_node_name, weight=1)
                    # todo: check edge weight
                    if time_slot_index == end_time_slot_index:
                        if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index] > 1:
                            self.time_auxiliary_graph.add_edge(node, out_node_name, weight=0.5+6E-9)
                            self.time_auxiliary_graph.add_edge(in_node_name, node, weight=0.5+6E-9)
                        else:
                            self.time_auxiliary_graph.add_edge(node, out_node_name, weight=1.25+6E-9)
                            if str(node) == str(request[0]) or str(node) == str(request[1]):
                                self.time_auxiliary_graph.add_edge(in_node_name, node, weight=1.25+6E-9)
                            else:
                                node_from_time_slot_name = str(node) + "from" + str(time_slot_index)
                                self.time_auxiliary_graph.add_edge(in_node_name, node_from_time_slot_name, weight=1.25+6E-9)
                                for time_slot_index_restricted in range(start_time_slot_index, end_time_slot_index+1):
                                    if time_slot_index == time_slot_index_restricted:
                                        continue
                                    if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index_restricted]:
                                        out_node_name_restricted = str(time_slot_index_restricted) + "-" + str(node) + "-out"
                                        if time_slot_index_restricted == end_time_slot_index:
                                            if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index_restricted] > 1:
                                                self.time_auxiliary_graph.add_edge(node_from_time_slot_name, out_node_name_restricted,
                                                                                   weight=0.5 + 6E-9)
                                            else:
                                                self.time_auxiliary_graph.add_edge(node_from_time_slot_name, out_node_name_restricted,
                                                                                   weight=1.25 + 6E-9)
                    else:
                        if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index] > 1:
                            self.time_auxiliary_graph.add_edge(node, out_node_name, weight=0.5+2*6E-9)
                            self.time_auxiliary_graph.add_edge(in_node_name, node, weight=0.5+2*6E-9)
                        else:
                            self.time_auxiliary_graph.add_edge(node, out_node_name, weight=1.25+2*6E-9)
                            if str(node) == str(request[0]) or str(node) == str(request[1]):
                                self.time_auxiliary_graph.add_edge(in_node_name, node, weight=1.25+2*6E-9)
                            else:
                                node_from_time_slot_name = str(node) + "from" + str(time_slot_index)
                                self.time_auxiliary_graph.add_edge(in_node_name, node_from_time_slot_name, weight=1.25+2*6E-9)
                                for time_slot_index_restricted in range(start_time_slot_index, end_time_slot_index+1):
                                    if time_slot_index == time_slot_index_restricted:
                                        continue
                                    if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index_restricted]:
                                        out_node_name_restricted = str(time_slot_index_restricted) + "-" + str(node) + "-out"
                                        if time_slot_index_restricted == end_time_slot_index:
                                            if DG_tmp.nodes[node]['qkd-modules-dic'][time_slot_index_restricted] > 1:
                                                self.time_auxiliary_graph.add_edge(node_from_time_slot_name, out_node_name_restricted,
                                                                                   weight=0.5 + 6E-9)
                                            else:
                                                self.time_auxiliary_graph.add_edge(node_from_time_slot_name, out_node_name_restricted,
                                                                                   weight=1.25 + 6E-9)
                    # self.time_auxiliary_graph.add_edge(node, out_node_name, weight=1)

            for i1 in range(len(activated_nodes_list)-1):
                for i2 in range(i1+1, len(activated_nodes_list)):
                    node1 = activated_nodes_list[i1]
                    node2 = activated_nodes_list[i2]
                    if (node1, node2) not in self.DG.edges:
                        continue
                    in_node1_name = str(time_slot_index) + "-" + str(node1) + "-in"
                    out_node1_name = str(time_slot_index) + "-" + str(node1) + "-out"
                    in_node2_name = str(time_slot_index) + "-" + str(node2) + "-in"
                    out_node2_name = str(time_slot_index) + "-" + str(node2) + "-out"

                    node_pair = [node1, node2]
                    flag, path_selected = \
                        self.check_available_channels_between_node_pair(time_slot_index, DG_tmp, node_pair,
                                                                        required_reach_index=reach_index,
                                                                        channel_index_selected=channel_index_selected,
                                                                        efficiency_first_run=True)

                    channel_index_edge = 0
                    if flag:
                        channel_index_edge = channel_index_selected
                    if time_slot_index != end_time_slot_index and not flag:
                        for channel_index in range(0, self.num_total_channels):
                            if channel_index == channel_index_selected:
                                continue
                            flag, path_selected = \
                                self.check_available_channels_between_node_pair(time_slot_index, DG_tmp, node_pair,
                                                                                required_reach_index=reach_index,
                                                                                channel_index_selected=channel_index,
                                                                                efficiency_first_run=True)
                            if flag:
                                channel_index_edge = channel_index
                                break

                    # todo: check new weight
                    if DG_tmp.nodes[node1]['qkd-modules-dic'][time_slot_index] == 1 or \
                            DG_tmp.nodes[node2]['qkd-modules-dic'][time_slot_index] == 1:
                        edge_weight = 2.5
                    else:
                        edge_weight = 1

                    if flag:
                        path_key_rate = self.get_key_rate_of_path(path_selected)
                        num_edges = len(self.pathEdgesDict[path_selected])
                        self.time_auxiliary_graph.add_edge(out_node1_name, in_node2_name,
                                                           weight=edge_weight+num_edges*6E-6,
                                                           channel_index=channel_index_edge,
                                                           path=path_selected,
                                                           keyrate=path_key_rate / self.num_time_slots)
                        # self.time_auxiliary_graph.add_edge(out_node2_name, in_node1_name, weight=1+num_edges*6E-6,
                        # path=path_selected, keyrate=path_key_rate / self.num_time_slots)

                    node_pair = [node2, node1]
                    flag, path_selected = \
                        self.check_available_channels_between_node_pair(time_slot_index, DG_tmp, node_pair,
                                                                        required_reach_index=reach_index,
                                                                        channel_index_selected=channel_index_selected,
                                                                        efficiency_first_run=True)

                    channel_index_edge = 0
                    if flag:
                        channel_index_edge = channel_index_selected
                    if time_slot_index != end_time_slot_index and not flag:
                        for channel_index in range(0, self.num_total_channels):
                            if channel_index == channel_index_selected:
                                continue
                            flag, path_selected = \
                                self.check_available_channels_between_node_pair(time_slot_index, DG_tmp, node_pair,
                                                                                required_reach_index=reach_index,
                                                                                channel_index_selected=channel_index,
                                                                                efficiency_first_run=True)
                            if flag:
                                channel_index_edge = channel_index
                                break

                    if flag:
                        path_key_rate = self.get_key_rate_of_path(path_selected)
                        num_edges = len(self.pathEdgesDict[path_selected])
                        if path_key_rate == reach_key_rate or request_key_rate <= path_key_rate / self.num_time_slots:
                            self.time_auxiliary_graph.add_edge(out_node2_name, in_node1_name,
                                                               weight=edge_weight + num_edges * 6E-6,
                                                               channel_index=channel_index_edge,
                                                               path=path_selected,
                                                               keyrate=path_key_rate / self.num_time_slots)
        #self.check_graph_figure(self.time_auxiliary_graph)

    def check_graph_figure(self, graph: nx.DiGraph):
        if graph is None:
            graph = self.time_auxiliary_graph
        fig = plt.figure(figsize=(12, 12))
        ax = plt.subplot(111)
        ax.set_title('Graph - Shapes', fontsize=10)
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, node_size=1500, node_color='yellow', font_size=8, font_weight='bold',
                with_labels=True)
        plt.tight_layout()
        plt.savefig("Graph.png", format="PNG")
        plt.show()

    def get_shortest_path_length(self, request):
        path_list = self.nodePairPathListDict[request[0], request[1]]
        return self.pathLengthDic[path_list[0]]

    def process_request(self):
        # the following class can add the same link twice, duplicate edges are replicated
        # G = nx.MultiGraph()
        self.ordered_request_edge_list = []
        self.ordered_request_edge_list = sorted(self.request_node_pair_num_list,
                                                key=lambda item: (self.get_shortest_path_length(item), self.request_key_rate_remaining_dic[item[0], item[1]]), reverse=False)

        # serve the request in the self.ordered_request_edge_list
        self.serve_ordered_request()
        self.serve_ordered_request_second_pass()

        average_physical_hops = 0
        average_virtual_hops = 0
        average_qkd_modules = 0
        num_request = 0

        for request in self.request_key_rate_remaining_dic.keys():
            if request in self.request_physical_hops_list_dic.keys():
                num_request = num_request + 1
                if len(self.request_physical_hops_list_dic[request[0], request[1]]) == 0:
                    self.request_physical_hops_list_dic[request[0], request[1]].append(0)
                if len(self.request_virtual_hops_list_dic[request[0], request[1]]) == 0:
                    self.request_virtual_hops_list_dic[request[0], request[1]].append(0)
                if len(self.request_qkd_modules_list_dic[request[0], request[1]]) == 0:
                    self.request_qkd_modules_list_dic[request[0], request[1]].append(0)
                average_physical_hops += statistics.mean(self.request_physical_hops_list_dic[request[0], request[1]])
                average_virtual_hops += statistics.mean(self.request_virtual_hops_list_dic[request[0], request[1]])
                average_qkd_modules += statistics.mean(self.request_qkd_modules_list_dic[request[0], request[1]])
        average_physical_hops = average_physical_hops / num_request
        average_virtual_hops = average_virtual_hops / num_request
        average_qkd_modules = average_qkd_modules / num_request

        # self.serve_ordered_request_ob()
        # self.serve_ordered_request_partial()
        self.storing_keys()

        served_request = []
        unserved_request = []
        num_requests = 0
        num_served_requests = 0
        weighted_served_requests = 0
        weighted_partially_served_requests = 0
        for request in self.request_key_rate_remaining_dic.keys():
            num_requests += 1
            if self.request_key_rate_remaining_dic[request[0], request[1]] > 0:
                unserved_request.append(request)
                weighted_partially_served_requests += \
                    self.request_key_rate_dic[request[0], request[1]] - self.request_key_rate_remaining_dic[request[0], request[1]]
            else:
                num_served_requests += 1
                served_request.append(request)
                weighted_served_requests += self.request_key_rate_dic[request[0], request[1]]
        print("Served request: ")
        print(served_request)
        print("Unserved request: ")
        print(unserved_request)

        # percentage of served request, weighted served request, weighted partially served request
        #cost_list = []
        cost_list = [num_served_requests/num_requests, weighted_served_requests, weighted_partially_served_requests]
        # stored keys
        key_stored_all = 0
        for node_pair in self.qkp_remaining_keys_original_dic.keys():
            key_stored_all = key_stored_all + self.qkp_remaining_keys_dic[node_pair[0], node_pair[1]] \
                             - self.qkp_remaining_keys_original_dic[node_pair[0], node_pair[1]]

        objective_vlaue = weighted_served_requests * 1000 + key_stored_all
        cost_list.append(objective_vlaue)

        key_storing_list = [key_stored_all, average_qkd_modules, average_physical_hops, average_virtual_hops]
        return cost_list, key_storing_list

    def get_information_node_auxiliary_graph(self, node):
        # quantum_node_flag = False
        # node_int = 0
        time_slot_index = -1
        if type(node) is str:
            if "from" in node:
                quantum_node_flag = False
                node_int = int(node.split("from")[0])
            else:
                quantum_node_flag = True
                node_int = int(node.split("-")[1])
                time_slot_index = int(node.split("-")[0])
        elif type(node) is int:
            quantum_node_flag = False
            node_int = node
        else:
            raise Exception("Error: the path has node that is either not a string or an int")

        return time_slot_index, quantum_node_flag, node_int

    def time_driven_auxiliary_graph_shortest_path(self, time_slot, qkp_remaining_keys_dic,
                                                  request, efficiency_first_run=False):
        """
        Function to find the shortest path in the auxiliary graph
        :param unused_channel_dic:
        :return: path_flag, path
        """
        try:
            shortest_path_nodes_list = nx.shortest_path(G=self.time_auxiliary_graph, source=request[0],
                                                        target=request[1], weight="weight")
            # shortest_path_length_tmp = nx.path_weight()
            # shortest_path_test2 = nx.path_weight(self.time_auxiliary_graph, shortest_path_nodes_list, "weight")
            # try:
            #     shortest_path_test1 = nx.path_weight(self.time_auxiliary_graph, [1, '1-1-out', '1-2-in', '1-2-out', '1-3-in', 3], "weight")
            # except Exception as e:
            #     print(e)
        except nx.NetworkXNoPath:
            # no path
            return False, -1, -1, -1, -1, -1, -1, -1
        # print(shortest_path_nodes_list)

        # get the number of QKD modules consumed
        # get the length of the path
        num_qkd_modules = 0
        num_quantum_channels = 0
        generated_key_rate = np.inf
        num_qkp_consumed_channels = 0
        num_physical_hops = 0
        num_virtual_hops = 0
        num_qkp_hops = 0

        for node_index in range(len(shortest_path_nodes_list)-1):
            node1 = shortest_path_nodes_list[node_index]
            node2 = shortest_path_nodes_list[node_index+1]
            time_slot_index1, quantum_node_flag1, node_int1 = self.get_information_node_auxiliary_graph(node1)
            time_slot_index2, quantum_node_flag2, node_int2 = self.get_information_node_auxiliary_graph(node2)
            if node_int1 != node_int2:
                if quantum_node_flag1 and quantum_node_flag2:
                    num_qkd_modules += 1
                    selected_path = self.time_auxiliary_graph.edges[node1, node2]["path"]
                    path_edges_list = self.pathEdgesDict[selected_path]
                    num_quantum_channels += len(path_edges_list)
                    if time_slot_index1 != time_slot:
                        num_virtual_hops = num_virtual_hops + 1
                    else:
                        num_physical_hops = num_physical_hops + 1
                elif not quantum_node_flag1 and not quantum_node_flag2:
                    num_quantum_channels += 0
                    path_nodes_list_tmp = nx.shortest_path(self.DG, node_int1, node_int2)
                    num_edges_tmp = len(path_nodes_list_tmp) - 1
                    num_qkp_consumed_channels += num_edges_tmp
                    num_virtual_hops = num_virtual_hops + 1
                    num_qkp_hops = num_qkp_hops + 1
                else:
                    raise Exception("Error: unexpected links between two nodes")
                if self.time_auxiliary_graph.edges[node1, node2]["keyrate"] < generated_key_rate:
                    generated_key_rate = self.time_auxiliary_graph.edges[node1, node2]["keyrate"]
            else:
                if quantum_node_flag1 and quantum_node_flag2:
                    num_qkd_modules += 1
                elif not quantum_node_flag1 and quantum_node_flag2:
                    num_qkd_modules += 1

        threshold = self.nodePairsPathThresholdNumEdgesDic[request[0], request[1]]
        # check whether the length is OK
        # if efficiency_first_run and num_quantum_channels > threshold:
        if efficiency_first_run and \
                (num_quantum_channels + num_qkp_consumed_channels > threshold or num_quantum_channels > threshold)\
                and (num_qkd_modules > threshold * 2):
            return False, -1, -1, -1, -1, -1, -1, -1
        else:
            return True, shortest_path_nodes_list, generated_key_rate, num_qkd_modules, num_quantum_channels, \
                   num_physical_hops, num_virtual_hops, num_qkp_hops

    def assign_shortest_path_auxiliary_graph(self, shortest_path_nodes_list, DG_tmp, assign_key_rate,
                                             qkp_remaining_keys_dic, channel_index):
        for node_index in range(len(shortest_path_nodes_list)-1):
            node1 = shortest_path_nodes_list[node_index]
            node2 = shortest_path_nodes_list[node_index+1]
            time_slot_index1, quantum_node_flag1, node_int1 = self.get_information_node_auxiliary_graph(node1)
            time_slot_index2, quantum_node_flag2, node_int2 = self.get_information_node_auxiliary_graph(node2)
            if node_int1 != node_int2:
                # if we consume a quantum module
                if quantum_node_flag1 and quantum_node_flag2:
                    selected_path = self.time_auxiliary_graph.edges[node1, node2]["path"]
                    path_edges_list = self.pathEdgesDict[selected_path]

                    # DG_tmp.nodes[node_int1]['qkd-modules-dic'][time_slot_index1] = \
                    #     DG_tmp.nodes[node_int1]['qkd-modules-dic'][time_slot_index1] - 1
                    DG_tmp.nodes[node_int2]['qkd-modules-dic'][time_slot_index2] = \
                        DG_tmp.nodes[node_int2]['qkd-modules-dic'][time_slot_index2] - 1
                    # self.DG.edges[edge]['channels'] = [0 for i in range(self.num_total_channels)]
                    # self.DG.edges[edge]['channels-dic'][i] = [0 for i in range(self.num_total_channels)]

                    channel_index = self.time_auxiliary_graph.edges[node1, node2]["channel_index"]
                    node_int_left = min(node_int1, node_int2)
                    node_int_right = max(node_int1, node_int2)
                    # qkp_remaining_keys_dic[node_int_left, node_int_right] += self.time_auxiliary_graph.edges[node1, node2][
                    #                                                    "keyrate"] - assign_key_rate
                    qkp_pair_storing_maximum = \
                        self.get_qkp_pair_storing_maximum([node_int_left, node_int_right], qkp_remaining_keys_dic)
                    qkp_pair_storing_achievable = qkp_remaining_keys_dic[node_int_left, node_int_right] + \
                                                  self.time_auxiliary_graph.edges[node1, node2]["keyrate"] - assign_key_rate
                    qkp_remaining_keys_dic[node_int_left, node_int_right] = \
                        min(qkp_pair_storing_maximum, qkp_pair_storing_achievable)

                    for edge in path_edges_list:
                        if DG_tmp.edges[edge]['channels-dic'][time_slot_index1][channel_index] == 1:
                            print("***************************Error in channel assignment******************")
                        else:
                            DG_tmp.edges[edge]['channels-dic'][time_slot_index1][channel_index] = 1
                # if we only use the QKP
                elif not quantum_node_flag1 and not quantum_node_flag2:
                    # qkp_remaining_keys_dic[node_int1, node_int2] = self.time_auxiliary_graph.edges[node1, node2][
                    #                                                    "keyrate"] - assign_key_rate
                    node_int_left = min(node_int1, node_int2)
                    node_int_right = max(node_int1, node_int2)
                    qkp_remaining_keys_dic[node_int_left, node_int_right] -= assign_key_rate
                    pass
                else:
                    raise Exception("Error: unexpected links between two nodes")
                # we have to update it for every node pair case
            else:
                if quantum_node_flag1 and quantum_node_flag2:
                    DG_tmp.nodes[node_int1]['qkd-modules-dic'][time_slot_index1] = \
                        DG_tmp.nodes[node_int1]['qkd-modules-dic'][time_slot_index1] - 1
                elif not quantum_node_flag1 and quantum_node_flag2:
                    DG_tmp.nodes[node_int1]['qkd-modules-dic'][time_slot_index2] = \
                        DG_tmp.nodes[node_int1]['qkd-modules-dic'][time_slot_index2] - 1

    def get_maximum_key_rate_baseline(self, request):
        maximum_key_rate_baseline = np.inf
        path_nodes_list = nx.shortest_path(self.DG, request[0], request[1], weight='length')
        for index in range(0, len(path_nodes_list)-1):
            edge = [path_nodes_list[index], path_nodes_list[index+1]]
            if self.get_key_rate_of_edge(edge) < maximum_key_rate_baseline:
                    maximum_key_rate_baseline = self.get_key_rate_of_edge(edge)
        if maximum_key_rate_baseline < np.inf:
            return maximum_key_rate_baseline
        else:
            return -1

    def serve_ordered_request(self, k=3):
        for request_index in range(len(self.ordered_request_edge_list)):
            request = self.ordered_request_edge_list[request_index]
            if self.qkp_remaining_keys_dic[request[0], request[1]] > 0:
                assign_key_rate_tmp = \
                    min(self.qkp_remaining_keys_dic[request[0], request[1]], self.request_key_rate_remaining_dic[request[0], request[1]])
                self.qkp_remaining_keys_dic[request[0], request[1]] -= assign_key_rate_tmp
                self.request_key_rate_remaining_dic[request[0], request[1]] -= assign_key_rate_tmp
        for request_index in range(len(self.ordered_request_edge_list)):
            # *****We copy the DG_tmp and qkp_remaining_keys_dic_tmp. If the key is ok, we use it***************
            # https://stackoverflow.com/questions/39555831/how-do-i-copy-but-not-deepcopy-a-networkx-graph
            DG_tmp = copy.deepcopy(self.DG)
            qkp_remaining_keys_dic_tmp = copy.deepcopy(self.qkp_remaining_keys_dic)
            unused_channel_dic_tmp = copy.deepcopy(self.unused_channel_dic)
            request = self.ordered_request_edge_list[request_index]
            request_key_rate_remaining = self.request_key_rate_remaining_dic[request[0], request[1]]
            maximum_key_rate_baseline = self.get_maximum_key_rate_baseline(request)
            if maximum_key_rate_baseline > 0:
                num_splits = math.ceil(request_key_rate_remaining / (maximum_key_rate_baseline / self.num_time_slots))
                if num_splits > 0:
                    key_rate_per_split = request_key_rate_remaining / num_splits
                else:
                    key_rate_per_split = 0
            else:
                continue

            request_physical_hops_list = []
            request_virtual_hops_list = []
            request_qkd_modules_list = []

            for channel_index in range(0, self.num_total_channels):
            # for time_slot in range(0, self.num_time_slots):
                # request_key_rate_remaining_before = self.request_key_rate_remaining_dic[request[0], request[1]]
                if request_key_rate_remaining <= 0:
                    continue

                selected_reach_index_dic = {}
                selected_generated_key_rate_dic = {}
                selected_consumed_module_dic = {}
                selected_efficiency = {}
                # if num_splits == 1:
                #     time_slot_start = self.num_time_slots - 1
                # else:
                #     time_slot_start = 0
                for time_slot in range(0, self.num_time_slots):
                # for channel_index in range(0, self.num_total_channels):
                    if request_key_rate_remaining <= 0:
                        break
                    selected_reach_index = -1
                    selected_generated_key_rate = 0
                    selected_consumed_module = np.inf
                    selected_num_paths = np.inf
                    selected_shortest_path_nodes_list = []
                    selected_num_physical_hops = 0
                    selected_num_virtual_hops = 0
                    selected_num_qkp_hops = 0
                    for reach_index in range(0, len(reaches_list)):
                        reach_key_rate = reaches_key_rate_list[reach_index]
                        # todo: check the implementation with splits
                        if reach_key_rate / self.num_time_slots < request_key_rate_remaining \
                                and reach_key_rate / self.num_time_slots < key_rate_per_split:
                            continue
                        self.initialize_time_auxiliary_graph_tr(DG_tmp=DG_tmp, start_time_slot_index=0,
                                                                end_time_slot_index=time_slot,
                                                                qkp_remaining_keys_dict=qkp_remaining_keys_dic_tmp,
                                                                reach_index=reach_index,
                                                                channel_index_selected=channel_index,
                                                                request_key_rate=min(request_key_rate_remaining,
                                                                                     key_rate_per_split),
                                                                request=request)
                        shortest_path_flag, shortest_path_nodes_list, generated_key_rate, num_qkd_modules, \
                            num_quantum_channels, num_physical_hops, num_virtual_hops, num_qkp_hops = \
                            self.time_driven_auxiliary_graph_shortest_path(time_slot=time_slot,
                                                                       qkp_remaining_keys_dic=qkp_remaining_keys_dic_tmp,
                                                                       request=request,
                                                                       efficiency_first_run=True)
                        # I want to use less QDK modules
                        if shortest_path_flag:
                            #if generated_key_rate / self.num_time_slots >= request_key_rate_remaining:
                            if generated_key_rate >= request_key_rate_remaining:
                                served_current_channel = True
                                if num_qkd_modules < selected_consumed_module:
                                    selected_consumed_module = num_qkd_modules
                                    selected_reach_index = reach_index
                                    selected_generated_key_rate = generated_key_rate
                                    selected_num_paths = 1
                                    selected_shortest_path_nodes_list = shortest_path_nodes_list
                                    selected_num_physical_hops = num_physical_hops
                                    selected_num_virtual_hops = num_virtual_hops
                                    selected_num_qkp_hops = num_qkp_hops
                            elif selected_num_paths > 1:
                                # if math.ceil(request_key_rate_remaining / (generated_key_rate / self.num_time_slots)) <= selected_num_paths:
                                if math.ceil(request_key_rate_remaining / generated_key_rate) <= selected_num_paths:
                                    if generated_key_rate >= selected_generated_key_rate and num_qkd_modules < selected_consumed_module:
                                        selected_consumed_module = num_qkd_modules
                                        selected_reach_index = reach_index
                                        selected_generated_key_rate = generated_key_rate
                                        selected_num_paths = math.ceil(request_key_rate_remaining / generated_key_rate)
                                        selected_shortest_path_nodes_list = shortest_path_nodes_list
                                        selected_num_physical_hops = num_physical_hops
                                        selected_num_virtual_hops = num_virtual_hops
                                        selected_num_qkp_hops = num_qkp_hops

                    if selected_reach_index != -1:
                        self.initialize_time_auxiliary_graph_tr(DG_tmp=DG_tmp, start_time_slot_index=0,
                                                                end_time_slot_index=time_slot,
                                                                qkp_remaining_keys_dict=qkp_remaining_keys_dic_tmp,
                                                                reach_index=selected_reach_index,
                                                                channel_index_selected=channel_index,
                                                                request_key_rate=min(request_key_rate_remaining,
                                                                                     key_rate_per_split),
                                                                request=request)
                        selected_reach_index_dic[channel_index] = selected_reach_index
                        selected_generated_key_rate_dic[channel_index] = selected_generated_key_rate
                        selected_consumed_module_dic[channel_index] = selected_consumed_module
                        selected_efficiency[channel_index] = selected_generated_key_rate / (selected_consumed_module + 0.1)
                        if selected_generated_key_rate >= request_key_rate_remaining:
                            selected_generated_key_rate = request_key_rate_remaining

                        # def assign_shortest_path_auxiliary_graph(self, shortest_path_nodes_list, DG_tmp,
                        #                                          assign_key_rate,
                        #                                          qkp_remaining_keys_dic, channel_index):
                        # todo: assign the resources for the selected path
                        self.assign_shortest_path_auxiliary_graph(shortest_path_nodes_list=selected_shortest_path_nodes_list,
                                                                  DG_tmp=DG_tmp, assign_key_rate=selected_generated_key_rate,
                                                                  qkp_remaining_keys_dic=qkp_remaining_keys_dic_tmp,
                                                                  channel_index=channel_index)

                        if selected_num_physical_hops == 0:
                            request_physical_hops_list.append(selected_num_virtual_hops-selected_num_qkp_hops)
                            request_virtual_hops_list.append(selected_num_qkp_hops)
                            request_qkd_modules_list.append(selected_consumed_module)
                        else:
                            request_physical_hops_list.append(selected_num_physical_hops)
                            request_virtual_hops_list.append(selected_num_virtual_hops)
                            request_qkd_modules_list.append(selected_consumed_module)

                        if selected_consumed_module > 0:
                            try:
                                unused_channel_dic_tmp[request[0], request[1], time_slot].remove(channel_index)
                            except Exception as e:
                                print(e)
                        request_key_rate_remaining = request_key_rate_remaining - selected_generated_key_rate

                # selected_channel_list = list(selected_reach_index_dic.keys())
                # selected_channel_generated_keys = 0
                # for selected_channel in selected_channel_list:
                #     selected_channel_generated_keys += selected_generated_key_rate_dic[selected_channel]

            assigned_key_rate_back = self.qkp_remaining_keys_original_dic[request[0], request[1]] \
                                     - self.qkp_remaining_keys_dic[request[0], request[1]]
            if request_key_rate_remaining <= 0.01:
                self.DG = DG_tmp
                self.qkp_remaining_keys_dic = qkp_remaining_keys_dic_tmp
                self.request_key_rate_remaining_dic[request[0], request[1]] = request_key_rate_remaining
                self.unused_channel_dic = unused_channel_dic_tmp
                if assigned_key_rate_back > 0:
                    request_virtual_hops_list.append(1)
                    request_physical_hops_list.append(0)
                    request_qkd_modules_list.append(0)
                self.request_physical_hops_list_dic[request[0], request[1]] = request_physical_hops_list
                self.request_virtual_hops_list_dic[request[0], request[1]] = request_virtual_hops_list
                self.request_qkd_modules_list_dic[request[0], request[1]] = request_qkd_modules_list
            else:
                self.qkp_remaining_keys_dic[request[0], request[1]] += assigned_key_rate_back
                self.request_key_rate_remaining_dic[request[0], request[1]] += assigned_key_rate_back

            served_request = []
            unserved_request = []
            for request in self.request_key_rate_remaining_dic.keys():
                if self.request_key_rate_remaining_dic[request[0], request[1]] > 0:
                    unserved_request.append(request)
                else:
                    served_request.append(request)
            # print("Served request: ")
            # print(served_request)
            # print("Unserved request: ")
            # print(unserved_request)
            # selected_channel_list = sorted(selected_channel_list, key=lambda item: selected_efficiency[item], reverse=True

    def serve_ordered_request_second_pass(self, k=3):
        for request_index in range(len(self.ordered_request_edge_list)):
            # *****We copy the DG_tmp and qkp_remaining_keys_dic_tmp. If the key is ok, we use it***************
            # https://stackoverflow.com/questions/39555831/how-do-i-copy-but-not-deepcopy-a-networkx-graph
            DG_tmp = copy.deepcopy(self.DG)
            qkp_remaining_keys_dic_tmp = copy.deepcopy(self.qkp_remaining_keys_dic)
            unused_channel_dic_tmp = copy.deepcopy(self.unused_channel_dic)
            request = self.ordered_request_edge_list[request_index]
            request_key_rate_remaining = self.request_key_rate_remaining_dic[request[0], request[1]]
            maximum_key_rate_baseline = self.get_maximum_key_rate_baseline(request)
            if request_key_rate_remaining == 0:
                continue
            if maximum_key_rate_baseline > 0:
                num_splits = math.ceil(request_key_rate_remaining / (maximum_key_rate_baseline / self.num_time_slots))
                key_rate_per_split = request_key_rate_remaining / num_splits
            else:
                continue

            request_physical_hops_list = []
            request_virtual_hops_list = []
            request_qkd_modules_list = []

            # for channel_index in range(0, self.num_total_channels):
            for channel_index in range(0, self.num_total_channels):
            # for time_slot in range(0, self.num_time_slots):
                # request_key_rate_remaining_before = self.request_key_rate_remaining_dic[request[0], request[1]]
                if request_key_rate_remaining <= 0:
                    continue

                selected_reach_index_dic = {}
                selected_generated_key_rate_dic = {}
                selected_consumed_module_dic = {}
                selected_efficiency = {}
                for time_slot in range(0, self.num_time_slots):
                # for channel_index in range(0, self.num_total_channels):
                    if request_key_rate_remaining <= 0:
                        break
                    if channel_index not in unused_channel_dic_tmp[request[0], request[1], time_slot]:
                        continue

                    selected_reach_index = -1
                    selected_generated_key_rate = 0
                    selected_consumed_module = np.inf
                    selected_num_paths = np.inf
                    selected_shortest_path_nodes_list = []
                    selected_num_physical_hops = 0
                    selected_num_virtual_hops = 0
                    selected_num_qkp_hops = 0
                    for reach_index in range(0, len(reaches_list)):
                        reach_key_rate = reaches_key_rate_list[reach_index]
                        # todo: second pass, check the implementation with splits
                        # if reach_key_rate / self.num_time_slots < request_key_rate_remaining \
                        #         and reach_key_rate < key_rate_per_split:
                        #     continue
                        self.initialize_time_auxiliary_graph_tr(DG_tmp=DG_tmp, start_time_slot_index=0,
                                                                   end_time_slot_index=time_slot,
                                                                   qkp_remaining_keys_dict=qkp_remaining_keys_dic_tmp,
                                                                   reach_index=reach_index,
                                                                   channel_index_selected=channel_index,
                                                                   request_key_rate=request_key_rate_remaining,
                                                                   request=request)
                        # todo: second pass, efficiency false
                        shortest_path_flag, shortest_path_nodes_list, generated_key_rate, num_qkd_modules,\
                            num_quantum_channels, num_physical_hops, num_virtual_hops, num_qkp_hops = \
                            self.time_driven_auxiliary_graph_shortest_path(time_slot=time_slot,
                                                                       qkp_remaining_keys_dic=qkp_remaining_keys_dic_tmp,
                                                                       request=request,
                                                                       efficiency_first_run=False)
                        # I want to use less QDK modules
                        if shortest_path_flag:
                            if generated_key_rate >= request_key_rate_remaining:
                                served_current_channel = True
                                if num_qkd_modules < selected_consumed_module:
                                    selected_consumed_module = num_qkd_modules
                                    selected_reach_index = reach_index
                                    selected_generated_key_rate = generated_key_rate
                                    selected_num_paths = 1
                                    selected_shortest_path_nodes_list = shortest_path_nodes_list
                                    selected_num_physical_hops = num_physical_hops
                                    selected_num_virtual_hops = num_virtual_hops
                                    selected_num_qkp_hops = num_qkp_hops
                            elif selected_num_paths > 1:
                                # todo: second pass
                                # if math.ceil(request_key_rate_remaining / (reach_key_rate / self.num_time_slots)) <= selected_num_paths:
                                if generated_key_rate >= selected_generated_key_rate and num_qkd_modules < selected_consumed_module:
                                    selected_consumed_module = num_qkd_modules
                                    selected_reach_index = reach_index
                                    selected_generated_key_rate = generated_key_rate
                                    selected_num_paths = math.ceil(request_key_rate_remaining / (generated_key_rate / self.num_time_slots))
                                    selected_shortest_path_nodes_list = shortest_path_nodes_list
                                    selected_num_physical_hops = num_physical_hops
                                    selected_num_virtual_hops = num_virtual_hops
                                    selected_num_qkp_hops = num_qkp_hops

                    if selected_reach_index != -1:
                        self.initialize_time_auxiliary_graph_tr(DG_tmp=DG_tmp, start_time_slot_index=0,
                                                                end_time_slot_index=time_slot,
                                                                qkp_remaining_keys_dict=qkp_remaining_keys_dic_tmp,
                                                                reach_index=selected_reach_index,
                                                                channel_index_selected=channel_index,
                                                                request_key_rate=request_key_rate_remaining,
                                                                request=request)
                        selected_reach_index_dic[channel_index] = selected_reach_index
                        selected_generated_key_rate_dic[channel_index] = selected_generated_key_rate
                        selected_consumed_module_dic[channel_index] = selected_consumed_module
                        selected_efficiency[channel_index] = selected_generated_key_rate / (selected_consumed_module + 0.1)
                        if selected_generated_key_rate >= request_key_rate_remaining:
                            selected_generated_key_rate = request_key_rate_remaining

                        # def assign_shortest_path_auxiliary_graph(self, shortest_path_nodes_list, DG_tmp,
                        #                                          assign_key_rate,
                        #                                          qkp_remaining_keys_dic, channel_index):
                        # todo: assign the resources for the selected path
                        self.assign_shortest_path_auxiliary_graph(shortest_path_nodes_list=selected_shortest_path_nodes_list,
                                                                  DG_tmp=DG_tmp, assign_key_rate=selected_generated_key_rate,
                                                                  qkp_remaining_keys_dic=qkp_remaining_keys_dic_tmp,
                                                                  channel_index=channel_index)

                        if selected_num_physical_hops == 0:
                            request_physical_hops_list.append(selected_num_virtual_hops-selected_num_qkp_hops)
                            request_virtual_hops_list.append(selected_num_qkp_hops)
                            request_qkd_modules_list.append(selected_consumed_module)
                        else:
                            request_physical_hops_list.append(selected_num_physical_hops)
                            request_virtual_hops_list.append(selected_num_virtual_hops)
                            request_qkd_modules_list.append(selected_consumed_module)

                        if selected_consumed_module > 0:
                            try:
                                unused_channel_dic_tmp[request[0], request[1], time_slot].remove(channel_index)
                            except Exception as e:
                                print(e)
                        request_key_rate_remaining = request_key_rate_remaining - selected_generated_key_rate

            if request_key_rate_remaining <= 0.01:
                self.DG = DG_tmp
                self.qkp_remaining_keys_dic = qkp_remaining_keys_dic_tmp
                self.request_key_rate_remaining_dic[request[0], request[1]] = request_key_rate_remaining
                self.unused_channel_dic = unused_channel_dic_tmp
                self.request_physical_hops_list_dic[request[0], request[1]] = request_physical_hops_list
                self.request_virtual_hops_list_dic[request[0], request[1]] = request_virtual_hops_list
                self.request_qkd_modules_list_dic[request[0], request[1]] = request_qkd_modules_list

    def storing_keys(self, k=3):
        nodes_list = list(self.DG.nodes)
        nodes_list.sort()
        node_pair_num_list = []
        for node1_index in range(0, len(nodes_list) - 1):
            for node2_index in range(node1_index + 1, len(nodes_list)):
                node1 = nodes_list[node1_index]
                node2 = nodes_list[node2_index]
                node_pair_num_list.append([node1, node2])

        ordered_node_pair_num_list = sorted(node_pair_num_list,
                                                key=lambda item: self.get_shortest_path_length(item), reverse=False)

        for request_index in range(len(ordered_node_pair_num_list)):
            request = ordered_node_pair_num_list[request_index]
            node1 = request[0]
            node2 = request[1]
            for time_slot in range(0, self.num_time_slots):
                qkp_pair_storing_maximum = self.get_qkp_pair_storing_maximum(request, self.qkp_remaining_keys_dic)
                # if self.qkp_remaining_keys_dic[node1, node2] >= self.num_max_qkp:
                if self.qkp_remaining_keys_dic[node1, node2] >= qkp_pair_storing_maximum:
                    break
                unused_channel_dic_tmp = copy.deepcopy(self.unused_channel_dic)
                for channel_index in unused_channel_dic_tmp[node1, node2, time_slot]:
                    DG_tmp = copy.deepcopy(self.DG)
                    qkp_remaining_keys_dic_tmp = copy.deepcopy(self.qkp_remaining_keys_dic)

                    for reach_index in range(0, len(reaches_list)):
                        reach_key_rate = reaches_key_rate_list[reach_index] / self.num_time_slots
                        self.initialize_time_auxiliary_graph_tr(DG_tmp=DG_tmp, start_time_slot_index=0,
                                                                   end_time_slot_index=time_slot,
                                                                   qkp_remaining_keys_dict=qkp_remaining_keys_dic_tmp,
                                                                   reach_index=reach_index,
                                                                   channel_index_selected=channel_index,
                                                                   request_key_rate=reach_key_rate, storing=True,
                                                                   request=request
                                                                )
                        # todo: second pass, efficiency false
                        shortest_path_flag, shortest_path_nodes_list, generated_key_rate, num_qkd_modules, \
                        num_quantum_channels, num_physical_hops, num_virtual_hops, num_qkp_hops = \
                            self.time_driven_auxiliary_graph_shortest_path(time_slot=time_slot,
                                                                           qkp_remaining_keys_dic=qkp_remaining_keys_dic_tmp,
                                                                           request=request,
                                                                           efficiency_first_run=False)
                        if shortest_path_flag:
                            self.assign_shortest_path_auxiliary_graph(
                                shortest_path_nodes_list=shortest_path_nodes_list,
                                DG_tmp=DG_tmp, assign_key_rate=generated_key_rate,
                                qkp_remaining_keys_dic=qkp_remaining_keys_dic_tmp,
                                channel_index=channel_index)

                            if num_qkd_modules > 0:
                                try:
                                    unused_channel_dic_tmp[request[0], request[1], time_slot].remove(channel_index)
                                except Exception as e:
                                    print(e)

                            # update keys in QKP
                            qkp_remaining_keys_dic_tmp[node1, node2] = \
                                min(qkp_remaining_keys_dic_tmp[node1, node2] + generated_key_rate, qkp_pair_storing_maximum)

                            self.DG = DG_tmp
                            self.qkp_remaining_keys_dic = qkp_remaining_keys_dic_tmp
                            break

    def storing_keys_one_pair(self, time_slot, DG_tmp:nx.DiGraph, node1, node2, channel_index, reach_index):
        pass

    def get_key_rate_of_path(self, path=None):
        if path:
            pathLength = self.pathLengthDic[path]
            for index in range(len(reaches_list)):
                if pathLength <= reaches_list[index]:
                    return reaches_key_rate_list[index]
            return 0
        else:
            return 0

    def get_key_rate_of_edge(self, edge=None):
        if edge:
            edgeLength = self.DG.edges[edge[0], edge[1]]['length']
            for index in range(len(reaches_list)):
                if edgeLength <= reaches_list[index]:
                    return reaches_key_rate_list[index]
            return 0
        else:
            return 0

    def assign_channels_between_node_pair(self, time_slot, DG_tmp:nx.DiGraph, path, channel_index_selected=None):
        pathEdges = self.pathEdgesDict[path]

        # self.DG.edges[edge]['channels'] = [0 for i in range(self.num_total_channels)]
        # self.DG.edges[edge]['channels-dic'][i] = [0 for i in range(self.num_total_channels)]
        for edge in pathEdges:
            if DG_tmp.edges[edge]['channels-dic'][time_slot][channel_index_selected] == 1:
                print("********************************Error in channel assignment")
            else:
                DG_tmp.edges[edge]['channels-dic'][time_slot][channel_index_selected] = 1

    def check_available_channels_between_node_pair_old(self, time_slot, DG_tmp:nx.DiGraph,
                                                   node_pair=None, required_reach_index=None,
                                                   channel_index_selected=None, efficiency_first_run=False):
        required_reach = reaches_list[required_reach_index]
        node_pair_path_list = self.nodePairPathListDict[node_pair[0], node_pair[1]]
        path_selected = -1
        path_selected_length = np.inf
        for path in node_pair_path_list:
            # todo: check efficiency_first_run
            # if efficiency_first_run:
            #     key_rate_path = self.get_key_rate_of_path(path)
            #     pathEdges = self.pathEdgesDict[path]
            #     efficiency_flag = True
            #     for edge in pathEdges:
            #         if self.get_key_rate_of_edge(edge) > key_rate_path:
            #             efficiency_flag = False
            #     if not efficiency_flag:
            #         continue
            if self.pathLengthDic[path] > required_reach or self.pathLengthDic[path] > path_selected_length:
                continue
            else:
                pathEdges = self.pathEdgesDict[path]

            # self.DG.edges[edge]['channels'] = [0 for i in range(self.num_total_channels)]
            # self.DG.edges[edge]['channels-dic'][i] = [0 for i in range(self.num_total_channels)]
            for channel_index in range(0, self.num_total_channels):
                if channel_index != channel_index_selected:
                    continue
                channel_available_flag = True
                for edge in pathEdges:
                    if DG_tmp.edges[edge]['channels-dic'][time_slot][channel_index] > 0:
                        channel_available_flag = False
                        break
                if channel_available_flag:
                    path_selected = path
                    path_selected_length = self.pathLengthDic[path]

        if path_selected < 0 or self.pathLengthDic[path_selected] > required_reach:
            return False, -1
        else:
            return True, path_selected

    def check_available_channels_between_node_pair(self, time_slot, DG_tmp:nx.DiGraph,
                                                   node_pair=None, required_reach_index=None,
                                                   channel_index_selected=None, efficiency_first_run=False):
        # required_reach = reaches_list[required_reach_index]
        node_pair_path_list = self.nodePairPathListDict[node_pair[0], node_pair[1]]
        path_selected = -1
        path_selected_length = np.inf
        for path in node_pair_path_list:
            pathEdges = self.pathEdgesDict[path]
            if len(pathEdges) > 1:
                continue

            # self.DG.edges[edge]['channels'] = [0 for i in range(self.num_total_channels)]
            # self.DG.edges[edge]['channels-dic'][i] = [0 for i in range(self.num_total_channels)]
            for channel_index in range(0, self.num_total_channels):
                if channel_index != channel_index_selected:
                    continue
                channel_available_flag = True
                for edge in pathEdges:
                    if DG_tmp.edges[edge]['channels-dic'][time_slot][channel_index] > 0:
                        channel_available_flag = False
                        break
                if channel_available_flag:
                    path_selected = path
            if path_selected != -1:
                break

        if path_selected < 0:
            return False, -1
        else:
            return True, path_selected


def german():
    # todo: make sure whether to load or generate
    arr_cost = []
    arr_energy = []
    key_rate_list = [100, 200, 300, 400, 500, 600]
    # data_rate_perc_list = [[0.20, 0.25, 0.25, 0.20, 0.05, 0.05],
    #                        [0.05, 0.20, 0.25, 0.25, 0.20, 0.05],
    #                        [0.05, 0.05, 0.20, 0.25, 0.25, 0.20]]
    # data_rate_perc_list = [[0.4, 0.4, 0.05, 0.05, 0.05, 0.05],
    #                        [0.05, 0.05, 0.4, 0.4, 0.05, 0.05],
    #                        [0.05, 0.05, 0.05, 0.05, 0.4, 0.4]]
    data_rate_perc_list = [[0.15, 0.25, 0.25, 0.15, 0.10, 0.10],
                           [0.10, 0.15, 0.25, 0.25, 0.15, 0.10],
                           [0.10, 0.10, 0.15, 0.25, 0.25, 0.15]]
    cases = ['rate1', 'rate2', 'rate3']
    length_factor = 1
    for case_index in range(len(cases)):
        for i in range(10):
            request_file_name = "requests/requests_german_percent_100_" + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".pkl"
            results_file = "results/" + "results_german_opaque" + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".txt"
            rwta = NetworkEnvironment(topology="german", num_total_channels=200, request_file_name=request_file_name,
                                      load_request_flag=True, request_percentage=1, results_file=results_file,
                                      key_rate_list=key_rate_list, key_rate_perc_list=data_rate_perc_list[case_index],
                                      length_factor=length_factor)
            cost_list, energy_list = rwta.process_request()

            arr_cost.append(cost_list)
            arr_energy.append(energy_list)


        np_arr_cost = np.array(arr_cost)
        np_arr_cost = np.mean(np_arr_cost, axis=0)
        np_arr_energy = np.array(arr_energy)
        np_arr_energy = np.mean(np_arr_energy, axis=0)
        with open("results/results_german_averaged_" + cases[case_index] + "_" + str(length_factor) + ".txt", "a") as f:
            for cost in np_arr_cost:
                f.write(str(cost))
                f.write(" ")
            f.write("\n")
            for energy in np_arr_energy:
                f.write(str(energy))
                f.write(" ")
            f.write("\n")


if __name__ == "__main__":
    german()