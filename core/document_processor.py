"""
Enhanced document processor for diverse PDF formats
"""
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
from typing import Dict, List, Any, Optional
import re
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process diverse PDF formats and extract structured data"""
    
    def __init__(self):
        self.text_cache = {}
        
    async def process_document(self, file_path: str, use_ocr: bool = False) -> Dict[str, Any]:
        """
        Main processing pipeline for documents
        
        Args:
            file_path: Path to the PDF file
            use_ocr: Force OCR even if text is extractable
            
        Returns:
            Structured document data with text, tables, and metadata
        """
        logger.info(f"Processing document: {file_path}")
        
        result = {
            "file_path": file_path,
            "filename": Path(file_path).name,
            "page_count": 0,
            "text_content": "",
            "tables": [],
            "metadata": {},
            "extraction_method": "",
            "parameters_found": {},
            "has_text": False,
            "has_tables": False,
            "has_images": False
        }
        
        try:
            # First try standard text extraction
            doc = fitz.open(file_path)
            result["page_count"] = len(doc)
            
            # Check document structure
            for page_num, page in enumerate(doc):
                # Check for images
                if page.get_images():
                    result["has_images"] = True
                
                # Extract text
                text = page.get_text()
                if text.strip():
                    result["has_text"] = True
                    result["text_content"] += text + "\n"
            
            doc.close()
            
            # If no text found or OCR forced, use OCR
            if not result["text_content"].strip() or use_ocr:
                logger.info("Using OCR for text extraction")
                result["text_content"] = await self._extract_with_ocr(file_path)
                result["extraction_method"] = "OCR"
            else:
                result["extraction_method"] = "PyMuPDF"
            
            # Extract tables
            result["tables"] = await self._extract_tables(file_path)
            if result["tables"]:
                result["has_tables"] = True
            
            # Identify parameters mentioned
            result["parameters_found"] = self._identify_parameters(result["text_content"])
            
            # Extract key metrics if found
            result["metrics"] = self._extract_metrics(result["text_content"])
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _extract_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR for scanned PDFs"""
        try:
            # Convert PDF to images
            images = convert_from_path(file_path, dpi=300, first_page=1, last_page=5)  # First 5 pages for speed
            
            text = ""
            for i, image in enumerate(images):
                # Use pytesseract to extract text
                page_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n{page_text}"
            
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    async def _extract_tables(self, file_path: str) -> List[Dict]:
        """Extract tables from PDF"""
        tables = []
        try:
            import camelot
            # Try to extract tables using camelot
            extracted_tables = camelot.read_pdf(file_path, pages='1-5', flavor='stream')
            
            for i, table in enumerate(extracted_tables):
                tables.append({
                    "table_id": i,
                    "data": table.df.to_dict(),
                    "accuracy": table.accuracy
                })
        except Exception as e:
            logger.warning(f"Table extraction failed with camelot: {e}")
            # Fallback to regex-based table detection
            tables = self._extract_tables_regex(file_path)
        
        return tables
    
    def _extract_tables_regex(self, file_path: str) -> List[Dict]:
        """Fallback table extraction using regex patterns"""
        tables = []
        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc[:5]):  # First 5 pages
                text = page.get_text()
                # Look for table-like patterns (multiple tabs or pipes)
                lines = text.split('\n')
                potential_table = []
                
                for line in lines:
                    if '\t' in line or '|' in line or re.search(r'\s{2,}\S+\s{2,}', line):
                        potential_table.append(line)
                    elif potential_table and len(potential_table) > 2:
                        # Found a potential table
                        tables.append({
                            "table_id": f"page_{page_num}_{len(tables)}",
                            "raw_text": '\n'.join(potential_table)
                        })
                        potential_table = []
            doc.close()
        except Exception as e:
            logger.error(f"Regex table extraction failed: {e}")
        
        return tables
    
    def _identify_parameters(self, text: str) -> Dict[str, bool]:
        """Identify which parameters are mentioned in the document"""
        from config import COMPLIANCE_RULES
        
        text_lower = text.lower()
        parameters_found = {}
        
        # Check critical parameters
        for param_key, param_info in COMPLIANCE_RULES["parameters"]["critical_must_have"].items():
            search_terms = param_info.get("search_terms", [param_key.replace("_", " ")])
            found = any(term.lower() in text_lower for term in search_terms)
            parameters_found[f"critical_{param_key}"] = found
        
        # Check problematic parameters
        for param_key, param_info in COMPLIANCE_RULES["parameters"]["problematic_avoid"].items():
            search_terms = param_info.get("search_terms", [param_key.replace("_", " ")])
            found = any(term.lower() in text_lower for term in search_terms)
            parameters_found[f"problem_{param_key}"] = found
        
        # Check for critical calculations with better matching
        for calc_key, calc_info in COMPLIANCE_RULES["critical_calculations"].items():
            # More comprehensive search for calculations
            calc_terms = []
            
            # Add the key itself
            calc_terms.append(calc_key.replace("_", " "))
            
            # Add formula keywords
            formula = calc_info.get("formula", "")
            if formula:
                calc_terms.append(formula.lower())
            
            # Add specific keywords for each calculation type
            if "hypoxic" in calc_key:
                calc_terms.extend(["hypoxic volume", "anoxic volume", "volume of hypoxic", "hypoxic water volume"])
            if "percentage" in calc_key or "percent" in calc_key:
                calc_terms.extend(["percent", "%", "percentage"])
            if "area" in calc_key:
                calc_terms.extend(["sediment area", "bottom area", "benthic area"])
            
            # Check if any term is found
            found = any(term in text_lower for term in calc_terms if term)
            parameters_found[f"calc_{calc_key}"] = found
        
        return parameters_found
    
    def _extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extract specific metrics and values from text"""
        metrics = {}
        
        # Extract DO values
        do_pattern = r'(?:dissolved oxygen|DO|D\.O\.)[:\s]*([0-9]+\.?[0-9]*)\s*(?:mg/L|ppm)'
        do_matches = re.findall(do_pattern, text, re.IGNORECASE)
        if do_matches:
            metrics["dissolved_oxygen_values"] = [float(val) for val in do_matches[:5]]  # First 5 values
        
        # Extract depth measurements
        depth_pattern = r'(\d+\.?\d*)\s*(?:m|meters|feet|ft)\s*(?:depth|deep)'
        depth_matches = re.findall(depth_pattern, text, re.IGNORECASE)
        if depth_matches:
            metrics["depth_measurements"] = [float(val) for val in depth_matches[:5]]
        
        # Extract phosphorus values
        phos_pattern = r'(?:phosphorus|phosphate|PO4|TP)[:\s]*([0-9]+\.?[0-9]*)\s*(?:mg/L|µg/L|ppb)'
        phos_matches = re.findall(phos_pattern, text, re.IGNORECASE)
        if phos_matches:
            metrics["phosphorus_values"] = [float(val) for val in phos_matches[:5]]
        
        # Look for percentage calculations
        percent_pattern = r'(\d+\.?\d*)\s*%\s*(?:hypoxic|anoxic|oxygen|volume)'
        percent_matches = re.findall(percent_pattern, text, re.IGNORECASE)
        if percent_matches:
            metrics["percentage_calculations"] = [float(val) for val in percent_matches[:3]]
        
        return metrics

class ParameterMatcher:
    """Advanced parameter matching using semantic similarity"""
    
    def __init__(self):
        self.parameter_variations = {
            'dissolved_oxygen': [
                'dissolved oxygen', 'DO', 'D.O.', 'oxygen levels', 
                'oxygen concentration', 'oxygen content', 'O2'
            ],
            'hypoxia': [
                'hypoxia', 'hypoxic', 'anoxia', 'anoxic', 
                'oxygen depletion', 'low oxygen', 'oxygen deficient'
            ],
            'orthophosphate': [
                'orthophosphate', 'ortho-phosphate', 'SRP', 
                'soluble reactive phosphorus', 'PO4', 'phosphate'
            ],
            'ammonia': [
                'ammonia', 'NH3', 'NH4', 'ammonium', 
                'ammonia nitrogen', 'NH3-N', 'NH4-N'
            ],
            'chlorophyll_a': [
                'chlorophyll-a', 'chlorophyll a', 'chl-a', 
                'chla', 'chlorophyll', 'chl a'
            ],
            'phytoplankton': [
                'phytoplankton', 'algae', 'cyanobacteria', 
                'blue-green algae', 'plankton', 'diatoms'
            ],
            'bathymetry': [
                'bathymetry', 'bathymetric', 'depth contours', 
                'lake morphometry', 'depth map', 'bottom topography'
            ]
        }
    
    def find_parameters(self, text: str) -> Dict[str, List[str]]:
        """Find parameter mentions with their context"""
        text_lower = text.lower()
        found_parameters = {}
        
        for param, variations in self.parameter_variations.items():
            contexts = []
            for variation in variations:
                # Find variation with context (50 chars before and after)
                pattern = rf'.{{0,50}}{re.escape(variation.lower())}.{{0,50}}'
                matches = re.findall(pattern, text_lower)
                contexts.extend(matches)
            
            if contexts:
                found_parameters[param] = contexts[:3]  # Keep first 3 contexts
        
        return found_parameters
