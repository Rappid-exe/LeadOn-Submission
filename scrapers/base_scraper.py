"""Base scraper class for all scrapers"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search for contacts based on query"""
        pass
    
    @abstractmethod
    def get_contact_details(self, contact_id: str) -> Dict[str, Any]:
        """Get detailed information about a contact"""
        pass

