from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class StorageInterface(ABC):
    
    @abstractmethod
    def save_state(self, key: str, value: Dict) -> bool:
        pass
    
    @abstractmethod
    def load_state(self, key: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def delete_state(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def save_artifact(self, artifact_id: str, content: Dict, checksum: str) -> bool:
        pass
    
    @abstractmethod
    def load_artifact(self, artifact_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def query_market_data(self, symbol: str, start: str, end: str) -> List[Dict]:
        pass
