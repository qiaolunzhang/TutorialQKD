# importing element tree
# under the alias of ET
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
from convertN2PAmpl3 import *
import numpy as np

# the first setting is for ZR, the other setting is for ZR+
modulation_setting_list = [1, 2, 3, 4, 5]
modulation_dataRate_list = [400, 400, 300, 200, 100]
modulation_spacing_list = [4, 3, 3, 3, 2]
modulation_length_list = [120, 600, 1800, 3000, 3000]
#modulation_length_list = [120, 600, 1800, 3000, 3000]

class RwtaTransparent:
    def __init__(self, topology="", num_total_slots=100, request_file_name="requests/requests.pkl", load_request_flag=False,
                 request_percentage=1.0, results_file="results/results.txt", data_rate_list=[], data_rate_perc_list=[],
                 length_factor=1):
        #self.Pip = 0.022
        #self.Ptr = 20.8
        self.PtrZr = 1
        self.PtrZrPlus = 1.3
        self.PRouter_fixed = 50
        self.PRouter_var_400G = 4
        self.POXC_shelf = 20
        # self.POXC_per_link = 1.4
        self.PAdb_ports = 3.5
        self.adb_module_ports = 16
        self.PIRoadm = 4.1
        # used for the opaque case, one AWG, two OA per direction
        self.POA = 1.7
        self.PAWG = 0.3
        self.PMonitong_opaque_node = 0.2
        self.PMonitong_transparent_node = 1.5
        #self.Pro = 100

        #self.Cip = 53
        self.CtrZr = 1
        self.CtrZrPlus = 2
        #self.Cro = 10

        self.DG = None
        self.num_total_slots = num_total_slots
        self.DG = None
        self.nodePairsList = []
        # Ep_u
        self.edge_ug_list = []
        self.load_topology(dataFileName='Net2PlanTopology/example7nodes.n2p', num_total_slots=self.num_total_slots,
                           topology=topology, length_factor=length_factor)

        # the subpath without regeneration for a node pair: (node i, node j): [list of subpaths]
        self.noRegSubpathDict = {}
        # the subpath without regeneration for a node pair: (node i, node j): [list of subpaths]
        self.regSubpathDict = {}
        # path edge dict: path: [(edge), (edge)]
        self.pathEdgesDict = {}
        # path nodes dict: path: [node, node]
        self.pathNodesDict = {}
        self.pathModulationsIndexDict = {}
        self.numPath = 0
        # number of segments in a path: path: [1, 2, 3, 4]
        self.pathNumSegmentsDict = {}
        self.generateAllPaths(k=2)

        # assigned path for requests: [(p, [[c, dataRate], [c, dataRate]), []]
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
        self.DG_compute = self.DG.copy()

        self.request_edge_list_num = []
        self.request_percentage = request_percentage
        self.get_request(request_file_name=request_file_name, load_flag=load_request_flag)

        self.request_bitrate_list = {}
        self.assign_request_bitrate(bitrate=400, multiBitrateFlag=True, unidirectionalFlag=False,
                                    request_file_name=request_file_name,
                                    load_flag=load_request_flag,
                                    data_rate_list=data_rate_list, data_rate_perc_list=data_rate_perc_list)

        self.requestLightpathIndexListDict = {}
        for request in self.request_edge_list_num:
            self.requestLightpathIndexListDict[request[0], request[1]] = []

        self.energy_consumption_total = 0
        self.num_ip_ports = 0
        self.num_zrPlus_transponders = 0
        self.num_zr_transponders = 0
        # what about the first node
        self.num_node_ip_port_dict = {}
        self.num_node_ip_traffic_dict = {}

        self.results_file = results_file

        self.add_drop_block_port_dict = {}
        self.router_traffic_dict = {}
        for node in self.DG.nodes:
            node = int(node)
            self.add_drop_block_port_dict[node] = 0
            self.router_traffic_dict[node] = 0

        # for key in self.request_bitrate_list.keys():
        #    self.request_bitrate_list[key] = 500

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
        for index in range(len(edge_list)):
            edge = edge_list[index]
            length = length_list[index]
            DG.add_edge(edge[0], edge[1], weight=length)
            DG.add_edge(edge[1], edge[0], weight=length)

        return DG


    def load_topology(self, dataFileName='Net2PlanTopology/example7nodes.n2p', num_total_slots=30, topology="", length_factor=1):
        net2PlanDataFile=dataFileName
        self.DG = getNxGraph(net2PlanDataFile)
        if topology == "japan":
            self.DG = self.get_japan_topology()
        elif topology == "german":
            self.DG = self.get_german_topology()
        else:
            UG = self.DG.to_undirected()
            print(UG.nodes)
            print(UG.edges)

            nodes_list = list(self.DG.nodes)
            edge_dg_list = list(self.DG.edges)
            edge_ug_list = list(UG.edges)
            self.edge_ug_list = edge_ug_list

        for edge in self.DG.edges:
            if self.DG.edges[edge]['weight'] * length_factor <= 600:
                self.DG.edges[edge]['weight'] = length_factor * self.DG.edges[edge]['weight']
            else:
                self.DG.edges[edge]['weight'] = 600

        for edge in self.DG.edges:
            # self.DG.edges[edge[0], edge[1]]['slots'] = list(range(30))
            self.DG.edges[edge]['slots'] = [0 for i in range(num_total_slots)]
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
            # print(self.DG.edges[1,3]['slots'])

        nodes_list = list(self.DG.nodes)
        for i in range(len(nodes_list)):
            for j in range(i+1, len(nodes_list)):
                self.nodePairsList.append((nodes_list[i], nodes_list[j]))
                self.nodePairsList.append((nodes_list[j], nodes_list[i]))

    def generateAllPaths(self, k=2):
        for nodePair in self.nodePairsList:
            # generate k shortest paths
            X = nx.shortest_simple_paths(self.DG, nodePair[0], nodePair[1])
            shortestKPaths = []
            for counter, path in enumerate(X):
                #print(path)
                shortestKPaths.append(path)
                if counter == k - 1:
                    break
            self.generateRegenerationSubpath(shortestKpaths=shortestKPaths, nodePair=nodePair)

    def generateRegenerationSubpath(self, shortestKpaths:list, nodePair):
        coveredModulationFormats = set()
        noRegSubpathList = []
        regSubpathList = []
        for shortestPath in shortestKpaths:
            lengthPath = path_weight(self.DG, shortestPath, 'length')
            pathModulationsIndexList = []
            for i in range(len(modulation_setting_list)):
                if modulation_length_list[i] >= lengthPath:
                    coveredModulationFormats.add(modulation_setting_list[i])
                    #pathModulationsIndexList.append(modulation_setting_list[i])
                    pathModulationsIndexList.append(i)
            self.numPath = self.numPath + 1

            noRegSubpathList.append(self.numPath)
            self.pathModulationsIndexDict[self.numPath] = pathModulationsIndexList
            self.pathNodesDict[self.numPath] = shortestPath
            # the edges of the path
            edges_list = []
            for index in range(0, len(shortestPath)-1):
                edges_list.append((shortestPath[index], shortestPath[index+1]))
            self.pathEdgesDict[self.numPath] = edges_list
            self.pathNumSegmentsDict[self.numPath] = 1

        if len(noRegSubpathList) > 0:
            self.noRegSubpathDict[nodePair[0], nodePair[1]] = noRegSubpathList

        # todo: move loop of modulation setting to outside, move shortestKpaths inside

        for index in range(len(modulation_setting_list)-1, -1, -1):
            modulationAddedFlag = False
            modulationToCheckFlag = False
            if modulation_setting_list[index] not in coveredModulationFormats:
                all_num_subseg_length_list = []
                for shortestPath in shortestKpaths:
                    num_subseg_length_list = []
                    modulationAddedFlag = True
                    modulation_length = modulation_length_list[index]
                    current_length = 0
                    for current_node_index in range(0, len(shortestPath)-1):
                        length_edge = self.DG.edges[shortestPath[current_node_index], shortestPath[current_node_index+1]]['length']
                        if current_length + length_edge <= modulation_length:
                            current_length = current_length + length_edge
                        else:
                            num_subseg_length_list.append(current_length)
                            current_length = length_edge
                    num_subseg_length_list.append(current_length)
                    all_num_subseg_length_list.append(num_subseg_length_list)
            else:
                continue

            selected_num_subseg_length_list = []
            selected_shortest_k_paths = []
            min_segment = len(all_num_subseg_length_list[0])
            for num_subseg_length_list in all_num_subseg_length_list:
                if len(num_subseg_length_list) < min_segment:
                    min_segment = len(num_subseg_length_list)
            for index in range(len(all_num_subseg_length_list)):
                if len(all_num_subseg_length_list[index]) == min_segment:
                    selected_num_subseg_length_list.append(all_num_subseg_length_list[index])
                    selected_shortest_k_paths.append(shortestKpaths[index])

            selectedPathModulationsIndexList = []
            for num_subseg_length_list in selected_num_subseg_length_list:
                pathModulationsIndexList = []
                for i in range(len(modulation_setting_list)):
                    if modulation_length_list[i] >= max(num_subseg_length_list):
                        # pathModulationsIndexList.append(modulation_setting_list[i])
                        pathModulationsIndexList.append(i)
                selectedPathModulationsIndexList.append(pathModulationsIndexList)
            max_num_modulation = len(selectedPathModulationsIndexList[0])
            for pathModulationsIndexList in selectedPathModulationsIndexList:
                if len(pathModulationsIndexList) > max_num_modulation:
                    max_num_modulation = len(pathModulationsIndexList)
            for index in range(len(selectedPathModulationsIndexList)):
                if len(selectedPathModulationsIndexList[index]) == max_num_modulation:
                    num_subseg_length_list = selected_num_subseg_length_list[index]
                    shortestPath = selected_shortest_k_paths[index]
                    break

            # update the covered modulation with the regeneration path
            pathModulationsIndexList = []
            for i in range(len(modulation_setting_list)):
                if modulation_length_list[i] >= max(num_subseg_length_list):
                    coveredModulationFormats.add(modulation_setting_list[i])
                    #pathModulationsIndexList.append(modulation_setting_list[i])
                    pathModulationsIndexList.append(i)
            self.numPath = self.numPath + 1

            self.pathNumSegmentsDict[self.numPath] = len(num_subseg_length_list)
            self.pathModulationsIndexDict[self.numPath] = pathModulationsIndexList
            regSubpathList.append(self.numPath)
            self.pathNodesDict[self.numPath] = shortestPath
            # the edges of the path
            edges_list = []
            for index in range(0, len(shortestPath) - 1):
                edges_list.append((shortestPath[index], shortestPath[index + 1]))
            self.pathEdgesDict[self.numPath] = edges_list

        if len(regSubpathList) > 0:
            self.regSubpathDict[nodePair[0], nodePair[1]] = regSubpathList
        else:
            self.regSubpathDict[nodePair[0], nodePair[1]] = []

    def get_request(self, request_file_name="requests/requests.pkl", load_flag=False):
        # todo: add the path number related to auxiliary link
        # todo: add the links related to path to the attributes of graph
        if load_flag:
            request_file = open(request_file_name, "rb")
            request_bitrate_list = pickle.load(request_file)
            self.request_edge_list_num = []
            for request in request_bitrate_list.keys():
                self.request_edge_list_num.append([request[0], request[1]])
            return

        nodes_list, edge_ug_list, edge_dg_list, length_list = getNodesEdgeLength(self.DG)
        num_physical_nodes = len(nodes_list)

        all_edges_list_num = []
        for i in range(1, num_physical_nodes):
            for j in range(i + 1, num_physical_nodes + 1):
                # print(str(i) + " " + str(j))
                # todo: bidirectional request
                all_edges_list_num.append([i, j])
                all_edges_list_num.append([j, i])
        # sorted_sample = [
        #     mylist[i] for i in sorted(random.sample(range(len(mylist)), sample_size))
        # ]
        if self.request_percentage < 1:
            sample_size = int(self.request_percentage * len(all_edges_list_num))
            self.request_edge_list_num = [
                all_edges_list_num[i] for i in sorted(random.sample(range(len(all_edges_list_num)), sample_size))
            ]
        else:
            self.request_edge_list_num = all_edges_list_num

        # todo: check small number of request
        # self.request_edge_list_num = [[2,4], [3,4]]
        # self.request_edge_list_num = [[2,4]]
        #print(self.request_edge_list_num)

    def assign_request_bitrate(self, bitrate=400, multiBitrateFlag=False, unidirectionalFlag=True,
                               request_file_name="requests/requests.pkl", load_flag=False,
                               data_rate_list=[], data_rate_perc_list=[]):
        if load_flag:
            request_file = open(request_file_name, "rb")
            self.request_bitrate_list = pickle.load(request_file)
            return

        if unidirectionalFlag:
            for i in range(0, len(self.request_edge_list_num), 2):
                if multiBitrateFlag:
                    bitrate = random.choice([100, 200, 300, 400])
                nodePair = self.request_edge_list_num[i]
                self.request_bitrate_list[nodePair[0], nodePair[1]] = bitrate
                self.request_bitrate_list[nodePair[1], nodePair[0]] = bitrate
        else:
            for i in range(len(self.request_edge_list_num)):
                if multiBitrateFlag:
                    bitrate = random.choice([100, 200, 300, 400])
                nodePair = self.request_edge_list_num[i]
                self.request_bitrate_list[nodePair[0], nodePair[1]] = bitrate

        if len(data_rate_list) > 0:
            request_index_list = [i for i in range(len(self.request_edge_list_num))]
            random.shuffle(request_index_list)
            data_rate_num_list = [int(perc * len(request_index_list)) for perc in data_rate_perc_list]
            data_rate_num_list[-1] = len(request_index_list) - sum(data_rate_num_list[0:-1])
            for i in range(len(data_rate_num_list)):
                start_index = 0
                start_index += sum(data_rate_num_list[0:i])
                end_index = sum(data_rate_num_list[0:i+1])
                for j in range(start_index, end_index):
                    nodePair = self.request_edge_list_num[request_index_list[j]]
                    self.request_bitrate_list[nodePair[0], nodePair[1]] = data_rate_list[i]

        # set the required bit rate
        request_file = open(request_file_name, "wb")
        pickle.dump(self.request_bitrate_list, request_file)
        request_file.close()

    def process_request(self):
        # the following class can add the same link twice, duplicate edges are replicated
        # G = nx.MultiGraph()
        self.ordered_request_edge_list = []
        len_path = 2
        while (len(self.ordered_request_edge_list) < len(self.request_edge_list_num)):
            for i in range(len(self.request_edge_list_num)):
                request = self.request_edge_list_num[i]
                path_request = self.noRegSubpathDict[request[0], request[1]][0]
                nodes_path_request = self.pathNodesDict[path_request]
                if len(nodes_path_request) == len_path:
                    self.ordered_request_edge_list.append(request)
            len_path += 1

        # serve the request in the self.ordered_request_edge_list
        self.serve_ordered_request()

        # todo: maybe I can add some post processing process to here
        # for request_index in range(len(self.request_edge_list_num)):
        #     # find the auxiliary link that can be added
        #     request = self.request_edge_list_num[request_index]
        #     request_bitrate = self.request_bitrate_list[request[0], request[1]]
        #     self.construct_auxiliary_graph(request_bitrate=request_bitrate)
        #
        #     try:
        #         if self.DG.edges[1,3]['availabeBitRateList'] == None:
        #             print("error")
        #         #if request == [2,5]:
        #         #    print("find problem")
        #     except Exception as e:
        #         print(e)

            # #check whether number of paths is correct
            # for edge in self.DG.edges:
            #     if len(self.DG.edges[edge]['pathList']) != len(self.DG.edges[edge]['pathEdges']):
            #         print("Issue")
        cost_zr = self.num_zr_transponders * self.CtrZr
        cost_zrPlus = self.num_zrPlus_transponders * self.CtrZrPlus
        cost_transponder = cost_zr + cost_zrPlus

        energy_zr = self.num_zr_transponders * self.PtrZr
        energy_zrPlus = self.num_zrPlus_transponders * self.PtrZrPlus
        energy_router = 0
        energy_router_chassis = 0
        energy_router_modulo_mda = 0
        energy_oxc = 0
        energy_oxc_shelf = 0
        energy_oxc_awg_oa = 0
        energy_oxc_add_drop_block = 0
        energy_monitoring = 0
        self.energy_consumption_total = 0

        for node in self.DG.nodes:
            node = int(node)
            energy_router_current = self.PRouter_fixed
            energy_router_chassis += self.PRouter_fixed

            energy_router_current += self.PRouter_var_400G * math.ceil(self.router_traffic_dict[node] / 400)
            energy_router_modulo_mda += self.PRouter_var_400G * math.ceil(self.router_traffic_dict[node] / 400)

            energy_router += energy_router_current

            # todo: maybe remove this one also for transparent case
            # the degree here actually take into account two direction  because it's a directional graph
            energy_oxc_current = self.POXC_shelf * math.ceil(self.DG.degree[node] / 8)
            energy_oxc_shelf += self.POXC_shelf * math.ceil(self.DG.degree[node] / 8)

            # todo: uncomment it for transparent case
            #energy_oxc_current += self.PAdb_ports * math.ceil(self.add_drop_block_port_dict[node] / self.adb_module_ports)
            # energy_oxc_add_drop_block += self.PAdb_ports * math.ceil(self.add_drop_block_port_dict[node] / self.adb_module_ports)
            # consumption of irdmx
            energy_oxc_current += (self.POA * 2 + self.PAWG) * (self.DG.degree[node] // 2)
            energy_oxc_awg_oa += (self.POA * 2 + self.PAWG) * (self.DG.degree[node] // 2)

            energy_oxc += energy_oxc_current

            # todo: change for transparent case
            energy_monitoring += self.PMonitong_opaque_node * (self.DG.degree[node] // 2)
        self.energy_consumption_total = energy_zr + energy_zrPlus + energy_router + energy_oxc + energy_monitoring

        print("Num of ZR transponders is: " + str(self.num_zr_transponders))
        print("Num of ZR+ transponders is: " + str(self.num_zrPlus_transponders))
        print("Num of ports of IP router is: " + str(self.num_ip_ports))
        print("Cost of transponders is : " + str(cost_transponder))
        print("*******************************************************")
        print("Energy consumption of ZR transponders is: " + str(energy_zr))
        print("Energy consumption of ZR+ transponders is: " + str(energy_zrPlus))
        print("Energy consumption of transponders is: " + str(energy_zr + energy_zrPlus))
        print("Energy consumption of routers is: " + str(energy_router))
        print("Energy consumption of OXC is: " + str(energy_oxc))
        print("Energy consumption of monitoring is: " + str(energy_monitoring))
        print("Total energy consumption is: " + str(self.energy_consumption_total))
        with open(self.results_file, "a") as f:
            f.write("Cost: Number of ZR transponders, Number of ZR+ transponders, Number of router ports, Cost of transponders\n")
            f.write(str(self.num_zr_transponders) + "," + str(self.num_zrPlus_transponders) + ","
                    + str(self.num_ip_ports) + "," + str(cost_transponder) + "\n")
            f.write("Energy consumption: ZR Transponders, ZR+ transponders, IP routers chasis, IP router modulo MDA, IP routers, OXC, Monitoring, Total\n")
            f.write(str(energy_zr) + "," + str(energy_zrPlus) + ","
                    + str(energy_router_chassis) + "," + str(energy_router_modulo_mda) + "," + str(energy_router)
                    + "," + str(energy_oxc_shelf) + "," + str(energy_oxc_awg_oa) + "," + str(energy_oxc_add_drop_block)
                    + "," + str(energy_monitoring) + "\n")
        cost_list = [self.num_zr_transponders, self.num_zrPlus_transponders, self.num_ip_ports, cost_transponder]
        energy_list = [energy_zr, energy_zrPlus,
                       energy_router_chassis, energy_router_modulo_mda, energy_router,
                       energy_oxc_shelf, energy_oxc_awg_oa, energy_oxc_add_drop_block, energy_oxc,
                       energy_monitoring, self.energy_consumption_total]
        return cost_list, energy_list


    def serve_ordered_request(self):
        for request_index in range(len(self.ordered_request_edge_list)):
            # find the auxiliary link that can be added
            request = self.request_edge_list_num[request_index]
            request_bitrate = self.request_bitrate_list[request[0], request[1]]
            self.construct_auxiliary_graph(request_bitrate=request_bitrate)
            noRegSubpathList = self.noRegSubpathDict[request[0], request[1]]
            pathWeight = -1
            selectedPath = -1
            for path in noRegSubpathList:
                pathNodesList = self.pathNodesDict[path]
                tmpPathWeight = path_weight(self.DG_compute, pathNodesList, "weight")
                if pathWeight == -1:
                    pathWeight = tmpPathWeight
                    selectedPath = path
                elif tmpPathWeight < pathWeight:
                    pathWeight = tmpPathWeight
                    selectedPath = path

            if pathWeight >= 100:
                print("##################Error: no spectrum####################")

            num_splits = math.ceil(request_bitrate / 400)
            request_bitrate_remaining = request_bitrate
            for split_index in range(num_splits):
                if split_index == num_splits - 1:
                    request_bitrate = request_bitrate_remaining - (num_splits - 1) * 400
                else:
                    request_bitrate = 400

                self.construct_auxiliary_graph(request_bitrate=request_bitrate)

                pathOfRequestsList = []
                num = 1
                self.requestLightpathIndexListDict[request[0], request[1]].append(split_index)

                edge_index = 0
                for edge in self.pathEdgesDict[selectedPath]:
                    if self.DG_compute.edges[edge[0], edge[1]]['auxiliary']:
                        edge_path = self.DG_compute.edges[edge[0], edge[1]]['selectedPath']
                        pathOfRequestEdge = self.assign_remaining_datarate(request, request_bitrate, edge, edge_path, split_index=split_index)
                        pathOfRequestsList.append((edge_path, pathOfRequestEdge))
                    else:
                        # todo: recheck the number of ip ports
                        #if num == 1:
                        #    self.num_ip_ports += 1
                        #else:
                        self.num_ip_ports += 2
                        self.add_drop_block_port_dict[edge[0]] += 1
                        self.add_drop_block_port_dict[edge[1]] += 1

                        pathOfRequestEdge = self.assign_available_slots_physical_link(request, request_bitrate, edge, split_index=split_index)
                        pathOfRequestsList.append(pathOfRequestEdge)
                    if edge_index == len(self.pathEdgesDict[selectedPath]) - 1:
                        self.router_traffic_dict[edge[0]] += request_bitrate
                        self.router_traffic_dict[edge[1]] += request_bitrate
                    else:
                        self.router_traffic_dict[edge[0]] += request_bitrate
                    edge_index = edge_index + 1
                    num = num + 1
                self.pathOfRequestsDict[request[0], request[1], split_index] = pathOfRequestsList
                # # assigned path for requests: [(p, [[c, dataRate], [c, dataRate]]), []]
                # self.pathOfRequestsDict = {}

    def check_remaining_datarate_physical_link(self, path=None, request_bitrate=None):
        pathRemainingCapacity = 0
        numChannels = self.pathNumChannelsDict[path]
        if numChannels == 0:
            return False, -1
        else:
            for channel in range(1, numChannels+1):
                pathRemainingCapacity += self.remainingDataRateDict[path, channel]
        if pathRemainingCapacity >= request_bitrate:
            return True, path
        else:
            return False, -1

    def check_available_slots_physical_link(self, edge=None, path=None, request_bitrate=None, num_split_assign=None):
        # todo: modify for long haul transponders
        # todo: modify for transparent
        frequency_slots_list = self.DG.edges[edge]['slots']
        length_link = self.DG.edges[edge]['length']
        modulationIndexList = self.pathModulationsIndexDict[path]
        for i in range(len(modulationIndexList)):
            if modulation_dataRate_list[i] >= request_bitrate:
                required_spacing = modulation_spacing_list[i] * num_split_assign
                for start_slot in range(0, self.num_total_slots - required_spacing):
                    if sum(frequency_slots_list[start_slot:start_slot+required_spacing]) == 0:
                        return True
        return False

    def construct_auxiliary_graph(self, request_bitrate):
        # clear all the nodes in DG_compute
        self.DG_compute.clear()
        # Construct the auxiliary graph
        for edge in self.DG.edges:
            noRegSubpathList = self.noRegSubpathDict[edge[0], edge[1]]
            noRegSubpathWeightList = []
            selected_path = -1
            selected_pathWeight = -1

            for path in noRegSubpathList:
                pathWeight = 0
                request_bitrate_remainder = request_bitrate % 400
                remainingFlag, groomingPath = \
                    self.check_remaining_datarate_physical_link(path=path, request_bitrate=request_bitrate_remainder)

                num_split_assign = request_bitrate // 400
                available_slots_flag = False
                if remainingFlag and request_bitrate < 400:
                    selected_path = path
                    self.DG_compute.add_edge(edge[0], edge[1], weight=0)
                    self.DG_compute.edges[edge]['auxiliary'] = True
                    self.DG_compute.edges[edge]['selectedPath'] = groomingPath
                    break
                elif remainingFlag and request_bitrate >= 400:
                    available_slots_flag = self.check_available_slots_physical_link(path=path, edge=edge, request_bitrate=400, num_split_assign=num_split_assign)
                    pathWeight = num_split_assign
                elif remainingFlag == False and request_bitrate < 400:
                    available_slots_flag = self.check_available_slots_physical_link(path=path, edge=edge, request_bitrate=request_bitrate, num_split_assign=1)
                    pathWeight = 1
                elif remainingFlag == False and request_bitrate >= 400:
                    available_slots_flag = self.check_available_slots_physical_link(path=path, edge=edge, request_bitrate=400, num_split_assign=num_split_assign+1)
                    pathWeight = num_split_assign + 1

                if available_slots_flag:
                    self.DG_compute.add_edge(edge[0], edge[1], weight=pathWeight)
                    self.DG_compute.edges[edge]['auxiliary'] = False
                    self.DG_compute.edges[edge]['selectedPath'] = path
                # This is the case where it is impossible
                else:
                    self.DG_compute.add_edge(edge[0], edge[1], weight=100)
                    self.DG_compute.edges[edge]['auxiliary'] = False

                # todo: for the opaque case, only need to check the first path
                break


    def assign_remaining_datarate(self, request, request_bitrate, edge, edge_path, split_index):
        numChannels = self.pathNumChannelsDict[edge_path]
        pathOfRequest = []
        print("*********************Grooming***************************")
        for channel in range(1, numChannels + 1):
            remainingDataRateChannel = self.remainingDataRateDict[edge_path, channel]
            if remainingDataRateChannel >= request_bitrate:
                pathOfRequest.append([channel, request_bitrate])
                self.remainingDataRateDict[edge_path, channel] -= request_bitrate
                self.subpathAssignedRequestsDict[edge_path, channel].append([request, split_index])
                break
            else:
                pathOfRequest.append([channel, remainingDataRateChannel])
                self.remainingDataRateDict[edge_path, channel] = 0
                self.subpathAssignedRequestsDict[edge_path, channel].append([request, split_index])
                request_bitrate = request_bitrate - remainingDataRateChannel
        return pathOfRequest
        # # number of channels: no need to update the channels
        # # self.pathNumChannelsDict = {}
        # # assigned requests: (subpath, channel): [list of requests]
        # self.subpathAssignedRequestsDict = {}
        # # remaining data rate dict: (subpath, channel): available data rate
        # self.remainingDataRateDict = {}

    def assign_available_slots_physical_link(self, request, request_bitrate, edge, split_index):
        # todo: modify for long haul transponders
        frequency_slots_list = self.DG.edges[edge]['slots']
        length_link = self.DG.edges[edge]['length']

        # todo: modify for transparent
        edge_path = self.noRegSubpathDict[edge][0]
        assigned_slots = []

        # if length_link <= 80:
        #     # assign the frequency slots
        #     # todo: change the channel spacing for ZR
        #     for start_slot in range(0, self.num_total_slots-3):
        #         if sum(frequency_slots_list[start_slot:start_slot+3]) == 0:
        #             self.DG.edges[edge]['slots'][start_slot] = 1
        #             self.DG.edges[edge]['slots'][start_slot + 1] = 1
        #             self.DG.edges[edge]['slots'][start_slot + 2] = 1
        #             assigned_slots.extend([start_slot, start_slot+1, start_slot+2])
        #             break
        #     assigned_modulation_index = -1
        #     available_bitrate = 400 - request_bitrate
        #     self.num_zr_transponders = self.num_zr_transponders + 2
        # else:
        selected_modulationIndex = -1
        available_bitrate = -1
        for i in range(len(self.pathModulationsIndexDict[edge_path])):
            if modulation_dataRate_list[i] >= request_bitrate:
                if selected_modulationIndex == -1:
                    selected_modulationIndex = self.pathModulationsIndexDict[edge_path][i]
                    available_bitrate = modulation_dataRate_list[i]
                elif modulation_dataRate_list[i] > available_bitrate:
                    selected_modulationIndex = self.pathModulationsIndexDict[edge_path][i]
                    available_bitrate = modulation_dataRate_list[i]

        selected_spacing = modulation_spacing_list[selected_modulationIndex]

        for start_slot in range(0, self.num_total_slots-selected_spacing):
            if sum(frequency_slots_list[start_slot:start_slot+selected_spacing]) == 0:
                for i in range(selected_spacing):
                    self.DG.edges[edge]['slots'][start_slot+i] = 1
                    assigned_slots.append(start_slot+i)
                break
        available_bitrate = available_bitrate - request_bitrate
        if selected_modulationIndex == 0:
            self.num_zr_transponders = self.num_zr_transponders + 2
        else:
            self.num_zrPlus_transponders = self.num_zrPlus_transponders + 2

        numChannels = self.pathNumChannelsDict[edge_path]
        numChannels += 1
        self.pathNumChannelsDict[edge_path] = numChannels

        self.remainingDataRateDict[edge_path, numChannels] = available_bitrate
        self.subpathAssignedRequestsDict[edge_path, numChannels] = [[request, split_index]]
        self.subpathAssignedSlotsDict[edge_path, numChannels] = assigned_slots
        # # assigned path for requests: [(p, [[c, dataRate], [c, dataRate]]), []]
        return (edge_path, [[numChannels, request_bitrate]])

def seven_node():
    arr_cost = []
    arr_energy = []
    for i in range(10):
        request_file_name = "requests/requests_seven_percent_100_" + str(i) + ".pkl"
        rwta = RwtaTransparent(topology="", num_total_slots=30, request_file_name=request_file_name,
                               load_request_flag=True, request_percentage=1, results_file="results/results_seven_opaque.txt")
        cost_list, energy_list = rwta.process_request()
        arr_cost.append(cost_list)
        arr_energy.append(energy_list)
    np_arr_cost = np.array(arr_cost)
    np_arr_cost = np.mean(np_arr_cost, axis=0)
    np_arr_energy = np.array(arr_energy)
    np_arr_energy = np.mean(np_arr_energy, axis=0)
    with open("results/results_averaged_seven.txt", "a") as f:
        for cost in np_arr_cost:
            f.write(str(cost))
            f.write(" ")
        f.write("\n")
        for energy in np_arr_energy:
            f.write(str(energy))
            f.write(" ")
        f.write("\n")


def japan():
    arr_cost = []
    arr_energy = []
    data_rate_list = [100, 200, 300, 400, 500, 600]
    data_rate_perc_list = [0.05, 0.05, 0.2, 0.2, 0.3, 0.2]
    for i in range(10):
        request_file_name = "requests/requests_japan_percent_100_" + str(i) + ".pkl"
        rwta = RwtaTransparent(topology="japan", num_total_slots=100, request_file_name=request_file_name,
                               load_request_flag=True, request_percentage=1, results_file="results/results_opaque.txt",
                               data_rate_list=data_rate_list, data_rate_perc_list=data_rate_perc_list)
        cost_list, energy_list = rwta.process_request()
        arr_cost.append(cost_list)
        arr_energy.append(energy_list)
    np_arr_cost = np.array(arr_cost)
    np_arr_cost = np.mean(np_arr_cost, axis=0)
    np_arr_energy = np.array(arr_energy)
    np_arr_energy = np.mean(np_arr_energy, axis=0)
    with open("results/results_averaged.txt", "a") as f:
        for cost in np_arr_cost:
            f.write(str(cost))
            f.write(" ")
        f.write("\n")
        for energy in np_arr_energy:
            f.write(str(energy))
            f.write(" ")
        f.write("\n")

def japanFinal():
    # todo: make sure whether to load or generate
    arr_cost = []
    arr_energy = []
    data_rate_list = [100, 200, 300, 400, 500, 600]
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
        node_add_drop_dict_list = []
        for i in range(10):
            request_file_name = "requests/requests_japan_percent_100_" + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".pkl"
            results_file = "results/" + "results_japan_opaque" + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".txt"
            rwta = RwtaTransparent(topology="japan", num_total_slots=200, request_file_name=request_file_name,
                                   load_request_flag=True, request_percentage=1, results_file=results_file,
                                   data_rate_list=data_rate_list, data_rate_perc_list=data_rate_perc_list[case_index],
                                   length_factor=length_factor)
            cost_list, energy_list = rwta.process_request()
            node_add_drop_dict = rwta.add_drop_block_port_dict
            node_add_drop_dict_list.append(node_add_drop_dict)

            arr_cost.append(cost_list)
            arr_energy.append(energy_list)

        with open("results/@adb_results_japan_OpaqueIP" + cases[case_index] + ".txt", "a") as f:
            nodes_list = list(node_add_drop_dict_list[0].keys())
            degree_list = [rwta.DG.degree[node] // 2 for node in nodes_list]
            nodes_list.sort()
            line = "Node"
            for node in nodes_list:
                line = line + "," + str(node)
            line = line + "\n"
            f.write(line)
            line = "Degree"
            for degree in degree_list:
                line = line + "," + str(degree)
            line = line + "\n"
            f.write(line)

            instance_index = 1
            for node_add_drop_dict in node_add_drop_dict_list:
                line = "Instance" + str(instance_index)
                for node in nodes_list:
                    line = line + "," + str(node_add_drop_dict[node])
                line = line + "\n"
                f.write(line)
                instance_index +=1

        np_arr_cost = np.array(arr_cost)
        np_arr_cost = np.mean(np_arr_cost, axis=0)
        np_arr_energy = np.array(arr_energy)
        np_arr_energy = np.mean(np_arr_energy, axis=0)
        with open("results/results_japan_averaged_" + cases[case_index] + "_" + str(length_factor) + ".txt", "a") as f:
            f.write("Cost: Number of ZR transponders, Number of ZR+ transponders, Number of router ports, Cost of transponders\n")
            f.write("Energy consumption: ZR Transponders, ZR+ transponders, IP routers chasis, IP router modulo MDA, IP routers, OXC, Monitoring, Total\n")
            #f.write("Energy consumption: ZR Transponders, ZR+ transponders, IP routers, OXC, Monitoring, Total\n")
        with open("results/results_japan_averaged_" + cases[case_index] + "_" + str(length_factor) + ".txt", "a") as f:
            for cost in np_arr_cost:
                f.write(str(cost))
                f.write(" ")
            f.write("\n")
            for energy in np_arr_energy:
                f.write(str(energy))
                f.write(" ")
            f.write("\n")

def german():
    # todo: make sure whether to load or generate
    arr_cost = []
    arr_energy = []
    # data_rate_list = [100, 200, 300, 400, 500, 600]
    data_rate_list = [100, 200, 300, 400, 500, 600]
    # data_rate_list = [item * 0.5 for item in data_rate_list]
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
        node_add_drop_dict_list = []
        for i in range(10):
            request_file_name = "requests/requests_german_percent_100_" + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".pkl"
            results_file = "results/" + "results_german_opaque" + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".txt"
            rwta = RwtaTransparent(topology="german", num_total_slots=200, request_file_name=request_file_name,
                                   load_request_flag=True, request_percentage=1, results_file=results_file,
                                   data_rate_list=data_rate_list, data_rate_perc_list=data_rate_perc_list[case_index],
                                   length_factor=length_factor)
            cost_list, energy_list = rwta.process_request()
            node_add_drop_dict = rwta.add_drop_block_port_dict
            node_add_drop_dict_list.append(node_add_drop_dict)

            arr_cost.append(cost_list)
            arr_energy.append(energy_list)
        with open("results/@adb_results_german_OpaqueIP" + cases[case_index] + ".txt", "a") as f:
            nodes_list = list(node_add_drop_dict_list[0].keys())
            degree_list = [rwta.DG.degree[node] // 2 for node in nodes_list]
            nodes_list.sort()
            line = "Node"
            for node in nodes_list:
                line = line + "," + str(node)
            line = line + "\n"
            f.write(line)
            line = "Degree"
            for degree in degree_list:
                line = line + "," + str(degree)
            line = line + "\n"
            f.write(line)

            instance_index = 1
            for node_add_drop_dict in node_add_drop_dict_list:
                line = "Instance" + str(instance_index)
                for node in nodes_list:
                    line = line + "," + str(node_add_drop_dict[node])
                line = line + "\n"
                f.write(line)
                instance_index += 1

        np_arr_cost = np.array(arr_cost)
        np_arr_cost = np.mean(np_arr_cost, axis=0)
        np_arr_energy = np.array(arr_energy)
        np_arr_energy = np.mean(np_arr_energy, axis=0)
        with open("results/results_german_averaged_" + cases[case_index] + "_" + str(length_factor) + ".txt", "a") as f:
            f.write("Cost: Number of ZR transponders, Number of ZR+ transponders, Number of router ports, Cost of transponders\n")
            f.write("Energy consumption: ZR Transponders, ZR+ transponders, IP routers chasis, IP router modulo MDA, IP routers, OXC, Monitoring, Total\n")
            #f.write("Energy consumption: ZR Transponders, ZR+ transponders, IP routers, OXC, Monitoring, Total\n")
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
    #rwta = RwtaTransparent(topology="japan", num_total_slots=100, request_file_name="requests/requests.pkl", load_request_flag=False)
    #rwta = RwtaTransparent(num_total_slots=30)
    #rwta.process_request()
    #seven_node()
    japanFinal()
    german()