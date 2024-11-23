import sys
import os

class suppress_output:
    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.null = open(os.devnull, "w")
        sys.stdout = self.null
        sys.stderr = self.null  # Redirect stderr as well

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.null.close()