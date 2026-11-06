from abc import ABC, abstractmethod

class BaseBot(ABC):
    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def run(self, headless=True):
        pass