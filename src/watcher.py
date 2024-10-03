import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.utils import printyellow


class Watcher:
    DIRECTORY_TO_WATCH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output', 'responses'))

    def __init__(self, filename):
        self.observer = Observer()
        self.filename = filename

    def run(self):
        # Ensure the directory exists, if not create it
        if not os.path.exists(self.DIRECTORY_TO_WATCH):
            os.makedirs(self.DIRECTORY_TO_WATCH)
            printyellow(f"Created directory: {self.DIRECTORY_TO_WATCH}")

        event_handler = Handler(self.filename)
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):

    def __init__(self, filename):
        self.filename = filename

    def process(self, event):
        """
        Process the file change event.
        """
        # We check if the modified file is the one we care about
        if not event.is_directory and event.src_path.endswith(self.filename):
            printyellow(f"File {self.filename} has been modified.")
            # Perform actions such as reading the file, updating database, etc.
            self.handle_file_change(event.src_path)

    @staticmethod
    def handle_file_change(file_path):
        """
        Your logic to handle the file change.
        """
        printyellow(f"Handling change for {file_path}")
        # Implement what to do with the file, e.g., read its contents, process the data, etc.
        with open(file_path, 'r') as f:
            data = f.read()
            printyellow(f"Contents of {file_path}: {data}")

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


if __name__ == '__main__':
    filename_to_watch = "all-task-1.json"
    w = Watcher(filename_to_watch)
    w.run()
