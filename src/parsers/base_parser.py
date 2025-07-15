"""Abstract base parser interface"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..core.models import Contact, Message


class BaseParser(ABC):
    """Abstract base class for parsers"""
    
    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, List[Message]]:
        """
        Parse a file and extract messages grouped by contact
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary mapping contact identifiers to lists of messages
        """
        pass
    
    @abstractmethod
    def extract_contacts(self, file_path: Path) -> List[Contact]:
        """
        Extract unique contacts from a file
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            List of unique contacts found in the file
        """
        pass
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate if the file can be parsed by this parser
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if the file is valid for this parser
        """
        pass