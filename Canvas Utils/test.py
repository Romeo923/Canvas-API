from canvasAPI import CanvasAPI
from Utils import *
course_id = 1865191
login_token = 'LOGIN TOKEN'
canvasAPI = CanvasAPI(login_token, course_id)
# os.chdir(f'./{course_id}/')

# tools = canvasAPI.external_tools.list().json()
# print('\nList')
# [print(tool, "\n") for tool in tools]

# tool_id = tools[0]['id']
# print(f"\n{tool_id}")


# tool = canvasAPI.external_tools.get(tool_id)
# print('\nGet')
# print(tool)
# print(tool.reason)
# print(tool.json())

# response = canvasAPI.external_tools.delete(tool_id)
# print('\nDelete')
# print(response)
# print(response.reason)
# print(response.json())

# tool_data = {
#     "client_id": "N/A",
#     "consumer_key": "N/A",
#     "shared_secret": "N/A",
#     "privacy_level": "public",
#     "name": "Redirect Tool",
#     "url": "https://www.edu-apps.org/redirect",
#     "custom_fields[url]": "https://docs.google.com/forms/d/e/1FAIpQLSdMWslUXXzwDNnKbTb-SmRYZJmHhKcEZ6rIJpDdfSV6-SeQyg/viewform?usp=sf_link",
#     "course_navigation[text]": "Redirect Tool",
#     "course_navigation[enabled]": True
# }

# print('\nCreate')
# res = canvasAPI.external_tools.create(tool_data)
# print(res)
# print(res.json())
# print(res.reason)

# tabs = canvasAPI.getTabs()
# [print(tab) for tab in tabs]

# print("\nEdit")
# response = canvasAPI.external_tools.edit(tool_id, {"name":"TESTING"})
# print(response)
# print(response.reason)
# print(response.json())

tab_list = [
    "Home",
    "Files",
    "People",
    "Zoom",
    "Assignments",
    "Quizzes",
    "Grades",
    "Settings",
    "TEST REDIRECT",
    "Smarthinking Online Tutoring"
]

canvas_tabs = canvasAPI.tabs.listGenerator()
# [print(f"Tab: {tab['label']}\n\tID: {tab['id']}\n\tPos: {tab['position']}") for tab in canvas_tabs if tab['label'] in tab_list]

# tab_id = "people"
# data = {'position': 5}
# res = canvasAPI.tabs.edit(tab_id, data)
# print(res)
# print(res.json())
# print(res.reason)

for tab in canvas_tabs:
    hidden = tab['label'] not in tab_list
    position = tab['position'] if hidden else tab_list.index(tab['label']) + 1
    data = {'hidden': hidden, 'position': position, "label": tab["label"]}

    canvasAPI.tabs.edit(tab['id'],data)
    print(f'{tab["label"]}: {data}')
