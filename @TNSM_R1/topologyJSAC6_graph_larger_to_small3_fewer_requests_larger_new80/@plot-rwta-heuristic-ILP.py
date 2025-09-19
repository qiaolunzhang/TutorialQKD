#!/usr/bin/env python
# coding: utf-8

# In[9]:


import numpy as np
import matplotlib as mpl
#mpl.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

# plt.rc('font', family='serif', serif='Times')
# Arial
plt.rc('font', family='serif', serif='Times')
plt.rc('text', usetex=True)
plt.rc('xtick', labelsize=7)
plt.rc('ytick', labelsize=7)
plt.rc('axes', labelsize=8)
#axes.linewidth : 0.5
plt.rc('axes', linewidth=0.5)
#ytick.major.width : 0.5
plt.rc('ytick.major', width=0.5)
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rc('ytick.minor', visible=True)

# set grid under the plot
# https://stackoverflow.com/questions/23357798/how-to-draw-grid-lines-behind-matplotlib-bar-graph
# https://stackoverflow.com/questions/1726391/matplotlib-draw-grid-lines-behind-other-graph-elements/39039520#39039520
plt.rc('axes', axisbelow=True)


#plt.style.use(r"..\..\styles\infocom.mplstyle") # Insert your save location here

# width as measured in inkscape
fig_width = 3.487
fig_height = fig_width / 1.618
# fig_height = 1.8
#fig_height = fig_width / 1.3 / 2


# In[10]:


num_instances = 4
selected_instance_list = [0, 3]
folder_prefix = "results/"
acceptance_ratio = np.zeros((4, num_instances), dtype=float)
stored_keys = np.zeros((4, num_instances), dtype=float)
num_physical_hops = np.zeros((4, num_instances), dtype=float)
num_virtual_hops = np.zeros((4, num_instances), float)
num_qkd_module = np.zeros((4, num_instances), dtype=float)

objective_value = np.zeros((4, num_instances), dtype=float)
execution_time = np.zeros((4, num_instances), dtype=float)

case_prefix_list = ["results_No_OB_TR_poliqi_averaged_rate", "results_OB_poliqi_averaged_rate", 
         "results_TR_poliqi_averaged_rate", "results_OB_TR_poliqi_averaged_rate"]


# In[11]:


for i in range(len(case_prefix_list)):
    case_prefix = case_prefix_list[i]
    filename = folder_prefix + case_prefix + str(0) + "_1.txt"
    with open(filename, "r") as f:
        lines = f.readlines()
        tmp = 100 * float(lines[0].split(" ")[0])
        acceptance_ratio[i][1] = tmp
        objective_value[i][1] = float(lines[0].split(" ")[3])
        stored_keys[i][1] = float(lines[1].split(" ")[0])
        execution_time[i][1] = float(lines[1].split(" ")[4])

for i in range(len(case_prefix_list)):
    case_prefix = case_prefix_list[i]
    filename = folder_prefix + case_prefix + str(1) + "_1.txt"
    with open(filename, "r") as f:
        lines = f.readlines()
        tmp = 100 * float(lines[0].split(" ")[0])
        acceptance_ratio[i][3] = tmp
        objective_value[i][3] = float(lines[0].split(" ")[3])
        stored_keys[i][3] = float(lines[1].split(" ")[0])
        execution_time[i][3] = float(lines[1].split(" ")[4])
            
            
print(acceptance_ratio)
print(stored_keys)
print(objective_value)
print(execution_time)


# In[20]:


folder_prefix = "results/bonsai-ilp/"

filename = folder_prefix + "Poliqi-case-0-module-2.txt"

setting_index = 0
num_instances = 0
with open(filename, "r") as f:
    lines = f.readlines()
    for line in lines:
        line_ele_list = line.split(",")
        if "Time" in line and "CPLEX" not in line:
            execution_time[setting_index][0] += float(line.split(":")[1])
        if len(line_ele_list) != 4:
            continue
        else:
#             print(line_ele_list)
            objective_value[setting_index][0] += float(line_ele_list[0])
            print(acceptance_ratio[setting_index][0])
            acceptance_ratio[setting_index][0] += 100 * float(line_ele_list[1])
            print(acceptance_ratio[setting_index][0])
            print(acceptance_ratio)
            print(float(line_ele_list[1]))
            stored_keys[setting_index][0] += float(line_ele_list[3])
            setting_index = (setting_index + 1) % 4
            num_instances = num_instances + 1
    num_instances = int(num_instances / 4)
    print(num_instances)
print(acceptance_ratio)
for i in range(4):
    for j in [0]:
        acceptance_ratio[i][j] /= num_instances
        stored_keys[i][j] /= num_instances    
        objective_value[i][j] /= num_instances
        execution_time[i][j] /= num_instances

filename = folder_prefix + "Poliqi-case-1-module-2.txt"

