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


def get_length_no_whitespace(code):
    return sum([
        len("".join(line.split())) for line in code
    ])

def get_length_no_whitespace_no_comments(code):
    length = 0
    for line in code:
        if "#" in line:
            length += get_length_no_whitespace(line.split("#")[0])
        else:
            length += get_length_no_whitespace(line)
    return length