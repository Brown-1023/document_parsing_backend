"""
Load and manage 'Our Thinking' reference documents
As per Brief: "Our Thinking will be defined by several White Papers, e-Books"
"""
import json
from pathlib import Path
from typing import Dict, List

class OurThinkingManager:
    """Manages 'Our Thinking' reference documents"""
    
    # Define which documents represent "Our Thinking"
    OUR_THINKING_DOCUMENTS = [
        "Simplify the Science (Final version).pdf",
        "Measure What Matters (Final version).pdf", 
        "Lake Management Plan (Final version).pdf",
        "1 - THE RISK MANAGEMENT TRAP.pdf",
        "2 - MEASURING WHAT MATTERS.pdf",
        "3 - KNOW SOONER – ACT SMARTER.pdf"
    ]
    
    @staticmethod
    def get_our_thinking_principles() -> Dict:
        """
        Return the core principles from 'Our Thinking'
        Based on the Brief and reference documents
        """
        return {
            "core_philosophy": {
                "focus": "Address root causes (hypoxia), not symptoms",
                "key_message": "Traditional reports often measure non-actionable parameters",
                "solution": "Convert to ACTION Plans that work"
            },
            "critical_insights": {
                "dissolved_oxygen": {
                    "principle": "DO is the most important parameter - hypoxia drives HABs",
                    "requirement": "Must have detailed profiles, not averages",
                    "action": "Calculate hypoxic volumes and percentages"
                },
                "nutrients": {
                    "principle": "Measure available nutrients in hypoxic zones",
                    "requirement": "Orthophosphate and ammonia below oxycline",
                    "action": "Track what cyanobacteria can actually use"
                },
                "phytoplankton": {
                    "principle": "Biovolume matters more than cell counts",
                    "requirement": "Taxonomic identification with toxin producer tracking",
                    "action": "Monitor shift from beneficial to harmful species"
                },
                "bathymetry": {
                    "principle": "Essential for all meaningful calculations",
                    "requirement": "Use for volume calculations, not just maps",
                    "action": "Calculate hypoxic volumes and areas"
                }
            },
            "what_to_avoid": {
                "tsi": "Outdated - doesn't account for HABs",
                "chlorophyll_a": "Masks cyanobacteria dominance",
                "conductivity_ph": "Cannot be changed by intervention",
                "total_nutrients": "Too high-level, need specific forms",
                "clarity_measures": "Symptoms, not causes"
            },
            "conversion_to_action": {
                "step1": "Reallocate budget from non-actionable to critical parameters",
                "step2": "Begin monthly DO profiling with hypoxic calculations",
                "step3": "Track orthophosphate and ammonia in hypoxic zones",
                "step4": "Monitor phytoplankton biovolume and taxonomy",
                "step5": "Use bathymetry for all volume calculations"
            }
        }
    
    @staticmethod
    def generate_parameter_comment(parameter_name: str, is_found: bool, parameter_info: Dict, partial_credit: bool = False) -> str:
        """
        Generate a specific comment for each parameter as per Brief requirement:
        'Generate a short report or comment on each'
        
        Args:
            partial_credit: For calculations, True if the percentage version is found but absolute is not
        """
        if parameter_name.startswith('critical_'):
            if is_found:
                requirements = parameter_info.get('requirements', [])
                
                # Special handling for parameters that need measurement location guidance
                if 'orthophosphate' in parameter_name.lower() or 'ammonia' in parameter_name.lower():
                    # Find the measurement location requirement
                    location_req = None
                    other_reqs = []
                    for req in requirements:
                        if "deepest part of the lake" in req.lower():
                            location_req = req
                        else:
                            other_reqs.append(req)
                    
                    # Build the response with location guidance as separate sentence
                    base_response = (f"RELEVANT - {parameter_info.get('importance', '')}. "
                                   f"Ensure it meets requirements: {', '.join(other_reqs[:2])}")
                    if location_req:
                        return f"{base_response}. {location_req}"
                    return base_response
                
                # For dissolved oxygen, show all requirements
                elif 'dissolved_oxygen' in parameter_name.lower():
                    return (f"RELEVANT - {parameter_info.get('importance', '')}. "
                           f"Ensure it meets requirements: {', '.join(requirements)}")
                
                # Default for other parameters
                return (f"RELEVANT - {parameter_info.get('importance', '')}. "
                       f"Ensure it meets requirements: {', '.join(requirements[:2])}")
            else:
                return (f"MISSING - This is critical! {parameter_info.get('importance', '')}. "
                       f"Without this, you cannot properly assess lake health or HAB risk.")
        
        elif parameter_name.startswith('problem_'):
            if is_found:
                issue = parameter_info.get('issue', '')
                return (f"NOT ACTIONABLE - {issue}. "
                       f"This parameter does not provide actionable insights. "
                       f"Consider removing or de-emphasizing in favor of root cause metrics.")
            else:
                # Get the issue description to use in the "not found" message
                issue = parameter_info.get('issue', 'problematic parameter')
                # Convert to lowercase for the message (e.g., "outdated parameter" becomes "an outdated parameter")
                issue_lower = issue.lower()
                # Add appropriate article (a/an)
                article = 'an' if issue_lower[0] in 'aeiou' else 'a'
                return f"Not found (good - this is {article} {issue_lower})"
        
        elif parameter_name.startswith('calc_'):
            if is_found:
                return f"EXCELLENT - This calculation is being performed as it should be."
            elif partial_credit:
                # Percentage version is found but absolute value is not
                importance = parameter_info.get('importance', '')
                return (f"PARTIAL - Percentage calculated but absolute value not shown. {importance}. "
                       f"Consider reporting actual volumes/areas for better impact.")
            else:
                importance = parameter_info.get('importance', '')
                return (f"NOT CALCULATED - Critical calculation missing! {importance}. "
                       f"This calculation is essential for understanding lake dynamics.")
        
        return f"Status unclear"
    
    @staticmethod
    def get_educational_links() -> Dict[str, str]:
        """
        Return educational YouTube links for missing parameters
        As per Brief: 'include links to YouTube videos that explain more'
        
        NOTE: These should be replaced with actual client YouTube videos
        """
        return {
            "dissolved_oxygen": "https://www.youtube.com/results?search_query=lake+dissolved+oxygen+profiling+importance",
            "hypoxia_calculations": "https://www.youtube.com/results?search_query=calculating+hypoxic+volume+lakes",
            "orthophosphate_importance": "https://www.youtube.com/results?search_query=orthophosphate+vs+total+phosphorus+lakes",
            "ammonia_in_hypoxic": "https://www.youtube.com/results?search_query=ammonia+hypoxic+water+cyanobacteria",
            "phytoplankton_biovolume": "https://www.youtube.com/results?search_query=phytoplankton+biovolume+vs+cell+count",
            "bathymetry_calculations": "https://www.youtube.com/results?search_query=bathymetry+lake+volume+calculations",
            "cyanobacteria_habs": "https://www.youtube.com/results?search_query=cyanobacteria+harmful+algal+blooms+causes",
            "root_causes_vs_symptoms": "https://www.youtube.com/results?search_query=lake+management+root+causes+hypoxia"
        }
    
    @staticmethod
    def assess_lake_condition(doc_data: Dict) -> Dict:
        """
        Analyze the data in reports to provide assessment of each lake
        As per Brief: 'analyze the data in the reports to provide an assessment of each lake'
        """
        metrics = doc_data.get('metrics', {})
        parameters = doc_data.get('parameters_found', {})
        
        assessment = {
            "risk_level": "ELEVATED",  # Default to elevated when we don't have enough data
            "hypoxia_status": "Inadequately Monitored",
            "hab_potential": "Moderate", 
            "trajectory": "Concerning But Manageable - Good Monitoring In Place",
            "key_concerns": [],
            "positive_indicators": [],
            "data_quality": "Good"
        }
        
        # Check for critical parameters first
        critical_found = sum(1 for k, v in parameters.items() 
                           if k.startswith('critical_') and v)
        has_do_measurement = parameters.get('critical_dissolved_oxygen', False)
        
        # Check for problematic parameters
        problem_found = sum(1 for k, v in parameters.items() 
                          if k.startswith('problem_') and v)
        
        # Check for critical calculations
        calc_performed = sum(1 for k, v in parameters.items()
                           if k.startswith('calc_') and v)
        calc_missing = sum(1 for k, v in parameters.items()
                         if k.startswith('calc_') and not v)
        
        # Assess data quality
        if critical_found < 3:
            assessment["data_quality"] = "Poor"
            assessment["key_concerns"].append("Insufficient critical parameters measured")
        elif critical_found >= 4:
            assessment["data_quality"] = "Good"
            assessment["positive_indicators"].append("Measuring most critical parameters")
        else:
            assessment["data_quality"] = "Fair"
        
        # Try to assess based on DO values if available
        do_values = metrics.get('dissolved_oxygen_values', [])
        if do_values:
            min_do = min(do_values)
            if min_do < 2:
                assessment["hypoxia_status"] = "Severe"
                assessment["hab_potential"] = "High"
                assessment["risk_level"] = "CRITICAL"
                assessment["key_concerns"].append("Severe hypoxia detected - high HAB risk")
            elif min_do < 4:
                assessment["hypoxia_status"] = "Moderate"
                assessment["hab_potential"] = "Moderate"
                assessment["risk_level"] = "ELEVATED"
                assessment["key_concerns"].append("Moderate hypoxia - increasing HAB risk")
            else:
                assessment["hypoxia_status"] = "Minimal"
                assessment["hab_potential"] = "Low"
                assessment["risk_level"] = "LOW"
                assessment["positive_indicators"].append("Adequate oxygen levels")
        else:
            # No numeric DO values, but make assessment based on parameters and calculations
            if has_do_measurement:
                # DO is measured but values not extracted
                if calc_missing > 2:
                    assessment["risk_level"] = "ELEVATED"
                    assessment["hypoxia_status"] = "Likely Present"
                    assessment["hab_potential"] = "Moderate-High"
                    assessment["key_concerns"].append("Critical calculations missing - cannot fully assess hypoxia extent")
                elif calc_performed >= 2:
                    assessment["risk_level"] = "MODERATE"
                    assessment["hypoxia_status"] = "Inadequately Monitored"
                    assessment["hab_potential"] = "Moderate"
                    assessment["positive_indicators"].append("Performing critical calculations")
                else:
                    assessment["risk_level"] = "ELEVATED"
                    assessment["hypoxia_status"] = "Inadequately Monitored"
                    assessment["hab_potential"] = "Moderate"
            else:
                # DO not measured at all
                assessment["risk_level"] = "HIGH"
                assessment["hypoxia_status"] = "Not Monitored"
                assessment["hab_potential"] = "Unknown But Concerning"
                assessment["key_concerns"].append("Not measuring dissolved oxygen - cannot assess hypoxia risk")
        
        # Adjust based on problematic parameters
        if problem_found > 5:
            assessment["key_concerns"].append("Too many non-actionable parameters - consider reallocating resources")
            # Increase risk if not focusing on actionable parameters
            if assessment["risk_level"] == "low":
                assessment["risk_level"] = "moderate"
            elif assessment["risk_level"] == "moderate":
                assessment["risk_level"] = "elevated"
        
        # Determine trajectory based on comprehensive assessment
        if assessment["risk_level"] == "CRITICAL":
            if problem_found > 5:
                assessment["trajectory"] = "Declining Rapidly - Severe Problems and Wrong Focus"
            else:
                assessment["trajectory"] = "Declining - Severe Hypoxia Present"
        elif assessment["risk_level"] in ["HIGH", "ELEVATED"]:
            if critical_found >= 4 and calc_performed >= 2:
                assessment["trajectory"] = "Concerning But Manageable - Good Monitoring In Place"
            else:
                assessment["trajectory"] = "At Risk - Needs Immediate Attention"
        elif assessment["risk_level"] == "MODERATE":
            if critical_found >= 4:
                assessment["trajectory"] = "Stable - Continue Monitoring"
            else:
                assessment["trajectory"] = "Uncertain - Improve Monitoring"
        else:  # LOW risk
            if critical_found >= 4:
                assessment["trajectory"] = "Stable/Improving - Good Monitoring"
            else:
                assessment["trajectory"] = "Stable But Needs Better Monitoring"
        
        return assessment
