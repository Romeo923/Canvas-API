import os
from Utils import *

os.chdir('./1865191/')

import canvas

#* display all flags
canvas.main('--help')

#* reset and init canvas
canvas.main('--init')

#* create a new assignment
os.chdir('./hmk/')
create_assignment = ['hmk-test', '55', 'true']
canvas.main(*create_assignment)

#* edit an assignment
edit_assignment = ['-r', 'hmk-7', '10/12/2025', 'false']
canvas.main(*edit_assignment)

#* delete an assignment
delete_assignment = ['-d', 'quiz-3']
canvas.main(*delete_assignment)

#* upload a file with name indexing 3 times
#* should upload file-1, file-2, and file-3
os.chdir('../slide/')
index_file = ['-i', 'Slide 4.pdf']
canvas.main(*index_file)
canvas.main(*index_file)
canvas.main(*index_file)

#* shift assignment due dates
os.chdir('../quiz/')
shift_assignment = ['-s', 'quiz-30', '12/20/2022']
canvas.main(*shift_assignment)

print_stderr('\nTest Complete.\n')
