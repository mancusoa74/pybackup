import yamale
from yamale.validators import DefaultValidators, Validator
import os


class Path(Validator):
    tag = 'path'

    def _is_valid(self, value):
        return os.path.isdir(value)


class File(Validator):
    tag = 'file'

    def _is_valid(self, value):
        try:
            if os.path.isfile(value):
                return True

            file = open(value, 'w')
            file.close()
            os.remove(value)
            return True
        except (FileNotFoundError, IsADirectoryError, TypeError):
            return False


class CustomValidators():
    def __init__(self):
        self._validators = DefaultValidators.copy()
        self._validators[Path.tag] = Path
        self._validators[File.tag] = File

    def get_validators(self):
        return self._validators
