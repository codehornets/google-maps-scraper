API Integration

The Botasaurus API client provides a convenient way to access the Scraper via an API.

It provides a simple and convenient way to create, fetch, download, abort, and delete tasks, as well as manage their results.

Usage First, import the Api class from the library:

from botasaurus_api import Api

Then, create an instance of the Api class:

api = Api()

Additionally, the API client will create response JSON files in the output/responses/ directory to help with debugging and development. If you want to disable this feature in production, you can set create_response_files=False.

api = Api(create_response_files=False)

Creating Tasks
There are two types of tasks:

Asynchronous Task
Synchronous Task
Asynchronous tasks run asynchronously, without waiting for the task to be completed. The server will return a response immediately, containing information about the task, but not the actual results. The client can then retrieve the results later.

Synchronous tasks, on the other hand, wait for the completion of the task. The server response will contain the results of the task.

You should use asynchronous tasks when you want to run a task in the background and retrieve the results later. Synchronous tasks are better suited for scenarios where you have a small number of tasks and want to wait and get the results immediately.

To create an asynchronous task, use the create_async_task method:

data = {
    'queries': ['Web Developers in Bangalore'],
    'country': None,
    'business_type': '',
    'max_cities': None,
    'randomize_cities': True,
    'api_key': '',
    'enable_reviews_extraction': False,
    'max_reviews': 20,
    'reviews_sort': 'newest',
    'lang': None,
    'max_results': None,
    'coordinates': '',
    'zoom_level': 14,
}
task = api.create_async_task(scraper_name='google_maps_scraper', data)

To create a synchronous task, use the create_sync_task method:

data = {
    'queries': ['Web Developers in Bangalore'],
    'country': None,
    'business_type': '',
    'max_cities': None,
    'randomize_cities': True,
    'api_key': '',
    'enable_reviews_extraction': False,
    'max_reviews': 20,
    'reviews_sort': 'newest',
    'lang': None,
    'max_results': None,
    'coordinates': '',
    'zoom_level': 14,
}
task = api.create_sync_task(scraper_name='google_maps_scraper', data)

You can create multiple asynchronous or synchronous tasks at once using the create_async_tasks and create_sync_tasks methods, respectively:

data_items = [
    {
        'queries': ['Web Developers in Bangalore'],
        'country': None,
        'business_type': '',
        'max_cities': None,
        'randomize_cities': True,
        'api_key': '',
        'enable_reviews_extraction': False,
        'max_reviews': 20,
        'reviews_sort': 'newest',
        'lang': None,
        'max_results': None,
        'coordinates': '',
        'zoom_level': 14,
    },
    {
        'queries': ['Web Developers in Bangalore'],
        'country': None,
        'business_type': '',
        'max_cities': None,
        'randomize_cities': True,
        'api_key': '',
        'enable_reviews_extraction': False,
        'max_reviews': 20,
        'reviews_sort': 'newest',
        'lang': None,
        'max_results': None,
        'coordinates': '',
        'zoom_level': 14,
    },
]
tasks = api.create_async_tasks(scraper_name='google_maps_scraper', data_items)
tasks = api.create_sync_tasks(scraper_name='google_maps_scraper', data_items)

Fetching Tasks
To fetch tasks from the server, use the get_tasks method:

tasks = api.get_tasks()

By default, all tasks are returned. You can also apply pagination, views, filters or sorts:

results = api.get_task_results(
    task_id=1,
    page=1,
    per_page=20,
    view=None,  # view can be one of: overview, featured_reviews or detailed_reviews
    sort=None,  # sort can be one of: no_sort, best_potential_customers_sort (default), reviews_numeric_descending_sort, reviews_numeric_ascending_sort or name_numeric_ascending_sort
    filters={
        # 'reviews_min_number_input': 0, # Enter a number
        # 'reviews_max_number_input': 0, # Enter a number
        # 'website_bool_select_dropdown': 'your-option', # Can be one of the following options: no or yes
        # 'phone_is_truthy_checkbox': True, # Must be True Only
        # 'is_spending_on_ads_is_true_checkbox': True, # Must be True Only
        # 'can_claim_bool_select_dropdown': 'your-option', # Can be one of the following options: yes or no
        # 'is_temporarily_closed_bool_select_dropdown': 'your-option', # Can be one of the following options: yes or no
        # 'categories_multi_select_dropdown': ['your-option-1', 'your-option-2'], # Can be any among 4011 options: abbey, accountant, acupuncturist, aeroclub, airline, airport, airstrip, allergist, amphitheatre, anesthesiologist, ...
        # 'rating_min_number_input': 0, # Enter a number
    }
)

To fetch a specific task by its ID, use the get_task method:

task = api.get_task(task_id=1)

Fetching Task Results
To fetch the results of a specific task, use the get_task_results method:

results = api.get_task_results(task_id=1)

You can also apply pagination, views, filters or sorts:

