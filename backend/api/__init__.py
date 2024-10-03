import os
from typing import Optional

import requests
from requests.exceptions import ConnectionError
from tenacity import retry, wait_exponential, stop_after_attempt

from src.utils import printyellow
from .utils import get_filename_from_response_headers, write_json_response, write_file_response, \
    remove_after_first_slash

DEFAULT_API_URL = os.getenv('DEFAULT_API_URL', 'http://127.0.0.1:8000')


class ApiException(Exception):
    pass


class Api:
    def __init__(self, api_url: Optional[str] = None, create_response_files: bool = True) -> None:
        """
        Initializes the API client with a specified server URL and an option to create response files.

        :param api_url: The base URL for the API server. If not specified, defaults to "http://127.0.0.1:8000".
        :param create_response_files: Indicates if the client should create response files for each API call. This is useful for debugging or development purposes. Defaults to True.
        """
        self._api_url = remove_after_first_slash(api_url) if api_url else DEFAULT_API_URL
        self._create_response_files = create_response_files  # Flag for creating response files
        printyellow(f"\nAPI initialized with URL: {self._api_url}")

        if not self.is_api_running():
            raise ApiException(f"API at {self._api_url} is not running. Please check if the API is up and running.")

    @staticmethod
    def _create_filename(path):
        return "output/responses/" + path + ".json"

    def _write_json(self, filename, data):
        """
        Writes data to a JSON file specified by the filename. This method only runs if the create_response_files flag is True.

        :param filename: The filename for the JSON file to be created.
        :param data: The data to be written to the file.
        """
        if self._create_response_files:
            path = self._create_filename(filename)
            write_json_response(path, data)
            printyellow(f"\nView {filename} response at: ./{path}")

    def _make_api_url(self, path):
        return f"{self._api_url}/{path}"

    @staticmethod
    def _raise_for_status(response):
        if 400 <= response.status_code < 500:
            data = response.json()
            message = data.get("message")
            if message:
                raise ApiException(message)
            else:
                response.raise_for_status()
        elif 500 <= response.status_code < 600:
            response.raise_for_status()

    # Add retry decorator to critical API calls
    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
    def is_api_running(self) -> bool:
        """
        Checks if the API is running by performing a health check on the "/api" endpoint.

        :return: True if the health check is successful, otherwise False.
        """
        try:
            response = requests.get(self._make_api_url("api"))
            # Check if the response status code is 200 (OK)
            return response.status_code == 200
        except ConnectionError:
            raise ApiException(
                f"API at {self._api_url} is not running. Check the network connection, or verify if the API is running on a different endpoint. In case the API is running on a different endpoint, you can pass the endpoint as follows: api = Api('https://example.com')"
            )

    def create_task(self, data, scraper_name=None, sync=True):
        """
        Submits a task to the server.

        :param data: The data to be processed by the task.
        :param scraper_name: The name of the scraper to use for the task. If not provided, the server will use the default scraper.
        :param sync: Whether the task should be synchronous (True) or asynchronous (False).
        :return: The created task object.
        """
        task_type = "create-task-sync" if sync else "create-task-async"
        url = self._make_api_url(f"api/tasks/{task_type}")
        payload = {
            "data": data,
            "scraper_name": scraper_name,
        }
        response = requests.post(url, json=payload)
        self._raise_for_status(response)
        response_data = response.json()
        self._write_json(f"create_{task_type}", response_data)
        return response_data

    def create_tasks(self, data_items, scraper_name=None, sync=True):
        """
        Submits multiple tasks to the server, either synchronous or asynchronous.

        :param data_items: A list of dictionaries, each containing the scraper's input data.
        :param scraper_name: The name of the scraper to use for the tasks.
        :param sync: Boolean to indicate if the tasks are synchronous (True) or asynchronous (False).
        :return: A list of created task objects.
        """
        task_type = "create-task-sync" if sync else "create-task-async"
        url = self._make_api_url(f"api/tasks/{task_type}")
        payload = [{"data": data, "scraper_name": scraper_name} for data in data_items]
        response = requests.post(url, json=payload)
        self._raise_for_status(response)
        response_data = response.json()
        self._write_json(f"create_{task_type}_tasks", response_data)
        return response_data

    def get_tasks(self, page=1, per_page=None, with_results=True):
        """
        Fetches tasks from the server, with optional result inclusion, pagination, and filtering.

        :param page: The page number for pagination.
        :param per_page: The number of tasks to return per page.
        :param with_results: Whether to include the task results in the response.
        :return: A dictionary containing the task results and pagination information.
        """
        url = self._make_api_url("api/tasks")
        params = {
            "with_results": str(with_results).lower(),
        }
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["per_page"] = str(per_page)

        response = requests.get(url, params=params)
        self._raise_for_status(response)
        response_data = response.json()

        if self._create_response_files:
            has_many_pages = response_data["total_pages"] > 1

            filename = f"get_tasks-page-{page}" if has_many_pages else "get_tasks"
            msg = f"get_tasks, page {page}" if has_many_pages else "get_tasks"
            path = self._create_filename(filename)
            write_json_response(path, response_data)
            printyellow(f"\nView {msg} response at: ./{path}")

        return response_data

    def get_task(self, task_id):
        """
        Retrieves a specific task by ID.

        :param task_id: The ID of the task to retrieve.
        :return: The task object.
        """
        url = self._make_api_url(f"api/tasks/{task_id}")
        response = requests.get(url)
        self._raise_for_status(response)
        response_data = response.json()
        self._write_json("get_task", response_data)  # Call write_json with method name
        return response_data

    def get_task_results(self, task_id, filters=None, sort=None, view=None, page=1, per_page=None):
        """
        Retrieves the results of a specific task.

        :param task_id: The ID of the task.
        :param filters: A dictionary of filters to apply to the task results, optional.
        :param sort: The sort to apply to the task results, optional.
        :param view: The view to apply to the task results, optional.
        :param page: The page number to retrieve, default is 1.
        :param per_page: The number of results to return per page. If per_page is not provided, all results are returned, optional.

        :return: A dictionary containing the task results and pagination information if page and per_page are provided.
        """
        url = self._make_api_url(f"api/tasks/{task_id}/results")
        payload = {}
        if filters:
            payload["filters"] = filters
        if sort:
            payload["sort"] = sort
        if view:
            payload["view"] = view
        if page:
            payload["page"] = page
        if per_page:
            payload["per_page"] = per_page
        response = requests.post(url, json=payload)
        self._raise_for_status(response)
        response_data = response.json()

        if self._create_response_files:
            has_many_pages = response_data["total_pages"] > 1

            filename = f"get_task_results-page-{page}" if has_many_pages else "get_task_results"
            msg = f"get_task_results, page {page}" if has_many_pages else "get_task_results"
            path = self._create_filename(filename)
            write_json_response(path, response_data)
            printyellow(f"\nView {msg} response at: ./{path}")

        return response_data

    def download_task_results(
            self, task_id, data_format=None, filters=None, sort=None, view=None, convert_to_english=True
    ):
        """
        Downloads the results of a specific task in the specified format.

        :param task_id: The ID of the task.
        :param data_format: The format to download the task results in. Available formats are "json", "csv", "excel". The default format is "json".
        :param filters: A dictionary of filters to apply to the task results, optional.
        :param sort: The sort to apply to the task results, optional.
        :param view: The view to apply to the task results, optional.
        :param convert_to_english: Whether to convert the task results to English, default is True, optional.

        :return: The downloaded task results in the specified format as bytes.
        """
        payload = {}
        if data_format:
            payload["format"] = data_format
        if filters:
            payload["filters"] = filters
        if sort:
            payload["sort"] = sort
        if view:
            payload["view"] = view
        if convert_to_english:
            payload["convert_to_english"] = convert_to_english

        url = self._make_api_url(f"api/tasks/{task_id}/download")
        response = requests.post(url, json=payload)
        self._raise_for_status(response)

        content = response.content
        filename = get_filename_from_response_headers(response)
        if self._create_response_files:
            path = write_file_response("output/responses/", filename, content)
            printyellow(f"\nView downloaded file at: ./{path}")

        return content, filename

    def abort_task(self, task_id):
        """
        Aborts a specific task.

        :param task_id: The ID of the task to abort.
        :return: A success message.
        """
        url = self._make_api_url(f"api/tasks/{task_id}/abort")
        response = requests.patch(url)
        self._raise_for_status(response)
        response_data = response.json()
        self._write_json("abort_task", response_data)  # Call write_json with method name
        return response_data

    def delete_task(self, task_id):
        """
        Deletes a specific task.

        :param task_id: The ID of the task to delete.
        :return: A success message.
        """
        url = self._make_api_url(f"api/tasks/{task_id}")
        response = requests.delete(url)
        self._raise_for_status(response)
        response_data = response.json()
        self._write_json("delete_task", response_data)  # Call write_json with method name
        return response_data

    def delete_tasks(self, *task_ids):
        """
        Bulk deletes tasks.

        :param task_ids: A list of task IDs to be deleted.
        :return: A success message.
        """
        url = self._make_api_url("api/tasks/bulk-delete")
        payload = {"task_ids": task_ids}
        response = requests.post(url, json=payload)
        self._raise_for_status(response)
        response_data = response.json()
        self._write_json("delete_tasks", response_data)  # Call write_json with method name
        return response_data

    def abort_tasks(self, *task_ids):
        """
        Bulk aborts tasks.

        :param task_ids: A list of task IDs to be aborted.
        :return: A success message.
        """
        url = self._make_api_url("api/tasks/bulk-abort")
        payload = {"task_ids": task_ids}
        response = requests.post(url, json=payload)
        self._raise_for_status(response)
        response_data = response.json()
        self._write_json("abort_tasks", response_data)  # Call write_json with method name
        return response_data
