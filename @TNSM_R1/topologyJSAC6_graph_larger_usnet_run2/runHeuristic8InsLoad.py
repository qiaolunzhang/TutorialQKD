import os

os.system('conda activate rwa')
# os.system('python ../One/a.py')
os.system('python run-JLT-heuristic6-OBTR.py 8 1')
os.system('python run-JLT-heuristic6-OB.py 8')
os.system('python run-JLT-heuristic6-TR.py 8')
os.system('python run-JLT-heuristic6-NoOBNoTR.py 8')
