import os

os.system('conda activate rwa')
# os.system('python ../One/a.py')
os.system('python run-JLT-heuristic6-OBTR-module.py 8')
os.system('python run-JLT-heuristic6-OB-module.py 8')
os.system('python run-JLT-heuristic6-TR-module.py 8')
os.system('python run-JLT-heuristic6-NoOBNoTR-module.py 8')
