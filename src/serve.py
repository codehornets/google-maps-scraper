import argparse
import atexit
import os
import subprocess
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify

from backend.api import Api, ApiException
from src.utils import printyellow, printred

app = Flask(__name__)

# Global variables
API_CHECK_RETRY_INTERVAL = 5  # Time between API server availability checks
MAX_API_CHECK_RETRIES = 10  # Number of times to check if API is up
API_SERVER_PROCESS = None
CLI_PAYLOAD = None

WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 5000))  # Ensure port is an integer
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
EXECUTOR = ThreadPoolExecutor(max_workers=5)


def start_api_server():
    """Starts the API server by calling run.py and checks if it's running."""
    global API_SERVER_PROCESS

    # Start the API server using subprocess
    printyellow("Starting the API server...")
    try:
        API_SERVER_PROCESS = subprocess.Popen(["python", "run.py", "backend", "--force"])
    except OSError as e:
        printred(f"Failed to start API server: {e}")
        return False

    # Create an instance of the API to check its availability
    api = Api()

    # Retry mechanism to check if API is running
    backoff_interval = 2
    for attempt in range(MAX_API_CHECK_RETRIES):
        try:
            # Check if API is running
            if api.is_api_running():
                printyellow("API server is up and running.")
                return True
        except ApiException:
            printyellow(f"Waiting for API to start... Attempt {attempt + 1}/{MAX_API_CHECK_RETRIES}")
            time.sleep(backoff_interval)
            backoff_interval *= 2  # Exponential backoff

    # If the server hasn't started within the retries, fail
    printred("Failed to start the API server after multiple attempts.")
    return False


def stop_api_server():
    """Stops the API server by terminating the process."""
    global API_SERVER_PROCESS
    if API_SERVER_PROCESS:
        printyellow("Stopping the API server...")
        API_SERVER_PROCESS.terminate()
        API_SERVER_PROCESS.wait(timeout=10)
        printyellow("API server stopped.")


def run_cli_task(data, scraper_name='google_maps_scraper'):
    """Runs the CLI to pass the payload and creates a task using the API."""
    api = Api()

    try:
        # Submit a new task to the API using the provided data
        task_list = api.create_task(data, scraper_name)
        task = task_list[0] if isinstance(task_list, list) and task_list else task_list

        # Fetch the task results
        task = api.get_task(task['id'])
        # printyellow(f'Fetched task: {task}')

        results = api.get_task_results(task['id'])
        # printyellow(f'Fetched task results: {results}')

        return {"task": task, "results": results}

    except ApiException as e:
        printred(f"API error: {e}")
        return {"error": str(e)}
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
        printred(error_message)
        return {"error": error_message}


def async_task(data):
    # Run the CLI task with the given data
    result = run_cli_task(data)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200


@app.route('/start-task', methods=['POST'])
def start_task():
    """Handles incoming POST requests to create a task."""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    # Start the task in a separate thread
    EXECUTOR.submit(async_task, data)
    return jsonify({"status": "Task started successfully"}), 200


def run_webhook_server():
    """Starts a Flask server to accept incoming POST requests."""
    printyellow(f"Starting webhook server on {WEBHOOK_HOST}:{WEBHOOK_PORT}...")
    app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT)


def validate_payload(payload):
    if 'queries' not in payload or not payload['queries']:
        raise ValueError("Queries are required for scraping.")


def run_orchestrator(webhook=False):
    """Main function to start the orchestrator."""
    try:
        # Start the API server and wait for it to be available
        if not start_api_server():
            return  # Exit if the API server could not start

        if webhook:
            # If webhook option is enabled, start the webhook server
            run_webhook_server()
        else:
            # Validate the payload
            validate_payload(CLI_PAYLOAD)

            # If webhook is not enabled, run the CLI manually with the provided payload
            data = {
                'queries': CLI_PAYLOAD['queries'].split(','),
                'country': CLI_PAYLOAD.get('country'),
                'business_type': CLI_PAYLOAD.get('business_type'),
                'max_cities': CLI_PAYLOAD.get('max_cities'),
                'randomize_cities': CLI_PAYLOAD.get('randomize_cities', True),
                'api_key': CLI_PAYLOAD.get('api_key'),
                'enable_reviews_extraction': CLI_PAYLOAD.get('enable_reviews_extraction', False),
                'max_reviews': CLI_PAYLOAD.get('max_reviews', 20),
                'reviews_sort': CLI_PAYLOAD.get('reviews_sort', 'newest'),
                'lang': CLI_PAYLOAD.get('lang'),
                'max_results': CLI_PAYLOAD.get('max_results'),
                'coordinates': CLI_PAYLOAD.get('coordinates'),
                'zoom_level': CLI_PAYLOAD.get('zoom_level', 14),
            }
            run_cli_task(data)
    finally:
        # Stop the API server once everything is done
        stop_api_server()

        # Ensure API server is stopped on exit
        atexit.register(stop_api_server)


if __name__ == "__main__":
    # Argument parser for orchestrator
    parser = argparse.ArgumentParser(description="Orchestrator for starting the API server and running CLI tasks")
    parser.add_argument('--webhook', action='store_true', help="Start webhook server to accept POST requests")
    parser.add_argument('--api-key', default='', help='API Key for Google Maps')
    parser.add_argument('--queries', default='Barbershop in Montreal', help='Queries, separated by commas')
    parser.add_argument('--country', default=None, help='Country for queries')
    parser.add_argument('--business-type', default='', help='Business type to scrape')
    parser.add_argument('--max-cities', default=None, help='Maximum number of cities')
    parser.add_argument('--randomize-cities', default=True, type=bool, help='Randomize city selection')
    parser.add_argument('--enable-reviews-extraction', default=False, type=bool, help='Enable reviews extraction')
    parser.add_argument('--max-reviews', default=20, type=int, help='Max number of reviews to scrape')
    parser.add_argument('--reviews-sort', default='newest', help='Sort order for reviews')
    parser.add_argument('--lang', default=None, help='Language for scraping')
    parser.add_argument('--max-results', default=None, help='Maximum results to fetch')
    parser.add_argument('--coordinates', default='', help='Coordinates for scraping')
    parser.add_argument('--zoom-level', default=14, type=int, help='Zoom level for map queries')

    args = parser.parse_args()

    # Prepare CLI payload if webhook is not enabled
    CLI_PAYLOAD = vars(args)

    # Run the orchestrator
    run_orchestrator(webhook=args.webhook)
