"""Excel Exporter for WhatsApp Extractor v2"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available - Excel export will be limited")

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not available - Excel formatting will be limited")


class ExcelExporter:
    """Export WhatsApp data to Excel format"""
    
    def __init__(self):
        self.default_fields = [
            'contact_name',
            'message_id',
            'timestamp', 
            'direction',
            'message_type',
            'content',
            'transcription',
            'media_path',
            'media_type',
            'file_size'
        ]
    
    def export(self, data: List[Dict[str, Any]], output_path: Path,
               fields: Optional[List[str]] = None) -> bool:
        """
        Export data to Excel file
        
        Args:
            data: List of message dictionaries
            output_path: Path where to save Excel file  
            fields: List of field names to include
            
        Returns:
            bool: True if export successful
        """
        try:
            if not data:
                logger.warning("No data to export")
                return False
                
            # Use default fields if none specified
            if fields is None:
                fields = self.default_fields
                
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if PANDAS_AVAILABLE:
                return self._export_with_pandas(data, output_path, fields)
            else:
                return self._export_manual(data, output_path, fields)
                
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return False
            
    def _export_with_pandas(self, data: List[Dict[str, Any]], output_path: Path,
                           fields: List[str]) -> bool:
        """Export using pandas (preferred method)"""
        try:
            # Clean data for pandas
            cleaned_data = []
            for row in data:
                cleaned_row = {}
                for field in fields:
                    value = row.get(field, '')
                    
                    # Handle special data types
                    if isinstance(value, dict) or isinstance(value, list):
                        value = json.dumps(value, ensure_ascii=False)
                    elif value is None:
                        value = ''
                        
                    cleaned_row[field] = value
                    
                cleaned_data.append(cleaned_row)
                
            # Create DataFrame
            df = pd.DataFrame(cleaned_data)
            
            # Export to Excel
            with pd.ExcelWriter(output_path, engine='openpyxl' if OPENPYXL_AVAILABLE else 'xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Messages', index=False)
                
                # Add formatting if openpyxl available
                if OPENPYXL_AVAILABLE:
                    workbook = writer.book
                    worksheet = writer.sheets['Messages']
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                                
                        adjusted_width = min(max_length + 2, 50)  # Max width 50
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                        
            logger.info(f"Excel export successful: {output_path} ({len(data)} rows)")
            return True
            
        except Exception as e:
            logger.error(f"Pandas Excel export failed: {e}")
            return False
            
    def _export_manual(self, data: List[Dict[str, Any]], output_path: Path,
                      fields: List[str]) -> bool:
        """Manual export without pandas (fallback)"""
        try:
            # Create a simple CSV-like structure that Excel can read
            import csv
            
            # Change extension to .csv for compatibility
            csv_path = output_path.with_suffix('.csv')
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                
                for row in data:
                    cleaned_row = {}
                    for field in fields:
                        value = row.get(field, '')
                        
                        if isinstance(value, dict) or isinstance(value, list):
                            value = json.dumps(value, ensure_ascii=False)
                        elif value is None:
                            value = ''
                        else:
                            value = str(value)
                            
                        cleaned_row[field] = value
                        
                    writer.writerow(cleaned_row)
                    
            logger.info(f"Manual Excel export (as CSV) successful: {csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"Manual Excel export failed: {e}")
            return False
            
    def export_multi_sheet(self, data_dict: Dict[str, List[Dict[str, Any]]], 
                          output_path: Path) -> bool:
        """Export multiple sheets to one Excel file"""
        try:
            if not PANDAS_AVAILABLE:
                logger.error("Multi-sheet export requires pandas")
                return False
                
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with pd.ExcelWriter(output_path, engine='openpyxl' if OPENPYXL_AVAILABLE else 'xlsxwriter') as writer:
                
                for sheet_name, sheet_data in data_dict.items():
                    if not sheet_data:
                        continue
                        
                    # Clean data
                    cleaned_data = []
                    for row in sheet_data:
                        cleaned_row = {}
                        for key, value in row.items():
                            if isinstance(value, dict) or isinstance(value, list):
                                value = json.dumps(value, ensure_ascii=False)
                            elif value is None:
                                value = ''
                            cleaned_row[key] = value
                        cleaned_data.append(cleaned_row)
                        
                    # Create DataFrame and export
                    df = pd.DataFrame(cleaned_data)
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)  # Excel sheet name limit
                    
            logger.info(f"Multi-sheet Excel export successful: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Multi-sheet Excel export failed: {e}")
            return False
            
    def get_dependencies_info(self) -> Dict[str, bool]:
        """Get information about available dependencies"""
        return {
            'pandas': PANDAS_AVAILABLE,
            'openpyxl': OPENPYXL_AVAILABLE,
            'excel_support': PANDAS_AVAILABLE or OPENPYXL_AVAILABLE
        }