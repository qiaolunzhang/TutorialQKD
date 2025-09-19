import numpy as np
num_instances = 7
# file_list = list(range(num_cases))
# filename_prefix = "results/results_japan_averaged_rate"
folder_prefix = "results/TS8Module10/"
acceptance_ratio = np.zeros((4, num_instances), dtype=float)
num_physical_hops = np.zeros((4, num_instances), dtype=float)
num_virtual_hops = np.zeros((4, num_instances), float)
num_qkd_module = np.zeros((4, num_instances), dtype=float)

case_prefix_list = ["results_No_OB_TR_german_averaged_rate", "results_OB_german_averaged_rate",
         "results_TR_german_averaged_rate", "results_OB_TR_german_averaged_rate"]

for j in range(num_instances):
    # for file in file_list:
    #     file = file_list[j]
    for i in range(len(case_prefix_list)):
        case_prefix = case_prefix_list[i]
        filename = folder_prefix + case_prefix + str(j) + "_1.txt"
        with open(filename, "r") as f:
            lines = f.readlines()
            print(acceptance_ratio[i][j])
            tmp = float(lines[0].split(" ")[0])
            print(tmp)
            print(type(tmp))
            acceptance_ratio[i][j] = tmp
print(acceptance_ratio)