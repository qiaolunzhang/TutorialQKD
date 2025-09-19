import numpy as np

acceptance_matrix = np.zeros((4,8))
folder = "../results/tnsm_r1/load/"

setting_list = ["No_OB_TR", "OB", "TR", "OB_TR"]

for setting_index in range(len(setting_list)):
    for instance_index in range(8):
        file_name = folder + "results_" + setting_list[setting_index] + "_usnet_averaged_rate0_1_" + str(instance_index) + ".txt"
        with open(file_name, "r") as f:
            lines = f.readlines()
            line1 = lines[0].split(" ")
            current_acceptance = float(line1[0]) * 100
        acceptance_matrix[setting_index,instance_index] = current_acceptance

print(acceptance_matrix)

data = acceptance_matrix
# Assuming you have a (4, 8) array called 'data' containing the values

# Calculate the mean and standard deviation along the second axis (instances)
mean_values = np.mean(data, axis=1)
std_values = np.std(data, axis=1)

# Calculate the margin of error using the standard deviation and the t-value for a 95% confidence interval
t_value = 1.96  # For a 95% confidence interval and a large sample size
margin_of_error = t_value * std_values / np.sqrt(data.shape[1])  # Square root of the number of instances

# Calculate the confidence interval
confidence_interval_lower = mean_values - margin_of_error
confidence_interval_upper = mean_values + margin_of_error

# Print the confidence intervals for each setting
for i in range(data.shape[0]):
    print(f"Setting {i+1}: Mean = {mean_values[i]}, Confidence Interval = [{confidence_interval_lower[i]}, {confidence_interval_upper[i]}]")
