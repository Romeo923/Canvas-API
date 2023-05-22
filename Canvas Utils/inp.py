import os
import yaml

class Inp:

    def __init__(self, root_dir: str, settings: dict, course_id: str):
        self.root_dir = root_dir
        self.settings = settings
        self.course_id = course_id

        path = os.path.join(self.root_dir, 'ids.yaml')

        if not os.path.exists(path):
            self._allIDs = {}
            self.reset()
        else:
            with open(path, 'r') as f:
                self._allIDs = yaml.safe_load(f)

        self.IDs:dict = self._allIDs[self.course_id]

    def __getitem__(self,setting: str):
        return self.IDs if setting == 'IDs' else self.settings[setting]

    def __setitem__(self, setting: str, data: dict[str, dict]):
        if setting != 'IDs':
            raise KeyError(f"Cannot alter value of {setting}")
        self.IDs = data

    def __iter__(self):
        return self.settings.__iter__()

    def exists(self, name):
        return name in self.IDs['Assignments'] or name in self.IDs['Files']

    def save(self):
        self._allIDs[self.course_id] = self.IDs
        with open(os.path.join(self.root_dir, 'ids.yaml'), 'w') as f:
            yaml.safe_dump(self._allIDs, f, sort_keys=False)

    def reset(self):
        self.IDs = {
            "Groups":{},
            "Assignments":{},
            "Quizzes":{},
            "Files":{},
            "Folders":{}
        }

        self.save()

