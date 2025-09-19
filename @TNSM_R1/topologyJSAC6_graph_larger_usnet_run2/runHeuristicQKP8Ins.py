import os

os.system('conda activate rwa')
# os.system('python ../One/a.py')
os.system('python run-JLT-heuristic6-OBTR-qkp.py 8')
os.system('python run-JLT-heuristic6-OB-qkp.py 8')
os.system('python run-JLT-heuristic6-TR-qkp.py 8')
os.system('python run-JLT-heuristic6-NoOBNoTR-qkp.py 8')
