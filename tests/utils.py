import os
import shutil

from sparrow import ls


def rm(*file_pattern: str, rel=False):
    """Remove files or directories.
    Example:
    --------
        >>> rm("*.jpg", "*.png")
        >>> rm("*.jpg", "*.png", rel=True)
    """
    path_list = ls(".", *file_pattern, relp=rel, concat="extend")
    for file in path_list:
        if os.path.isfile(file):
            print("remove ", file)
            os.remove(file)
            # os.system("rm -f " + file)
        elif os.path.isdir(file):
            shutil.rmtree(file, ignore_errors=True)
            print("rm tree ", file)
