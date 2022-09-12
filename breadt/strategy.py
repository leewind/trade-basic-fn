import abc


class Strategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def monitor(self) -> None:
        pass
