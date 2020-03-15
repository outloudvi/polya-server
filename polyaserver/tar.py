import tempfile
import tarfile
import os

def get_tar_result(path):
    f = tempfile.NamedTemporaryFile()
    tar = tarfile.open(f.name, "w")
    if os.path.isfile(path):
        # For regular file, just add it
        paths = path.split("/")
        tar.add(path, paths[-1])
    elif os.path.isdir(path):
        # For directory, add everything inside
        for item in os.listdir(path):
            tar.add(os.path.join(path, item), item)
    tar.close()
    return f