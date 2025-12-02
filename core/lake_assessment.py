"""
Lake Assessment Module - Multi-Year Trend Analysis
Automatically performs trend analysis when 3+ reports from the same lake are submitted
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class LakeAssessment:
    """Performs multi-year trend analysis for lake data"""
    
    def __init__(self):
        self.minimum_reports_for_trends = 3
        
    def extract_lake_name_and_year(self, doc_data: Dict) -> Tuple[Optional[str], Optional[int]]:
        """
        Extract lake name and year from document data
        
        Args:
            doc_data: Document analysis data
            
        Returns:
            Tuple of (lake_name, year) or (None, None) if not found
        """
        filename = doc_data.get('filename', '')
        text = doc_data.get('text', '')
        
        # Try to extract from filename first
        lake_name = None
        year = None
        
        # Common lake name patterns in filename
        lake_patterns = [
            r'(\w+\s+Lake)',  # "Austin Lake"
            r'Lake\s+(\w+)',  # "Lake Michigan"
            r'(\w+)\s+Lake',  # "Paradise Lake"
            r'(Lake\s+\w+)',  # "Lake Monticello"
        ]
        
        for pattern in lake_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                lake_name = match.group(0).strip()
                break
        
        # If not in filename, try document text (first 2000 chars for better coverage)
        if not lake_name and text:
            for pattern in lake_patterns:
                match = re.search(pattern, text[:2000], re.IGNORECASE)
                if match:
                    lake_name = match.group(0).strip()
                    break
        
        # Fallback: Use the project/organization name from filename
        # Handles cases like "PLEON_TWCWC_2021_report.pdf"
        if not lake_name:
            # Try to extract a project identifier from filename
            # Remove year, "report", "final", etc. and use what's left
            clean_filename = filename.replace('.pdf', '').replace('.PDF', '')
            
            # Remove common suffixes
            for suffix in ['_report', '_final', '_FINAL', ' report', ' Report', '_Report', 
                          '(1)', '(2)', '(3)', '_copy', ' copy', ' Copy', '-Copy']:
                clean_filename = clean_filename.replace(suffix, '')
            
            # Remove year patterns
            clean_filename = re.sub(r'_?\d{4}_?', '_', clean_filename)
            clean_filename = re.sub(r'_+', '_', clean_filename)  # Collapse multiple underscores
            clean_filename = clean_filename.strip('_- ')
            
            if clean_filename and len(clean_filename) > 2:
                # Use the cleaned filename as the lake/project identifier
                lake_name = clean_filename.replace('_', ' ').strip()
                logger.info(f"Using fallback lake name from filename: {lake_name}")
        
        # Extract year from filename or text
        year_patterns = [
            r'(20\d{2})',  # 2000-2099
            r'(19\d{2})',  # 1900-1999
        ]
        
        # Try filename first - look for 4-digit years
        for pattern in year_patterns:
            matches = re.findall(pattern, filename)
            if matches:
                # Take the most recent year if multiple found
                year = max(int(y) for y in matches)
                break
        
        # If no 4-digit year found, try date formats like MMDDYY (071620 = July 16, 2020)
        if not year:
            # Pattern for MMDDYY format (6 digits)
            date_match = re.search(r'(\d{2})(\d{2})(\d{2})', filename)
            if date_match:
                mm, dd, yy = date_match.groups()
                # Convert 2-digit year to 4-digit
                yy_int = int(yy)
                if yy_int >= 0 and yy_int <= 30:
                    year = 2000 + yy_int  # 00-30 -> 2000-2030
                elif yy_int > 30 and yy_int <= 99:
                    year = 1900 + yy_int  # 31-99 -> 1931-1999
        
        # If not in filename, check document text
        if not year and text:
            # Look for report date, monitoring year, etc.
            date_contexts = [
                r'Report\s+Date[:\s]+.*?(20\d{2}|19\d{2})',
                r'Monitoring\s+Year[:\s]+.*?(20\d{2}|19\d{2})',
                r'Data\s+from[:\s]+.*?(20\d{2}|19\d{2})',
                r'Annual\s+Report\s+(20\d{2}|19\d{2})',
                r'(20\d{2})',  # Fallback: any 4-digit year in text
            ]
            
            for pattern in date_contexts:
                match = re.search(pattern, text[:2000], re.IGNORECASE)
                if match:
                    year = int(match.group(1))
                    break
        
        # Final fallback: use current year if still no year found
        if not year:
            logger.warning(f"Could not extract year from {filename}, using None")
        
        return lake_name, year
    
    def group_reports_by_lake(self, reports: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group multiple reports by lake name
        
        Args:
            reports: List of analyzed report data
            
        Returns:
            Dictionary mapping lake names to lists of reports
        """
        lake_groups = {}
        
        for report in reports:
            lake_name, year = self.extract_lake_name_and_year(report)
            
            if lake_name:
                # Normalize lake name for grouping
                normalized_name = lake_name.lower().strip()
                
                if normalized_name not in lake_groups:
                    lake_groups[normalized_name] = []
                
                report['extracted_year'] = year
                report['lake_name'] = lake_name
                lake_groups[normalized_name].append(report)
        
        # Sort each group by year (handle None values)
        for lake_name in lake_groups:
            lake_groups[lake_name].sort(key=lambda x: x.get('extracted_year') or 0)
        
        return lake_groups
    
    def analyze_parameter_trends(self, reports: List[Dict]) -> Dict:
        """
        Analyze trends in key parameters over time
        
        Args:
            reports: List of reports for the same lake, sorted by year
            
        Returns:
            Dictionary containing trend analysis results
        """
        trends = {
            'years': [],
            'parameters': {},
            'overall_trajectory': None,
            'key_findings': [],
            'recommendations': []
        }
        
        # Extract years
        years = [r.get('extracted_year') for r in reports if r.get('extracted_year')]
        trends['years'] = years
        
        if len(years) < self.minimum_reports_for_trends:
            trends['overall_trajectory'] = 'Insufficient data for trend analysis'
            return trends
        
        # Key parameters to track
        parameters_to_track = [
            'dissolved_oxygen_min',
            'hypoxic_volume',
            'hypoxic_percentage',
            'orthophosphate_max',
            'ammonia_max',
            'cyanobacteria_percentage',
            'compliance_score'
        ]
        
        for param in parameters_to_track:
            values = []
            for report in reports:
                metrics = report.get('metrics', {})
                compliance = report.get('compliance_evaluation', {})
                
                if param == 'compliance_score':
                    value = compliance.get('overall_score')
                else:
                    value = metrics.get(param)
                
                if value is not None:
                    values.append(float(value))
                else:
                    values.append(None)
            
            if any(v is not None for v in values):
                trends['parameters'][param] = self._calculate_trend(years, values)
        
        # Determine overall trajectory
        trends['overall_trajectory'] = self._determine_overall_trajectory(trends['parameters'])
        
        # Generate key findings
        trends['key_findings'] = self._generate_key_findings(trends['parameters'])
        
        # Generate recommendations
        trends['recommendations'] = self._generate_trend_recommendations(trends['parameters'])
        
        return trends
    
    def _calculate_trend(self, years: List[int], values: List[Optional[float]]) -> Dict:
        """
        Calculate trend statistics for a parameter
        
        Args:
            years: List of years
            values: List of values (may contain None)
            
        Returns:
            Dictionary with trend statistics
        """
        # Remove None values
        clean_data = [(y, v) for y, v in zip(years, values) if v is not None]
        
        if len(clean_data) < 2:
            return {
                'trend': 'insufficient_data',
                'direction': None,
                'change_rate': None,
                'values': values
            }
        
        years_clean, values_clean = zip(*clean_data)
        
        # Calculate linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(years_clean, values_clean)
        
        # Determine trend direction
        if p_value < 0.05:  # Statistically significant
            if abs(slope) < 0.01:
                direction = 'stable'
            elif slope > 0:
                direction = 'increasing'
            else:
                direction = 'decreasing'
        else:
            direction = 'no_clear_trend'
        
        # Calculate percentage change
        if values_clean[0] != 0:
            total_change = ((values_clean[-1] - values_clean[0]) / abs(values_clean[0])) * 100
        else:
            total_change = None
        
        return {
            'trend': 'analyzed',
            'direction': direction,
            'slope': slope,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'change_rate': total_change,
            'first_value': values_clean[0],
            'last_value': values_clean[-1],
            'values': values
        }
    
    def _determine_overall_trajectory(self, parameter_trends: Dict) -> str:
        """
        Determine overall lake trajectory based on parameter trends
        
        Args:
            parameter_trends: Dictionary of parameter trend analyses
            
        Returns:
            String describing overall trajectory
        """
        critical_params = ['dissolved_oxygen_min', 'hypoxic_volume', 'cyanobacteria_percentage']
        
        improving = 0
        degrading = 0
        stable = 0
        
        for param, trend_data in parameter_trends.items():
            if trend_data.get('direction'):
                # Determine if trend is good or bad based on parameter
                if param in ['dissolved_oxygen_min', 'compliance_score']:
                    # Higher is better
                    if trend_data['direction'] == 'increasing':
                        improving += 1
                    elif trend_data['direction'] == 'decreasing':
                        degrading += 1
                    else:
                        stable += 1
                elif param in ['hypoxic_volume', 'hypoxic_percentage', 'orthophosphate_max', 
                             'ammonia_max', 'cyanobacteria_percentage']:
                    # Lower is better
                    if trend_data['direction'] == 'decreasing':
                        improving += 1
                    elif trend_data['direction'] == 'increasing':
                        degrading += 1
                    else:
                        stable += 1
        
        # Determine overall trajectory
        if degrading > improving:
            if degrading >= 3:
                return "Significant Degradation - Immediate Action Required"
            else:
                return "Gradual Degradation - Intervention Recommended"
        elif improving > degrading:
            if improving >= 3:
                return "Significant Improvement - Continue Current Management"
            else:
                return "Gradual Improvement - Maintain Efforts"
        else:
            return "Stable - Monitor Closely for Changes"
    
    def _generate_key_findings(self, parameter_trends: Dict) -> List[str]:
        """
        Generate key findings from trend analysis
        
        Args:
            parameter_trends: Dictionary of parameter trend analyses
            
        Returns:
            List of key finding strings
        """
        findings = []
        
        for param, trend in parameter_trends.items():
            if trend.get('direction') and trend['direction'] != 'no_clear_trend':
                # Format parameter name
                param_name = param.replace('_', ' ').title()
                
                # Generate finding based on trend
                if trend['direction'] == 'increasing':
                    if trend.get('change_rate'):
                        findings.append(f"{param_name} has increased by {abs(trend['change_rate']):.1f}% over the monitoring period")
                    else:
                        findings.append(f"{param_name} shows an increasing trend")
                elif trend['direction'] == 'decreasing':
                    if trend.get('change_rate'):
                        findings.append(f"{param_name} has decreased by {abs(trend['change_rate']):.1f}% over the monitoring period")
                    else:
                        findings.append(f"{param_name} shows a decreasing trend")
                elif trend['direction'] == 'stable':
                    findings.append(f"{param_name} has remained relatively stable")
        
        return findings[:5]  # Top 5 findings
    
    def _generate_trend_recommendations(self, parameter_trends: Dict) -> List[str]:
        """
        Generate recommendations based on trend analysis
        
        Args:
            parameter_trends: Dictionary of parameter trend analyses
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check hypoxia trends
        if 'hypoxic_volume' in parameter_trends:
            trend = parameter_trends['hypoxic_volume']
            if trend.get('direction') == 'increasing':
                recommendations.append("Hypoxic volume is increasing - implement aeration or nutrient reduction strategies immediately")
            elif trend.get('direction') == 'decreasing':
                recommendations.append("Hypoxic volume is decreasing - continue current management practices")
        
        # Check DO trends
        if 'dissolved_oxygen_min' in parameter_trends:
            trend = parameter_trends['dissolved_oxygen_min']
            if trend.get('direction') == 'decreasing':
                recommendations.append("Dissolved oxygen is declining - investigate causes and consider intervention")
        
        # Check nutrient trends
        nutrients_increasing = False
        for param in ['orthophosphate_max', 'ammonia_max']:
            if param in parameter_trends:
                if parameter_trends[param].get('direction') == 'increasing':
                    nutrients_increasing = True
                    break
        
        if nutrients_increasing:
            recommendations.append("Nutrient levels are increasing - review watershed management and implement source controls")
        
        # Check cyanobacteria trends
        if 'cyanobacteria_percentage' in parameter_trends:
            trend = parameter_trends['cyanobacteria_percentage']
            if trend.get('direction') == 'increasing':
                recommendations.append("Cyanobacteria dominance is increasing - high HAB risk, implement mitigation measures")
        
        # Add general recommendation
        if not recommendations:
            recommendations.append("Continue regular monitoring and maintain current management practices")
        
        return recommendations[:4]  # Top 4 recommendations
    
    def should_perform_assessment(self, reports: List[Dict]) -> bool:
        """
        Determine if Lake Assessment should be performed
        
        Args:
            reports: List of uploaded report analyses
            
        Returns:
            True if assessment should be performed
        """
        # Group reports by lake
        lake_groups = self.group_reports_by_lake(reports)
        
        # Check if any lake has enough reports for trend analysis
        for lake_name, lake_reports in lake_groups.items():
            if len(lake_reports) >= self.minimum_reports_for_trends:
                # Check if reports span multiple years
                years = [r.get('extracted_year') for r in lake_reports if r.get('extracted_year')]
                if len(set(years)) >= self.minimum_reports_for_trends:
                    return True
        
        return False
    
    def perform_assessment(self, reports: List[Dict]) -> Dict[str, Dict]:
        """
        Perform Lake Assessment on multiple reports
        
        Args:
            reports: List of analyzed report data
            
        Returns:
            Dictionary mapping lake names to assessment results
        """
        assessments = {}
        
        # Group reports by lake
        lake_groups = self.group_reports_by_lake(reports)
        
        for lake_name, lake_reports in lake_groups.items():
            # Check if we have enough reports
            years = [r.get('extracted_year') for r in lake_reports if r.get('extracted_year')]
            
            if len(set(years)) >= self.minimum_reports_for_trends:
                logger.info(f"Performing Lake Assessment for {lake_name} with {len(lake_reports)} reports")
                
                assessment = {
                    'lake_name': lake_reports[0].get('lake_name', lake_name),
                    'reports_analyzed': len(lake_reports),
                    'year_range': f"{min(years)} - {max(years)}",
                    'trend_analysis': self.analyze_parameter_trends(lake_reports),
                    'individual_reports': lake_reports
                }
                
                assessments[lake_name] = assessment
            else:
                logger.info(f"Insufficient data for Lake Assessment of {lake_name}: only {len(set(years))} years available")
        
        return assessments
