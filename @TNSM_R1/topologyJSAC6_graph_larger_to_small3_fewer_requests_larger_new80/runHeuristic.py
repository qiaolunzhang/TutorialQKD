import os

os.system('conda activate rwa')
# os.system('python ../One/a.py')
os.system('python run-mgdm.py')
os.system('python run-JLT-heuristic6-OB.py')
os.system('python run-JLT-heuristic6-TR.py')
os.system('python run-JLT-heuristic6-NoOBNoTR.py')
