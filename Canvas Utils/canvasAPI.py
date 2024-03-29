import requests


class CanvasAPI:
    def __init__(self, login_token, course_id):
        self.ub_url = "https://bridgeport.instructure.com/api/v1"

        self.token = login_token
        self.headers = {"Authorization": f"Bearer {self.token}"}

        self.course_id = course_id

        self.endpoint_url = f"{self.ub_url}/courses/{self.course_id}"

        self.files = Files(
            base_url=self.ub_url,
            course_id=self.course_id,
            endpoint="files",
            headers=self.headers,
        )
        self.folders = Folders(
            base_url=self.ub_url,
            course_id=self.course_id,
            endpoint="folders",
            headers=self.headers,
        )
        self.groups = Groups(
            base_url=self.ub_url,
            course_id=self.course_id,
            endpoint="assignment_groups",
            headers=self.headers,
        )
        self.assignments = Assignments(
            base_url=self.ub_url,
            course_id=self.course_id,
            endpoint="assignments",
            headers=self.headers,
        )
        self.quizzes = Quizzes(
            base_url=self.ub_url,
            course_id=self.course_id,
            endpoint="quizzes",
            headers=self.headers,
        )
        self.external_tools = APISection(
            base_url=self.ub_url,
            course_id=self.course_id,
            endpoint="external_tools",
            headers=self.headers,
        )
        self.tabs = APISection(
            base_url=self.ub_url,
            course_id=self.course_id,
            endpoint="tabs",
            headers=self.headers,
        )

    def get(self, url: str, data=None):
        if data is None:
            data = {}
        return requests.get(url=url, headers=self.headers, params=data)

    def createGradingScale(self, scale_data):
        full_path = f"{self.endpoint_url}/grading_standards"
        return requests.post(url=full_path, headers=self.headers, params=scale_data)

    def getGradingScales(self):
        full_path = f"{self.endpoint_url}/grading_standards"
        return requests.get(url=full_path, headers=self.headers).json()

    def updateCourseSettings(self, course_data):
        full_path = f"{self.endpoint_url}"
        return requests.put(url=full_path, headers=self.headers, params=course_data)


class APISection:
    def __init__(
        self, base_url: str, course_id: int | str, endpoint: str, headers: dict
    ) -> None:
        self.base_url = base_url
        self.course_id = course_id
        self.endpoint = endpoint
        self.headers = headers

        self.endpoint_url = f"{self.base_url}/courses/{self.course_id}/{self.endpoint}"

    def get(self, item_id: int | str):
        full_path = f"{self.endpoint_url}/{item_id}"
        return requests.get(url=full_path, headers=self.headers)

    def list(self, data: dict | None = None):
        if not data:
            data = {}

        full_path = f"{self.endpoint_url}"
        return requests.get(url=full_path, headers=self.headers, params=data)

    def listGenerator(self, data: dict | None = None):
        if not data:
            data = {}

        response = self.list(data)
        items = response.json()
        links = response.links

        for item in items:
            yield item

        while "next" in links:
            response = requests.get(
                url=links["next"]["url"], headers=self.headers, params=data
            )
            items = response.json()
            links = response.links

            for item in items:
                yield item

    def create(self, data: dict):
        full_path = f"{self.endpoint_url}"
        return requests.post(url=full_path, headers=self.headers, data=data)

    def edit(self, item_id: int | str, data: dict):
        full_path = f"{self.endpoint_url}/{item_id}"
        return requests.put(url=full_path, headers=self.headers, data=data)

    def delete(self, item_id: int | str):
        full_path = f"{self.endpoint_url}/{item_id}"
        return requests.delete(url=full_path, headers=self.headers)

    def deleteAll(self):
        items = self.list().json()
        while len(items) > 0:
            for item in items:
                self.delete(item["id"])
            items = self.list().json()


class Files(APISection):
    def __init__(
        self, base_url: str, course_id: int | str, endpoint: str, headers: dict
    ) -> None:
        super().__init__(base_url, course_id, endpoint, headers)

    def create(self, path: str):
        full_path = f"{self.endpoint_url}"

        # prepares canvas for file upload
        response = requests.post(
            url=full_path, headers=self.headers, params={"parent_folder_path": ""}
        )
        output = response.json()

        # gets upload path and upload parameter from canvas
        upload_url = output["upload_url"]
        upload_params = output["upload_params"]

        # file to be uploaded
        file = {"file": open(path, "rb")}

        # sends file to given upload path with given parameters
        response = requests.post(url=upload_url, data=upload_params, files=file)

        if 300 <= response.status_code <= 399:
            # if response code is 3XX, another api request must be made

            location = response.json()["Location"]
            response = requests.post(url=location, headers=self.headers)

        return response

    def get(self, item_id: int | str):
        full_path = f"{self.base_url}/{self.endpoint}/{item_id}"
        return requests.get(url=full_path, headers=self.headers)

    def edit(self, item_id: int | str, data: dict):
        full_path = f"{self.base_url}/{self.endpoint}/{item_id}"
        return requests.put(url=full_path, headers=self.headers, data=data)

    def delete(self, item_id: int | str):
        full_path = f"{self.base_url}/{self.endpoint}/{item_id}"
        return requests.delete(url=full_path, headers=self.headers)


