import abc


class Method:

    def __init__(self):
        pass


class DataTypeABC(abc.ABC):

    @staticmethod
    def get_name():
        pass

    @staticmethod
    def get_operations():
        pass

    @staticmethod
    def get_methods():
        pass
