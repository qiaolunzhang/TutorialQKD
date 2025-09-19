from JsacHeuristic6TR import *
import sys

def Poliqi(num_instances=1, start_instance:int=None, end_instance:int=None):
    # todo: make sure whether to load or generate
    key_rate_list = [3, 6, 9, 12, 15, 18, 21]
    # key_rate_list = [3, 6, 9, 12, 15, 18, 21]
    # key_rate_list = [1, 5, 9, 13, 17, 21]
    # key_rate_list = [0.7 * elem for elem in key_rate_list]
    # data_rate_perc_list = [[0.20, 0.25, 0.25, 0.20, 0.05, 0.05],
    #                        [0.05, 0.20, 0.25, 0.25, 0.20, 0.05],
    #                        [0.05, 0.05, 0.20, 0.25, 0.25, 0.20]]
    # data_rate_perc_list = [[0.4, 0.4, 0.05, 0.05, 0.05, 0.05],
    #                        [0.05, 0.05, 0.4, 0.4, 0.05, 0.05],
    #                        [0.05, 0.05, 0.05, 0.05, 0.4, 0.4]]
    # data_rate_perc_list = [[0.15, 0.25, 0.25, 0.15, 0.10, 0.10],
    #                        [0.10, 0.15, 0.25, 0.25, 0.15, 0.10],
    #                        [0.10, 0.10, 0.15, 0.25, 0.25, 0.15]]
    data_rate_perc_list = [[1, 0, 0, 0, 0, 0, 0],
                           [0, 1, 0, 0, 0, 0, 0],
                           [0, 0, 1, 0, 0, 0, 0],
                           [0, 0, 0, 1, 0, 0, 0],
                           [0, 0, 0, 0, 1, 0, 0],
                           [0, 0, 0, 0, 0, 1, 0],
                           [0, 0, 0, 0, 0, 0, 1]]

    # qkp_key_rate_list = [3, 0, 0, 0, 0]
    qkp_key_rate_list = [0, 0, 0, 0, 0]
    qkp_rate_perc_list = [1, 0, 0, 0, 0]
    #qkp_storing_file_name = "storedKeys/storedKeys.pkl"
    load_qkp_keys_flag = True
    load_request_flag = True
    # load_qkp_keys_flag = False
    # load_request_flag = False

    # cases = ['rate1', 'rate2', 'rate3']
    cases = ['rate' + str(num) for num in range(len(data_rate_perc_list))]
    # *********************************Define the number of cases and instances*******************************
    num_cases = len(cases)
    # num_instances = 8
    # num_cases = 1
    # num_instances = 1

    length_factor = 1
    topology_name = "usnet"
    num_qkd_channels = 5
    num_qkd_modules = 10
    num_shortest_path = 2

    # it is calculated with key rate
    num_max_qkp = 50

    num_time_slots = 8
    length_one_time_slot = 1
    num_time_slot_frame = 10

    # request_percentage = 1
    request_percentage = 0.8#5/6
    request_percentage_value = str(min(int(request_percentage * 100), 100))

    # num_qkd_modules_list = [8, 10, 12, 14, 16, 18, 20]
    num_qkd_modules_list = [3, 6, 9, 12, 15, 18, 21, 24, 27]

    for num_qkd_modules_index in range(len(num_qkd_modules_list)):
        num_qkd_modules = num_qkd_modules_list[num_qkd_modules_index]
        case_index = 4

        arr_cost = []
        arr_energy = []
        # if case_index != 2:
        #     continue
        # if case_index not in [5, 6]:
        # # if case_index not in [6]:
        #         continue
        load_request_pair_flag_current = True
        if start_instance is None:
            instance_list = list(range(num_instances))
        else:
            instance_list = list(range(start_instance, end_instance+1))
        # for i in range(num_instances):
        for i in instance_list:
            # if i not in [7]:
            #     continue
            request_file_name = "requests/requests_" + topology_name + "_percent_" + request_percentage_value \
                                + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".pkl"
            key_storing_file_name = "storedKeys/key_storing_" + topology_name + "_percent_" + request_percentage_value \
                                + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".pkl"
            results_file = "results/" + "results_" + topology_name + "_" + cases[case_index] + "_" + str(length_factor) \
                                + "_" + str(i) + ".txt"
            rwta = NetworkEnvironment(topology=topology_name, num_total_channels=num_qkd_channels,
                                      num_max_qkp=num_max_qkp,
                                      num_qkd_modules=num_qkd_modules,
                                      num_time_slots=num_time_slots, length_one_time_slot=length_one_time_slot,
                                      num_time_slot_frame=num_time_slot_frame,
                                      num_shortest_path=num_shortest_path,
                                      qkp_key_rate_list=qkp_key_rate_list, qkp_rate_perc_list=qkp_rate_perc_list,
                                      qkp_storing_file_name=key_storing_file_name, load_qkp_keys_flag=load_qkp_keys_flag,
                                      request_file_name=request_file_name, load_request_flag=load_request_flag,
                                      load_request_pair_flag=load_request_pair_flag_current,
                                      request_percentage=request_percentage,
                                      results_file=results_file, key_rate_list=key_rate_list,
                                      key_rate_perc_list=data_rate_perc_list[case_index],
                                      length_factor=length_factor)
            cost_list, energy_list = rwta.process_request()

            arr_cost.append(cost_list)
            arr_energy.append(energy_list)
            folder = "results/tnsm_r1/module/"
            try:
                if not os.path.exists(folder):
                    os.makedirs(folder)
            except Exception as e:
                print(e)
            file_name = folder + "results_module_TR_" + topology_name + "_averaged_" + cases[case_index] + "_" + str(length_factor) + ".txt"
            with open(file_name, "a") as f:
                for cost in cost_list:
                    f.write(str(cost))
                    f.write(" ")
                f.write("\n")
                for energy in energy_list:
                    f.write(str(energy))
                    f.write(" ")
                f.write("\n")

        np_arr_cost = np.array(arr_cost)
        np_arr_cost = np.mean(np_arr_cost, axis=0)
        np_arr_energy = np.array(arr_energy)
        np_arr_energy = np.mean(np_arr_energy, axis=0)
        with open("results/results_module_TR_" + topology_name + "_averaged_" + cases[case_index] + "_" + str(length_factor) + ".txt", "a") as f:
            for cost in np_arr_cost:
                f.write(str(cost))
                f.write(" ")
            f.write("\n")
            for energy in np_arr_energy:
                f.write(str(energy))
                f.write(" ")
            f.write("\n")


if __name__ == "__main__":
    # num_instance = int(sys.argv[1])
    if len(sys.argv) > 1:
        num_instance = int(sys.argv[1])
    else:
        num_instance = 1
    if len(sys.argv) > 5:
        start_instance = int(sys.argv[4])
        end_instance = int(sys.argv[5])
    else:
        start_instance = 0
        end_instance = num_instance-1
    Poliqi(num_instances=num_instance, start_instance=start_instance, end_instance=end_instance)
