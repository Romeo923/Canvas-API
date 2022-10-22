import json

class Inp:

    #? give IDs property for easier id fetching -> self.IDs["Files"] vs self["IDs"]['Files]
    def __init__(self, root_dir: str, settings: dict, all_settings: dict, course_id: str):
        self.root_dir = root_dir
        self.settings = settings
        self.all_settings = all_settings
        self.course_id = course_id

    def __getitem__(self,setting: str):
        return self.all_settings[self.course_id]['IDs'] if setting == 'IDs' else self.settings[setting]

    def __setitem__(self, setting: str, data: str | dict):
        if setting == 'IDs':
            self.all_settings[self.course_id][setting] = data
        else:
            self.settings[setting] = data

    def __iter__(self):
        return self.settings.__iter__()

    def exists(self, name):
        return name in self['IDs']['Assignments'] or name in self['IDs']['Files']

    def save(self):
        with open(self.root_dir, 'w') as f:
            json.dump(self.all_settings, f, indent= 2)

    def reset(self):
        self['IDs'] = {
            "Groups":{},
            "Assignments":{},
            "Files":{},
            "Folders":{}
        }

        self.save()

