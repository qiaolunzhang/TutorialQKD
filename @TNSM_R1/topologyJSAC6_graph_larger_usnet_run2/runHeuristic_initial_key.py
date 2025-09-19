import os

os.system('conda activate rwa')
# os.system('python ../One/a.py')
os.system('python run-JLT-heuristic6-OBTR.py 1 0 1')
os.system('python run-JLT-heuristic6-OB.py 1 1')
os.system('python run-JLT-heuristic6-TR.py 1 1')
os.system('python run-JLT-heuristic6-NoOBNoTR.py 1 1')
