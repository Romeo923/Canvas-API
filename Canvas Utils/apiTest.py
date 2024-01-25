import os
from Utils import *

os.chdir('./1865191/')

import canvas

#* display all flags
# canvas.main(canvas.HELP)

# # * dispalys course details
# canvas.main(canvas.DETAILS)

# * reset and init canvas
# canvas.main(canvas.INIT)

#* reorders tabs
tab_list = [
    "Home",
    "Assignments",
    "TEST REDIRECT",
    "Grades",
    "People",
    "Files",
    "Quizzes",
    "Zoom",
    "Smarthinking Online Tutoring"
    "Settings",
]
# tabs = [canvas.REORDER, tab_list]
# canvas.main(*tabs)

# #* create a new assignment
# os.chdir('./hmk/')
# create_assignment = ['hmk-75', '55', 'true']
# canvas.main(*create_assignment)

#* reuploads a quiz
# quiz = [canvas.QUIZ, 'Quiz 1']
# canvas.main(*quiz)

# #* edit an assignment
# edit_assignment = [canvas.REPLACE, 'hmk-1', '22', '10/12/2022']
# canvas.main(*edit_assignment)

# #* delete an assignment
# delete_assignment = [canvas.DELETE, 'hmk-1']
# canvas.main(*delete_assignment)

# #* upload a file with name indexing 3 times
# #* should upload file-1, file-2, and file-3
# os.chdir('../slide/')
# index_file = [canvas.INDEX, 'Slide 4.pdf']
# canvas.main(*index_file)
# canvas.main(*index_file)
# canvas.main(*index_file)

# #* shift assignment due dates
# os.chdir('../quiz/')
# shift_assignment = [canvas.SHIFT, 'quiz-30', '12/20/2022']
# canvas.main(*shift_assignment)

# #* grades assignments
# os.chdir('..')
# grade_assignments = [canvas.GRADE,'true']
# canvas.main(*grade_assignments)

# #* downloads submissions
# download_submissions = [canvas.DOWNLOAD, 'hmk-1']
# canvas.main(*download_submissions)

# # * sync data
# sync = [canvas.SYNC]
# canvas.main(*sync)

# * download quiz
# args = [canvas.QUIZ,'literally-anything', 'get']
args = [canvas.QUIZ,'Quiz 1']
canvas.main(*args)

print_stderr('\nTest Complete.\n')
