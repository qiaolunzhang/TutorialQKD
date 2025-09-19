import os

os.system('conda activate rwa')
# os.system('python ../One/a.py')

# the first parameter is the number of instance
# the second parameter is 0 if we want to generate new data
# 1 if we want to load data
os.system('python run-JLT-heuristic6-OBTR.py 1 0')
os.system('python run-JLT-heuristic6-OB.py 1')
os.system('python run-JLT-heuristic6-TR.py 1')
os.system('python run-JLT-heuristic6-NoOBNoTR.py 1')
