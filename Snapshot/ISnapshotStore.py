from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class ISnapshotStore(ABC):
    @abstractmethod
    def save_snapshot(self, node_id: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def load_snapshot(self, node_id: str) -> Optional[Dict[str, Any]]:
        pass