results = api.get_task_results(
    task_id=1,
    page=1,
    per_page=20,
    view=None,  # view can be one of: overview, featured_reviews or detailed_reviews
    sort=None,  # sort can be one of: no_sort, best_potential_customers_sort (default), reviews_numeric_descending_sort, reviews_numeric_ascending_sort or name_numeric_ascending_sort
    filters={
        # 'reviews_min_number_input': 0, # Enter a number
        # 'reviews_max_number_input': 0, # Enter a number
        # 'website_bool_select_dropdown': 'your-option', # Can be one of the following options: no or yes
        # 'phone_is_truthy_checkbox': True, # Must be True Only
        # 'is_spending_on_ads_is_true_checkbox': True, # Must be True Only
        # 'can_claim_bool_select_dropdown': 'your-option', # Can be one of the following options: yes or no
        # 'is_temporarily_closed_bool_select_dropdown': 'your-option', # Can be one of the following options: yes or no
        # 'categories_multi_select_dropdown': ['your-option-1', 'your-option-2'], # Can be any among 4011 options: abbey, accountant, acupuncturist, aeroclub, airline, airport, airstrip, allergist, amphitheatre, anesthesiologist, ...
        # 'rating_min_number_input': 0, # Enter a number
    }
)

Downloading Task Results
To download the results of a specific task in a particular format, use the download_task_results method:

results_bytes, filename = api.download_task_results(task_id=1, format='csv')
with open(filename, 'wb') as file:
    file.write(results_bytes)

You can also apply views, filters or sorts:

results_bytes, filename = api.download_task_results(
    task_id=1,
    format='excel',  # format can be one of: json, csv or excel
    view=None,  # view can be one of: overview, featured_reviews or detailed_reviews
    sort=None,  # sort can be one of: no_sort, best_potential_customers_sort (default), reviews_numeric_descending_sort, reviews_numeric_ascending_sort or name_numeric_ascending_sort
    filters={
        # 'reviews_min_number_input': 0, # Enter a number
        # 'reviews_max_number_input': 0, # Enter a number
        # 'website_bool_select_dropdown': 'your-option', # Can be one of the following options: no or yes
        # 'phone_is_truthy_checkbox': True, # Must be True Only
        # 'is_spending_on_ads_is_true_checkbox': True, # Must be True Only
        # 'can_claim_bool_select_dropdown': 'your-option', # Can be one of the following options: yes or no
        # 'is_temporarily_closed_bool_select_dropdown': 'your-option', # Can be one of the following options: yes or no
        # 'categories_multi_select_dropdown': ['your-option-1', 'your-option-2'], # Can be any among 4011 options: abbey, accountant, acupuncturist, aeroclub, airline, airport, airstrip, allergist, amphitheatre, anesthesiologist, ...
        # 'rating_min_number_input': 0, # Enter a number
    }
)

Aborting and Deleting Tasks
To abort a specific task, use the abort_task method:

api.abort_task(task_id=1)

To delete a specific task, use the delete_task method:

api.delete_task(task_id=1)

You can also bulk abort or delete multiple tasks at once using the abort_tasks and delete_tasks methods, respectively:

api.abort_tasks(1, 2, 3)
api.delete_tasks(4, 5, 6)

Examples
Here are some example usages of the API client:

from botasaurus_api import Api

# Create an instance of the API client
api = Api()

# Create an asynchronous task
data = {
    'queries': ['Web Developers in Bangalore'],
    'country': None,
    'business_type': '',
    'max_cities': None,
    'randomize_cities': True,
    'api_key': '',
    'enable_reviews_extraction': False,
    'max_reviews': 20,
    'reviews_sort': 'newest',
    'lang': None,
    'max_results': None,
    'coordinates': '',
    'zoom_level': 14,
}
task = api.create_sync_task(data, scraper_name='google_maps_scraper')

# Fetch the task
task = api.get_task(task['id'])

# Fetch the task results
results = api.get_task_results(task['id'])

# Download the task results as a CSV
results_bytes, filename = api.download_task_results(task['id'], format='csv')

# Abort the task
api.abort_task(task['id'])

# Delete the task
api.delete_task(task['id'])

# --- Bulk Operations ---

# Create multiple synchronous tasks
data_items = [
    {
        'queries': ['Web Developers in Bangalore'],
        'country': None,
        'business_type': '',
        'max_cities': None,
        'randomize_cities': True,
        'api_key': '',
        'enable_reviews_extraction': False,
        'max_reviews': 20,
        'reviews_sort': 'newest',
        'lang': None,
        'max_results': None,
        'coordinates': '',
        'zoom_level': 14,
    },
    {
        'queries': ['Web Developers in Bangalore'],
        'country': None,
        'business_type': '',
        'max_cities': None,
        'randomize_cities': True,
        'api_key': '',
        'enable_reviews_extraction': False,
        'max_reviews': 20,
        'reviews_sort': 'newest',
        'lang': None,
        'max_results': None,
        'coordinates': '',
        'zoom_level': 14,
    },
]
tasks = api.create_sync_tasks(data_items, scraper_name='google_maps_scraper')

# Fetch all tasks
all_tasks = api.get_tasks()

# Bulk abort tasks
api.abort_tasks(*[task['id'] for task in tasks])

# Bulk delete tasks
api.delete_tasks(*[task['id'] for task in tasks])

That's It!
Now, go and build something awesome.