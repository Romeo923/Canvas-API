import os

os.chdir('./1865191/')


#! Init Canvas
# import initCanvas
# initCanvas.main()

#! Edit Canvas
import editCanvas

#* uploads a quiz worth '' points with due date ''
# os.chdir('./quiz/')
# upload_assignment = ['-ua','test quiz']
# editCanvas.main(*upload_assignment)

#* uploads file
# os.chdir('./slide/')
# upload_file = ['-uf','']
# editCanvas.main(*upload_file)

#* uploads hmk with pdf worth '' points with due date ''
# os.chdir('./hmk/')
# upload_assignment_and_file = ['-uaf','test assignment']
# editCanvas.main(*upload_assignment_and_file)

#* publishes quiz-12
os.chdir('./quiz/')
edit = ['-raP','quiz-12','True']
editCanvas.main(*edit)

#* changes due date for quiz-12 to '11/25/2022'
#* changes points for quiz-12 to 50
os.chdir('./quiz/')
edit = ['-radp','quiz-12','11/25/2022','50']
editCanvas.main(*edit)

#* changes due date for quiz-5 to '10/10/2022'
#* changes points for quiz-5 to 75
#* publishes quiz-5
os.chdir('./quiz/')
edit = ['-radpP','quiz-5','10/10/2022','75','True']
editCanvas.main(*edit)

#* shifts quiz-19 to '12/27/2022'
#* should remove quizzes 21-45
os.chdir('./quiz/')
shift = ['-sa','quiz-19','12/27/2022']
editCanvas.main(*edit)


#! Grade Canvas
# import gradeCanvas
# gradeCanvas.main()
