from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class BaseProvider(ABC):
    @abstractmethod
    def decide(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]]
    ) -> Tuple[str, Any]:
        pass
