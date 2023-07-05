from canvasAPI import CanvasAPI
from Utils import *
course_id = 1865191
login_token = '19~jYAYBnhsrEOXha5H8k71YZPJZ6w9U5GitGidNf9QtWuzwAop8zmpY9zWgrpqJXmp'
canvasAPI = CanvasAPI(login_token, course_id)
# os.chdir(f'./{course_id}/')

def debug(res, items = False, content=False):
    print(res)
    print(res.reason)
    print()
    [print(item,'\n') for item in res.json() if items]
    print(res.content) if content else ()

# media_id = '6595fd41-d373-40e2-83c6-7c5f1009cddf-17223'
media_id = 'c3f0a030-e54e-4142-91c7-c18b1e6e0b4c-17175'
display_media_tabs = 'false'
display_download = 'true'

# embed = f'<p><iframe class="lti-embed" style="width: 800px; height: 880px;" title="discord-call-sound" src="/courses/1865191/external_tools/retrieve?display=borderless&amp;url=https%3A%2F%2Fbridgeport.instructuremedia.com%2Flti%2Flaunch%3Fcustom_arc_display_download%3D{display_download}%26custom_arc_launch_type%3Dembed%26custom_arc_media_id%3D{media_id}%26custom_arc_start_at%3D0" width="800" height="880" allowfullscreen="allowfullscreen" webkitallowfullscreen="webkitallowfullscreen" mozallowfullscreen="mozallowfullscreen" allow="geolocation *; microphone *; camera *; midi *; encrypted-media *; autoplay *; clipboard-write *; display-capture *" data-studio-resizable="{display_media_tabs}" data-studio-tray-enabled="{display_media_tabs}" data-studio-convertible-to-link="true"></iframe></p>'
# assignment_id = 17011041
# data = {
#     'assignment[description]': embed
# }
# res = canvasAPI.assignments.edit(assignment_id,data)
# debug(res)

# [print(item) for item in canvasAPI.quizzes.questions.listGenerator()]

quiz_id = 4122071
data = {
    "question":{
        "question_name" : 'test',
        "question_text" : 'test',
        "question_type" : 'test',
        # "position" : question,
        "quiz_group_id" : None,
        "points_possible" : 'test',
        "answers" : [
            {
                "text" : 'test',
                "weight" : 100
            },
            {
                "text" : 'test',
                "weight" : 0
            },
            {
                "text" : 'test',
                "weight" : 0
            }
        ]
    }
}
debug(canvasAPI.quizzes.questions.create(quiz_id,data))

