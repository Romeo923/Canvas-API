import os

print()
print(os.getcwd())
os.chdir('./1865191/quiz')
print(os.getcwd())


#! Init Canvas
# import initCanvas
# initCanvas.main()

#! Edit Canvas
import editCanvas

edit = ['-raP','quiz-12','True']
upload = ['-ua','test assignment']
shift = ['-sa','quiz-19','12/27/2022']

args = edit
editCanvas.main(*args)

#! Grade Canvas
# import gradeCanvas
# gradeCanvas.main()