class Folders(APISection):
    def __init__(
        self, base_url: str, course_id: int | str, endpoint: str, headers: dict
    ) -> None:
        super().__init__(base_url, course_id, endpoint, headers)

    def edit(self, item_id: int | str, data: dict):
        full_path = f"{self.base_url}/{self.endpoint}/{item_id}"
        return requests.put(url=full_path, headers=self.headers, data=data)

    def delete(self, item_id: int | str):
        full_path = f"{self.base_url}/{self.endpoint}/{item_id}"
        return requests.delete(url=full_path, headers=self.headers)

    def deleteAll(self):
        items = self.list().json()
        while len(items) > 1:
            for item in items:
                self.delete(item["id"])
            items = self.list().json()


class Assignments(APISection):
    def __init__(
        self, base_url: str, course_id: int | str, endpoint: str, headers: dict
    ) -> None:
        super().__init__(base_url, course_id, endpoint, headers)

    def grade(self, assignment_id, student_id, grade_data):
        full_path = f"{self.endpoint_url}/{assignment_id}/submissions/{student_id}"
        return requests.put(url=full_path, headers=self.headers, params=grade_data)

    def getSubmission(self, assignment_id, student_id):
        full_path = f"{self.endpoint_url}/{assignment_id}/submissions/{student_id}"
        return requests.get(url=full_path, headers=self.headers)

    def listSubmissions(self, assignment_id):
        full_path = f"{self.endpoint_url}/{assignment_id}/submissions"
        return requests.get(url=full_path, headers=self.headers)

    def listSubmissionsGenerator(self, assignment_id):
        response = self.listSubmissions(assignment_id)
        items = response.json()
        links = response.links

        for item in items:
            yield item

        while "next" in links:
            response = requests.get(url=links["next"]["url"], headers=self.headers)
            items = response.json()
            links = response.links

            for item in items:
                yield item


class Groups(APISection):
    def __init__(
        self, base_url: str, course_id: int | str, endpoint: str, headers: dict
    ) -> None:
        super().__init__(base_url, course_id, endpoint, headers)

    def enableGroupWeights(self):
        full_path = f"{self.base_url}/courses/{self.course_id}"
        return requests.put(
            url=full_path,
            headers=self.headers,
            params={"course[apply_assignment_group_weights]": True},
        )

    def disableGroupWeights(self):
        full_path = f"{self.base_url}/courses/{self.course_id}"
        return requests.put(
            url=full_path,
            headers=self.headers,
            params={"course[apply_assignment_group_weights]": False},
        )


class Quizzes(APISection):
    def __init__(
        self, base_url: str, course_id: int | str, endpoint: str, headers: dict
    ) -> None:
        super().__init__(base_url, course_id, endpoint, headers)

        self.questions = QuizElement(
            base_url=self.endpoint_url,
            course_id=self.course_id,
            endpoint="questions",
            headers=self.headers,
        )
        self.groups = QuizElement(
            base_url=self.endpoint_url,
            course_id=self.course_id,
            endpoint="groups",
            headers=self.headers,
        )


class QuizElement(APISection):
    def __init__(
        self, base_url: str, course_id: int | str, endpoint: str, headers: dict
    ) -> None:
        super().__init__(base_url, course_id, endpoint, headers)
        self.endpoint_url = ""

    # * data and params give code 500
    # * must use json
    def create(self, quiz_id, element_data):
        full_path = f"{self.base_url}/{quiz_id}/{self.endpoint}"
        return requests.post(url=full_path, headers=self.headers, json=element_data)

    def list(self, quiz_id):
        full_path = f"{self.base_url}/{quiz_id}/{self.endpoint}"
        return requests.get(url=full_path, headers=self.headers)

    def listGenerator(self, quiz_id):
        response = self.list(quiz_id)
        items = response.json()
        links = response.links

        for item in items:
            yield item

        while "next" in links:
            response = requests.get(url=links["next"]["url"], headers=self.headers)
            items = response.json()
            links = response.links

            for item in items:
                yield item

    def get(self, quiz_id, element_id):
        full_path = f"{self.base_url}/{quiz_id}/{self.endpoint}/{element_id}"
        return requests.get(url=full_path, headers=self.headers)

    def edit(self, quiz_id, element_id, element_data):
        full_path = f"{self.base_url}/{quiz_id}/{self.endpoint}/{element_id}"
        return requests.put(url=full_path, headers=self.headers, params=element_data)

    def delete(self, quiz_id, element_id):
        full_path = f"{self.base_url}/{quiz_id}/{self.endpoint}/{element_id}"
        return requests.delete(url=full_path, headers=self.headers)