setting_index = 0
num_instances = 0
with open(filename, "r") as f:
    lines = f.readlines()
    for line in lines:
        line_ele_list = line.split(",")
        if "Time" in line and "CPLEX" not in line:
            execution_time[setting_index][2] += float(line.split(":")[1])
        if len(line_ele_list) != 4:
            continue
        else:
#             print(line_ele_list)
            objective_value[setting_index][2] += float(line_ele_list[0])
            acceptance_ratio[setting_index][2] += 100 * float(line_ele_list[1])
            stored_keys[setting_index][2] += float(line_ele_list[3])
            setting_index = (setting_index + 1) % 4
            num_instances = num_instances + 1
    num_instances = int(num_instances / 4)

for i in range(4):
    for j in [2]:
        acceptance_ratio[i][j] /= num_instances
        stored_keys[i][j] /= num_instances
        objective_value[i][j] /= num_instances
        execution_time[i][j] /= num_instances

print(acceptance_ratio)
print(stored_keys)
print(objective_value)
print(execution_time)
print("num instances is: ", num_instances)


# In[15]:


color_list = ['#46509d', '#82a8ca', '#eeb976', '#d46247']

num_instances = 4
fig, ax = plt.subplots(nrows=1, ncols=2)
N = num_instances
ind = np.arange(N) 
# width = 1 / (num_instances-1)
width = 1 / (num_instances+1)

stage = np.arange(7)

print(stage)
print(ax)
marker_list = ["p", "v", "x", ".", "*"]
#label_list = ['No-rec', 'Link-rec', 'Lim-rec(5,0)', 'Lim-rec(5,2)', 'Any-rec']
label_list = ['No-OB-No-Tr', 'OB', 'Tr', 'OB-TR', 'Any-rec']
patterns = ('//////','\\\\\\','---',  'xxx', 'ooo ', '\\', '\\\\','++', '*', 'O', '.')

x_tick_label_list = ['S-ILP', 'S-H', 'L-ILP', 'L-H']
# x_tick_label_list = x_tick_label_list[0:num_instances]
# x_tick_label_list = x_tick_label_list[0+start_line:start_line+num_instances]
# x_tick_label_list = [float(elem) for elem in x_tick_label_list]

dataMatrix0 = acceptance_ratio
for i in range(4):
    ax[0].bar(ind + width * (i-1), dataMatrix0[i], width, label=label_list[i],
               hatch=patterns[i], alpha=0.9, color=color_list[i], edgecolor='black', linewidth=0.3)

dataMatrix1 = stored_keys
for i in range(4):
    ax[1].bar(ind + width * (i-1), dataMatrix1[i], width, label=label_list[i],
               hatch=patterns[i], alpha=0.9, color=color_list[i], edgecolor='black', linewidth=0.3)

ax[0].set_ylabel('Acceptance ratio (\%)')
ax[0].set_xlabel('Network settings')
# ax[0].set_title("subtitle")
ax[0].set_title('(a) Acceptance ratio', y=-0.55, fontsize=8)

ax[1].set_ylabel('Key storing rate (kb/s)')
ax[1].set_xlabel('Network settings')
ax[1].set_title('(b) Key storing rate', y=-0.55, fontsize=8)

# for i in range(0, 4):
#     ax[i].legend(loc='upper right',# bbox_to_anchor=(0.5, 1.2),
#               ncol=1, prop={'size': 5}, labelspacing=0.2)
# ax[0].legend(loc='upper center', bbox_to_anchor=(2.3, 1.28),
#           ncol=5, prop={'size': 6.5}, handletextpad=0.2)
ax[0].legend(loc='upper center', bbox_to_anchor=(1.1, 1.28),
          ncol=5, prop={'size': 6.5}, handletextpad=0.2)
    
mpl.pyplot.subplots_adjust(wspace = 0.35, hspace=0.5)
fig.subplots_adjust(left=.12, bottom=.3, right=.99, top=.85)

label_position = ind #+ width * (1.5 - 1)
label_position = [elem + width/2 for elem in label_position]
print(label_position)
print(x_tick_label_list)

for i in range(0, 2):
    ax[i].grid(lw = 0.25)
    ax[i].set_xticks(label_position)
    ax[i].set_xticklabels(x_tick_label_list)

# ax[1].ticklabel_format(style='sci', scilimits=(-1,2), axis='y')

#     ax[i].xaxis.set_major_locator(MaxNLocator(integer=True))
plt.rcParams['hatch.linewidth'] = 0.25  # previous pdf hatch linewidth

fig.set_size_inches(fig_width, fig_height/1.3)
plt.show()
fig.savefig('plot/@ilp-heuristic-allfigs.png')
fig.savefig('plot/@ilp-heuristic-allfigs.pdf')
# fig.savefig('heuristic-utilization-CC.pdf')


# In[ ]:




