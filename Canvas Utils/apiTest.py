import os
from Utils import *

os.chdir('./1865191/')

import canvas

#* display all flags
canvas.main(canvas.HELP)

#* reset and init canvas
canvas.main(canvas.INIT)

#* create a new assignment
os.chdir('./hmk/')
create_assignment = ['hmk-test', '55', 'true']
canvas.main(*create_assignment)

#* edit an assignment
edit_assignment = [canvas.REPLACE, 'hmk-1', '10/12/2025']
canvas.main(*edit_assignment)

#* delete an assignment
delete_assignment = [canvas.DELETE, 'quiz-3']
canvas.main(*delete_assignment)

#* upload a file with name indexing 3 times
#* should upload file-1, file-2, and file-3
os.chdir('../slide/')
index_file = [canvas.INDEX, 'Slide 4.pdf']
canvas.main(*index_file)
canvas.main(*index_file)
canvas.main(*index_file)

#* shift assignment due dates
os.chdir('../quiz/')
shift_assignment = [canvas.SHIFT, 'quiz-30', '12/20/2022']
canvas.main(*shift_assignment)

#* grades assignments
os.chdir('..')
grade_assignments = [canvas.GRADE,'true']
canvas.main(*grade_assignments)

#* downloads submissions
download_submissions = [canvas.DOWNLOAD, 'hmk-1']
canvas.main(*download_submissions)

print_stderr('\nTest Complete.\n')
