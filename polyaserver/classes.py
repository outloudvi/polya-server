import config

import persistent
import os
import yaml

class Student(persistent.Persistent):
    def __init__(self, student_id):
        filename = os.path.join(config.SUBMISSION_DIR, student_id, "init.yml")
        try:
            with open(filename) as fp:
                content = yaml.load(fp, Loader=yaml.BaseLoader)
        except Exception as es:
            print("Failed reading {}: {}".format(student_id, es))
            self.valid = False
            return
        self.student_id: str = student_id
        self.build_shell: str = content["build_shell"] or ""
        self.run_shell: str = content["run_shell"] or ""
        self.notification: str = content["notification"] or ""
        self.valid = True