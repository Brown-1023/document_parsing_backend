"""
Compliance engine for evaluating documents against best practices
"""
from typing import Dict, List, Any
from enum import Enum
import logging
from config import COMPLIANCE_RULES
from .our_thinking_loader import OurThinkingManager

logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    """Compliance level categories"""
    EXCELLENT = "excellent"  # 80-100%
    GOOD = "good"           # 60-80%
    FAIR = "fair"           # 40-60%
    POOR = "poor"           # 20-40%
    FAILING = "failing"     # 0-20%

class ComplianceEngine:
    """Evaluate documents against David Shackleton's best practices"""
    
    def __init__(self):
        self.rules = COMPLIANCE_RULES
        self.scoring_weights = self.rules.get("scoring_weights", {})
        self.thinking_manager = OurThinkingManager()
    
    def evaluate_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a document against compliance rules
        
        Returns detailed evaluation with scores, issues, and recommendations
        """
        evaluation = {
            "overall_score": 0,
            "max_possible_score": 100,
            "compliance_level": ComplianceLevel.FAILING,
            "compliance_percentage": 0,
            "critical_parameters": {
                "found": [],
                "missing": [],
                "properly_measured": [],
                "partial_credit": []  # Parameters found but not properly measured per client feedback
            },
            "problematic_parameters": {
                "found": [],
                "issues": []
            },
            "calculations": {
                "found": [],
                "missing": []
            },
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "red_flags": [],
            "detailed_analysis": {},
            "individual_parameter_comments": {},  # As per Brief requirement
            "lake_assessment": {},  # As per Brief requirement
            "phytoplankton_management": {  # Per client feedback
                "interventions_found": [],
                "concerns": [],
                "is_negative": False
            }
        }
        
        # Evaluate critical parameters
        self._evaluate_critical_parameters(doc_data, evaluation)
        
        # Evaluate problematic parameters
        self._evaluate_problematic_parameters(doc_data, evaluation)
        
        # Evaluate calculations
        self._evaluate_calculations(doc_data, evaluation)
        
        # Evaluate phytoplankton management interventions (per client feedback)
        self._evaluate_phytoplankton_management(doc_data, evaluation)
        
        # Generate individual parameter comments (Brief requirement)
        self._generate_parameter_comments(doc_data, evaluation)
        
        # Assess lake condition (Brief requirement) 
        evaluation["lake_assessment"] = self.thinking_manager.assess_lake_condition(doc_data)
        
        # Calculate final score
        self._calculate_score(evaluation)
        
        # Generate recommendations
        self._generate_recommendations(evaluation)
        
        # Determine compliance level
        evaluation["compliance_level"] = self._determine_compliance_level(
            evaluation["compliance_percentage"]
        )
        
        return evaluation
    
    def evaluate_plan(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a Lake Management PLAN (proposed future actions)
        Focus on whether the plan addresses root causes and includes proper interventions
        """
        # Start with standard evaluation
        evaluation = self.evaluate_document(doc_data)
        
        # Adjust evaluation for plans
        evaluation["document_type"] = "Lake Management Plan"
        evaluation["focus_areas"] = {
            "addresses_root_causes": False,
            "includes_hypoxia_interventions": False,
            "has_monitoring_schedule": False,
            "has_phytoplankton_management": False,
            "has_bathymetry_plans": False
        }
        
        # Check if plan text mentions key interventions
        text_content = doc_data.get("text_content", "").lower()
        
        # Check for root cause focus
        if any(term in text_content for term in ["hypoxia", "dissolved oxygen", "do profile", "oxycline"]):
            evaluation["focus_areas"]["addresses_root_causes"] = True
            evaluation["strengths"].append("Plan addresses hypoxia - the root cause of HABs")
        else:
            evaluation["weaknesses"].append("Plan does not address hypoxia - missing root cause")
            evaluation["recommendations"].append({
                "priority": "HIGH",
                "recommendation": "Include hypoxia reduction strategies",
                "explanation": "Hypoxia drives HABs - must be addressed"
            })
        
        # Check for monitoring plans
        if "monthly" in text_content and any(term in text_content for term in ["monitor", "measure", "sampling"]):
            evaluation["focus_areas"]["has_monitoring_schedule"] = True
            evaluation["strengths"].append("Plan includes monthly monitoring schedule")
        else:
            evaluation["weaknesses"].append("No monthly monitoring schedule specified")
        
        # Check for intervention types
        if any(term in text_content for term in ["aeration", "destratification", "oxygenation", "circulation"]):
            evaluation["focus_areas"]["includes_hypoxia_interventions"] = True
            evaluation["strengths"].append("Plan includes hypoxia mitigation interventions")
        
        # Check for problematic interventions
        if any(term in text_content for term in ["algaecide", "copper sulfate", "chemical treatment", "herbicide"]):
            evaluation["red_flags"].append("Plan includes chemical treatments - treats symptoms not causes")
            evaluation["recommendations"].append({
                "priority": "HIGH",
                "recommendation": "Replace chemical treatments with root cause interventions",
                "explanation": "Chemicals provide temporary relief but don't address underlying hypoxia"
            })
        
        return evaluation
    
    def evaluate_report(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a Lake REPORT (actual measured data)
        Focus on data quality, trends, and what the measurements reveal
        """
        # Start with standard evaluation
        evaluation = self.evaluate_document(doc_data)
        
        # Adjust evaluation for reports with data
        evaluation["document_type"] = "Lake Report"
        evaluation["data_assessment"] = {
            "has_temporal_data": False,
            "has_depth_profiles": False,
            "has_quantitative_metrics": False,
            "data_frequency": "unknown"
        }
        
        # Check for actual measurements
        metrics = doc_data.get("metrics", {})
        text_content = doc_data.get("text_content", "").lower()
        
        # Check for DO measurements
        if metrics.get("dissolved_oxygen_values"):
            do_values = metrics["dissolved_oxygen_values"]
            min_do = min(do_values) if do_values else None
            
            if min_do and min_do < 2:
                evaluation["red_flags"].append(f"Severe hypoxia detected: {min_do} mg/L")
                evaluation["recommendations"].append({
                    "priority": "HIGH",
                    "recommendation": "Immediate intervention needed for severe hypoxia",
                    "explanation": "DO below 2 mg/L indicates critical HAB risk"
                })
            
            evaluation["data_assessment"]["has_quantitative_metrics"] = True
        
        # Check for temporal patterns
        if any(month in text_content for month in ["january", "february", "march", "april", "may", "june", 
                                                    "july", "august", "september", "october", "november", "december"]):
            evaluation["data_assessment"]["has_temporal_data"] = True
            evaluation["strengths"].append("Report includes temporal/seasonal data")
        
        # Check for depth measurements
        if metrics.get("depth_measurements") or "depth" in text_content:
            evaluation["data_assessment"]["has_depth_profiles"] = True
            evaluation["strengths"].append("Report includes depth profile data")
        
        # Check data collection frequency
        if "monthly" in text_content:
            evaluation["data_assessment"]["data_frequency"] = "monthly"
            evaluation["strengths"].append("Data collected monthly as recommended")
        elif "quarterly" in text_content:
            evaluation["data_assessment"]["data_frequency"] = "quarterly"
            evaluation["weaknesses"].append("Data only collected quarterly - should be monthly")
        elif "annual" in text_content or "yearly" in text_content:
            evaluation["data_assessment"]["data_frequency"] = "annual"
            evaluation["weaknesses"].append("Data only collected annually - insufficient frequency")
        
        # Add data-specific recommendations
        if not evaluation["data_assessment"]["has_depth_profiles"]:
            evaluation["recommendations"].append({
                "priority": "HIGH",
                "recommendation": "Include depth profile measurements",
                "explanation": "Need to measure parameters at multiple depths to understand stratification"
            })
        
        return evaluation
    
    def evaluate_hybrid(self, doc_data: Dict[str, Any], detected_type: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate a document as a HYBRID - analyzing it both as a forward-looking plan 
        and as a retrospective report. Most lake documents are a combination of both.
        
        This method:
        1. Auto-detects document characteristics
        2. Analyzes historical/retrospective data aspects
        3. Analyzes forward-looking/planning aspects
        4. Provides unified assessment with both perspectives
        """
        # Start with standard evaluation
        evaluation = self.evaluate_document(doc_data)
        
        # Initialize hybrid analysis structure
        evaluation["document_type"] = "Hybrid (Plan + Report)"
        evaluation["hybrid_analysis"] = {
            "document_characteristics": {},
            "retrospective_analysis": {},
            "forward_looking_analysis": {},
            "ai_detected_type": detected_type
        }
        
        text_content = doc_data.get("text_content", "").lower()
        metrics = doc_data.get("metrics", {})
        
        # ==========================================
        # DOCUMENT CHARACTERISTIC DETECTION
        # ==========================================
        characteristics = self._detect_document_characteristics(text_content, metrics)
        evaluation["hybrid_analysis"]["document_characteristics"] = characteristics
        
        # ==========================================
        # RETROSPECTIVE ANALYSIS (Report/Data aspect)
        # ==========================================
        retrospective = self._analyze_retrospective_aspects(text_content, metrics, evaluation)
        evaluation["hybrid_analysis"]["retrospective_analysis"] = retrospective
        
        # ==========================================
        # FORWARD-LOOKING ANALYSIS (Plan aspect)
        # ==========================================
        forward_looking = self._analyze_forward_looking_aspects(text_content, evaluation)
        evaluation["hybrid_analysis"]["forward_looking_analysis"] = forward_looking
        
        # ==========================================
        # UNIFIED ASSESSMENT
        # ==========================================
        # Combine insights from both perspectives
        self._generate_unified_recommendations(evaluation, characteristics, retrospective, forward_looking)
        
        return evaluation
    
    def _detect_document_characteristics(self, text_content: str, metrics: Dict) -> Dict[str, Any]:
        """Detect what type of content the document contains"""
        characteristics = {
            "has_historical_data": False,
            "has_future_plans": False,
            "has_measurements": False,
            "has_recommendations": False,
            "has_interventions": False,
            "time_references": {
                "past": [],
                "present": [],
                "future": []
            },
            "dominant_type": "unknown",
            "plan_percentage": 0,
            "report_percentage": 0
        }
        
        # Check for historical/past data indicators
        past_indicators = [
            "was measured", "were measured", "measured in", "data from",
            "observed", "recorded", "collected", "detected", "found",
            "results showed", "analysis showed", "testing revealed",
            "last year", "previous year", "in 2", "during 2",
            "historical", "past season", "prior to"
        ]
        past_count = sum(1 for indicator in past_indicators if indicator in text_content)
        
        # Check for current/present indicators
        present_indicators = [
            "currently", "this year", "this season", "present",
            "ongoing", "is being", "are being", "now shows"
        ]
        present_count = sum(1 for indicator in present_indicators if indicator in text_content)
        
        # Check for future/planning indicators
        future_indicators = [
            "will be", "plan to", "planning to", "proposed",
            "recommend", "should", "would", "could",
            "next year", "next season", "future", "upcoming",
            "intend to", "scheduled for", "anticipated",
            "implementation", "strategy", "objectives", "goals"
        ]
        future_count = sum(1 for indicator in future_indicators if indicator in text_content)
        
        # Check for actual measurement data
        if metrics.get("dissolved_oxygen_values") or metrics.get("phosphorus_values"):
            characteristics["has_measurements"] = True
            characteristics["has_historical_data"] = True
        
        # Check for month/year mentions (data reporting)
        months = ["january", "february", "march", "april", "may", "june", 
                  "july", "august", "september", "october", "november", "december"]
        if any(month in text_content for month in months):
            characteristics["has_historical_data"] = True
        
        # Check for intervention mentions
        interventions = ["aeration", "destratification", "treatment", "application", 
                        "dredging", "harvesting", "chemical", "algaecide"]
        if any(intervention in text_content for intervention in interventions):
            characteristics["has_interventions"] = True
        
        # Determine percentages
        total_indicators = past_count + present_count + future_count
        if total_indicators > 0:
            characteristics["report_percentage"] = round((past_count + present_count) / total_indicators * 100)
            characteristics["plan_percentage"] = round(future_count / total_indicators * 100)
        else:
            # Default to 50/50 if no clear indicators
            characteristics["report_percentage"] = 50
            characteristics["plan_percentage"] = 50
        
        # Set dominant type
        if characteristics["report_percentage"] > 70:
            characteristics["dominant_type"] = "report"
        elif characteristics["plan_percentage"] > 70:
            characteristics["dominant_type"] = "plan"
        else:
            characteristics["dominant_type"] = "hybrid"
        
        characteristics["has_historical_data"] = past_count > 0 or characteristics["has_measurements"]
        characteristics["has_future_plans"] = future_count > 0
        characteristics["has_recommendations"] = "recommend" in text_content or "should" in text_content
        
        return characteristics
    
    def _analyze_retrospective_aspects(self, text_content: str, metrics: Dict, evaluation: Dict) -> Dict[str, Any]:
        """Analyze the document as a retrospective report (data from the past)"""
        retrospective = {
            "data_quality": "unknown",
            "temporal_coverage": "unknown",
            "key_findings": [],
            "data_gaps": [],
            "measurements_present": False,
            "depth_profiles": False,
            "time_period": "unknown"
        }
        
        # Check for DO measurements
        if metrics.get("dissolved_oxygen_values"):
            do_values = metrics["dissolved_oxygen_values"]
            min_do = min(do_values) if do_values else None
            max_do = max(do_values) if do_values else None
            
            retrospective["measurements_present"] = True
            retrospective["key_findings"].append(f"DO range: {min_do}-{max_do} mg/L")
            
            if min_do and min_do < 2:
                retrospective["key_findings"].append("CRITICAL: Severe hypoxia detected in historical data")
                evaluation["red_flags"].append(f"Historical data shows severe hypoxia: {min_do} mg/L")
            elif min_do and min_do < 4:
                retrospective["key_findings"].append("WARNING: Moderate hypoxia in historical data")
        
        # Check for temporal data
        year_pattern_found = False
        for year in range(2015, 2026):
            if str(year) in text_content:
                year_pattern_found = True
                retrospective["time_period"] = f"Includes data from {year}"
                break
        
        if "monthly" in text_content:
            retrospective["temporal_coverage"] = "monthly"
            retrospective["data_quality"] = "good"
            evaluation["strengths"].append("Historical data collected at monthly intervals")
        elif "quarterly" in text_content:
            retrospective["temporal_coverage"] = "quarterly"
            retrospective["data_quality"] = "fair"
            evaluation["weaknesses"].append("Historical data only quarterly - monthly is preferred")
        elif "annual" in text_content or year_pattern_found:
            retrospective["temporal_coverage"] = "annual"
            retrospective["data_quality"] = "limited"
        
        # Check for depth profiles in historical data
        if "depth" in text_content and ("profile" in text_content or "meter" in text_content):
            retrospective["depth_profiles"] = True
            retrospective["key_findings"].append("Depth profile measurements available")
        else:
            retrospective["data_gaps"].append("Missing depth profile measurements")
        
        # Identify data gaps
        if not metrics.get("dissolved_oxygen_values"):
            retrospective["data_gaps"].append("No quantitative DO data found")
        
        if "bathymetry" not in text_content and "volume" not in text_content:
            retrospective["data_gaps"].append("No bathymetric or volume data")
        
        if "hypoxic" not in text_content and "anoxic" not in text_content:
            retrospective["data_gaps"].append("No hypoxic volume calculations")
        
        return retrospective
    
    def _analyze_forward_looking_aspects(self, text_content: str, evaluation: Dict) -> Dict[str, Any]:
        """Analyze the document as a forward-looking plan (future actions)"""
        forward_looking = {
            "has_action_plan": False,
            "addresses_root_causes": False,
            "intervention_quality": "unknown",
            "timeline_present": False,
            "proposed_interventions": [],
            "problematic_plans": [],
            "recommended_improvements": []
        }
        
        # Check for action plan indicators
        action_indicators = ["will implement", "plan to", "scheduled", "proposed", 
                           "objectives", "goals", "strategy", "action items"]
        if any(indicator in text_content for indicator in action_indicators):
            forward_looking["has_action_plan"] = True
            evaluation["strengths"].append("Document includes forward-looking action plan")
        
        # Check if plan addresses root causes (hypoxia)
        root_cause_terms = ["hypoxia", "dissolved oxygen", "do profile", "oxycline", 
                           "stratification", "anoxia", "oxygen depletion"]
        if any(term in text_content for term in root_cause_terms):
            forward_looking["addresses_root_causes"] = True
            evaluation["strengths"].append("Plan addresses root causes (hypoxia/DO)")
        else:
            forward_looking["recommended_improvements"].append(
                "Plan should address hypoxia - the root cause of most lake problems"
            )
        
        # Check for good interventions
        good_interventions = {
            "aeration": "Aeration/oxygenation - addresses root cause",
            "destratification": "Destratification - addresses thermal stratification",
            "oxygenation": "Oxygenation - directly addresses hypoxia",
            "circulation": "Circulation improvement - promotes mixing"
        }
        
        for intervention, description in good_interventions.items():
            if intervention in text_content:
                forward_looking["proposed_interventions"].append(description)
                forward_looking["intervention_quality"] = "good"
        
        # Check for problematic interventions
        problematic_interventions = {
            "algaecide": "Algaecide - treats symptoms, not causes",
            "copper sulfate": "Copper sulfate - chemical treatment, temporary solution",
            "herbicide": "Herbicide treatment - does not address root cause",
            "dredging": "Dredging - can release nutrients if not done properly"
        }
        
        for intervention, issue in problematic_interventions.items():
            if intervention in text_content:
                forward_looking["problematic_plans"].append(issue)
                evaluation["red_flags"].append(f"Plan includes: {issue}")
                if forward_looking["intervention_quality"] != "good":
                    forward_looking["intervention_quality"] = "concerning"
        
        # Check for timeline
        timeline_indicators = ["timeline", "schedule", "phase", "year 1", "year 2", 
                             "by 2025", "by 2026", "q1", "q2", "q3", "q4"]
        if any(indicator in text_content for indicator in timeline_indicators):
            forward_looking["timeline_present"] = True
            evaluation["strengths"].append("Plan includes implementation timeline")
        else:
            forward_looking["recommended_improvements"].append(
                "Add specific timeline for proposed actions"
            )
        
        # Check for monitoring plans
        if "monitor" in text_content and ("monthly" in text_content or "regular" in text_content):
            evaluation["strengths"].append("Plan includes ongoing monitoring schedule")
        else:
            forward_looking["recommended_improvements"].append(
                "Include monthly monitoring schedule in plan"
            )
        
        return forward_looking
    
    def _generate_unified_recommendations(self, evaluation: Dict, characteristics: Dict, 
                                         retrospective: Dict, forward_looking: Dict):
        """Generate unified recommendations considering both aspects"""
        
        # Add hybrid-specific summary
        evaluation["hybrid_summary"] = {
            "document_nature": f"This document is {characteristics['report_percentage']}% retrospective data and {characteristics['plan_percentage']}% forward-looking plans",
            "data_quality_assessment": retrospective.get("data_quality", "unknown"),
            "plan_quality_assessment": forward_looking.get("intervention_quality", "unknown"),
            "key_data_findings": retrospective.get("key_findings", []),
            "key_plan_elements": forward_looking.get("proposed_interventions", []),
            "critical_gaps": []
        }
        
        # Identify critical gaps
        if retrospective.get("data_gaps"):
            evaluation["hybrid_summary"]["critical_gaps"].extend(retrospective["data_gaps"])
        
        if forward_looking.get("recommended_improvements"):
            evaluation["hybrid_summary"]["critical_gaps"].extend(forward_looking["recommended_improvements"])
        
        # Add unified recommendations
        unified_recommendations = []
        
        # If data shows problems but no plan to address them
        if retrospective.get("key_findings") and not forward_looking.get("has_action_plan"):
            unified_recommendations.append({
                "priority": "HIGH",
                "category": "Missing Action Plan",
                "recommendation": "ADD ACTION PLAN based on historical data findings",
                "explanation": "Document contains data/findings but lacks a forward-looking plan to address issues"
            })
        
        # If plan doesn't address issues found in data
        if "hypoxia" in str(retrospective.get("key_findings", [])).lower() and not forward_looking.get("addresses_root_causes"):
            unified_recommendations.append({
                "priority": "HIGH",
                "category": "Root Cause Not Addressed",
                "recommendation": "PLAN MUST ADDRESS HYPOXIA identified in the data",
                "explanation": "Historical data shows hypoxia but future plans don't address this root cause"
            })
        
        # If no historical data to base plans on
        if not retrospective.get("measurements_present") and forward_looking.get("has_action_plan"):
            unified_recommendations.append({
                "priority": "MEDIUM",
                "category": "Data-Driven Planning",
                "recommendation": "COLLECT BASELINE DATA before implementing plans",
                "explanation": "Plans should be based on quantitative data, not assumptions"
            })
        
        # Add to existing recommendations
        evaluation["recommendations"] = unified_recommendations + evaluation.get("recommendations", [])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in evaluation["recommendations"]:
            rec_key = rec.get("recommendation", "")
            if rec_key not in seen:
                seen.add(rec_key)
                unique_recommendations.append(rec)
        evaluation["recommendations"] = unique_recommendations
    
    def _evaluate_critical_parameters(self, doc_data: Dict, evaluation: Dict):
        """Evaluate critical parameters that must be present"""
        critical_params = self.rules["parameters"]["critical_must_have"]
        text_content = doc_data.get("text_content", "").lower()
        
        # Check for depth-related measurements (per client feedback)
        depth_indicators = self._check_depth_measurements(text_content)
        
        for param_key, param_info in critical_params.items():
            param_found_key = f"critical_{param_key}"
            
            if doc_data.get("parameters_found", {}).get(param_found_key, False):
                # Check measurement quality based on parameter type (per client feedback)
                quality_assessment = self._assess_parameter_quality(
                    param_key, text_content, depth_indicators, doc_data
                )
                
                evaluation["critical_parameters"]["found"].append({
                    "name": param_key,
                    "importance": param_info.get("importance", ""),
                    "quality": quality_assessment
                })
                
                # Determine if properly measured based on quality assessment
                if quality_assessment["full_credit"]:
                    evaluation["critical_parameters"]["properly_measured"].append(param_key)
                    evaluation["strengths"].append(
                    f"Measures {param_key.replace('_', ' ')} - {param_info.get('importance', '')}"
                    )
                    evaluation["overall_score"] += self.scoring_weights.get(
                    "critical_parameter_present", 10
                    )
                else:
                    # Partial credit - parameter found but not properly measured
                    evaluation["critical_parameters"]["partial_credit"].append({
                        "name": param_key,
                        "reason": quality_assessment["reason"],
                        "requirements_met": quality_assessment.get("requirements_met", []),
                        "requirements_missing": quality_assessment.get("requirements_missing", [])
                    })
                    evaluation["strengths"].append(
                        f"Measures {param_key.replace('_', ' ')} - {param_info.get('importance', '')} "
                        f"(PARTIAL: {quality_assessment['reason']})"
                    )
                    # Give partial score (half credit)
                    evaluation["overall_score"] += self.scoring_weights.get(
                        "critical_parameter_present", 10
                    ) * 0.5
            else:
                evaluation["critical_parameters"]["missing"].append({
                    "name": param_key,
                    "importance": param_info.get("importance", ""),
                    "requirements": param_info.get("requirements", [])
                })
                evaluation["weaknesses"].append(
                    f"Missing critical parameter: {param_key.replace('_', ' ')}"
                )
                evaluation["overall_score"] += self.scoring_weights.get(
                    "critical_parameter_missing", -10
                )
    
    def _check_depth_measurements(self, text_content: str) -> Dict[str, bool]:
        """
        Check for indicators that measurements are taken at depth/bottom.
        Per client feedback: DO, orthophosphate, ammonia must be measured at the bottom.
        """
        depth_indicators = {
            "has_depth_profile": False,
            "measures_at_bottom": False,
            "measures_at_multiple_depths": False,
            "has_hypolimnion_data": False
        }
        
        # Check for depth profile indicators
        depth_profile_terms = [
            "depth profile", "vertical profile", "profile measurement",
            "multiple depths", "depths measured", "depth intervals",
            "every meter", "every 0.5m", "every half meter",
            "surface to bottom", "top to bottom", "entire water column"
        ]
        for term in depth_profile_terms:
            if term in text_content:
                depth_indicators["has_depth_profile"] = True
                depth_indicators["measures_at_multiple_depths"] = True
                break
        
        # Check for bottom measurement indicators
        bottom_terms = [
            "bottom", "near bottom", "near-bottom", "at bottom",
            "sediment-water interface", "benthic", "deep water",
            "deepest point", "maximum depth", "bottom water"
        ]
        for term in bottom_terms:
            if term in text_content:
                depth_indicators["measures_at_bottom"] = True
                break
        
        # Check for hypolimnion indicators (below thermocline)
        hypolimnion_terms = [
            "hypolimnion", "hypolimnetic", "below thermocline",
            "below oxycline", "deep layer", "bottom layer",
            "metalimnion", "stratification"
        ]
        for term in hypolimnion_terms:
            if term in text_content:
                depth_indicators["has_hypolimnion_data"] = True
                break
        
        return depth_indicators
    
    def _assess_parameter_quality(self, param_key: str, text_content: str, 
                                   depth_indicators: Dict[str, bool], 
                                   doc_data: Dict) -> Dict[str, Any]:
        """
        Assess if a parameter is measured properly based on client requirements.
        
        Per client feedback:
        - DO: Must be measured at regular intervals to bottom + hypoxic calculations
        - Orthophosphate: Must be measured at the bottom
        - Ammonia: Must be measured at the bottom
        """
        result = {
            "full_credit": True,
            "reason": "",
            "requirements_met": [],
            "requirements_missing": []
        }
        
        params_found = doc_data.get("parameters_found", {})
        
        if param_key == "dissolved_oxygen":
            # DO requirements per client:
            # 1. Measured at regular intervals all the way to bottom
            # 2. Hypoxic water volume calculated
            # 3. Hypoxic sediment area calculated
            
            has_depth = depth_indicators["has_depth_profile"] or depth_indicators["measures_at_multiple_depths"]
            has_bottom = depth_indicators["measures_at_bottom"]
            has_hypoxic_volume = params_found.get("calc_hypoxic_water_volume", False)
            has_hypoxic_area = params_found.get("calc_hypoxic_sediment_area", False)
            
            if has_depth and has_bottom:
                result["requirements_met"].append("Measured at regular intervals to bottom")
            elif has_depth:
                result["requirements_met"].append("Measured at multiple depths")
                result["requirements_missing"].append("Need measurements all the way to bottom")
            elif has_bottom:
                result["requirements_met"].append("Measured at bottom")
                result["requirements_missing"].append("Need regular interval depth profile")
            else:
                result["requirements_missing"].append("Need depth profile measurements to bottom")
            
            if has_hypoxic_volume:
                result["requirements_met"].append("Hypoxic water volume calculated")
            else:
                result["requirements_missing"].append("Need hypoxic water volume calculation")
            
            if has_hypoxic_area:
                result["requirements_met"].append("Hypoxic sediment area calculated")
            else:
                result["requirements_missing"].append("Need hypoxic sediment area calculation")
            
            # Full credit only if all requirements met
            if result["requirements_missing"]:
                result["full_credit"] = False
                result["reason"] = "; ".join(result["requirements_missing"][:2])
        
        elif param_key == "orthophosphate":
            # Orthophosphate must be measured at bottom (below oxycline)
            has_bottom = depth_indicators["measures_at_bottom"] or depth_indicators["has_hypolimnion_data"]
            
            if has_bottom:
                result["requirements_met"].append("Measured at bottom/hypolimnion")
            else:
                result["full_credit"] = False
                result["requirements_missing"].append("Must be measured at the bottom, not just surface")
                result["reason"] = "Must be measured at the bottom, not just surface"
        
        elif param_key == "ammonia":
            # Ammonia must be measured at bottom (below oxycline)
            has_bottom = depth_indicators["measures_at_bottom"] or depth_indicators["has_hypolimnion_data"]
            
            if has_bottom:
                result["requirements_met"].append("Measured at bottom/hypolimnion")
            else:
                result["full_credit"] = False
                result["requirements_missing"].append("Must be measured at the bottom, not just surface")
                result["reason"] = "Must be measured at the bottom, not just surface"
        
        elif param_key == "phytoplankton_demographics":
            # Check for proper phytoplankton analysis
            has_taxonomy = any(term in text_content for term in ["taxonomy", "taxonomic", "species", "genus"])
            has_biovolume = "biovolume" in text_content
            
            if has_taxonomy:
                result["requirements_met"].append("Includes taxonomic analysis")
            else:
                result["requirements_missing"].append("Need taxonomic identification")
            
            if has_biovolume:
                result["requirements_met"].append("Includes biovolume data")
            else:
                result["requirements_missing"].append("Need biovolume measurements")
            
            if not has_taxonomy or not has_biovolume:
                result["full_credit"] = False
                result["reason"] = "; ".join(result["requirements_missing"][:2]) if result["requirements_missing"] else "Incomplete analysis"
        
        elif param_key == "bathymetry":
            # Check if bathymetry is used for calculations
            has_volume_calc = any(term in text_content for term in ["volume calculation", "calculate volume", "water volume"])
            
            if has_volume_calc:
                result["requirements_met"].append("Used for volume calculations")
            else:
                result["full_credit"] = False
                result["requirements_missing"].append("Need to use for volume calculations")
                result["reason"] = "Present but not used for volume calculations"
        
        return result
    
    def _evaluate_problematic_parameters(self, doc_data: Dict, evaluation: Dict):
        """Evaluate problematic parameters that should be avoided"""
        problem_params = self.rules["parameters"]["problematic_avoid"]
        
        for param_key, param_info in problem_params.items():
            param_found_key = f"problem_{param_key}"
            
            if doc_data.get("parameters_found", {}).get(param_found_key, False):
                # Check for parameter dependencies
                is_acceptable = False
                modified_issue = param_info.get("issue", "Not actionable")
                
                # Check TP/OP dependency
                if param_key == "total_phosphorus":
                    if doc_data.get("parameters_found", {}).get("critical_orthophosphate", False):
                        is_acceptable = True
                        modified_issue = "Acceptable when paired with Orthophosphate measurement"
                    else:
                        modified_issue = "Needs to be paired with Orthophosphate measurement"
                
                # Check TN/Ammonia dependency
                elif param_key == "total_nitrogen":
                    if doc_data.get("parameters_found", {}).get("critical_ammonia", False):
                        is_acceptable = True
                        modified_issue = "Acceptable when paired with Ammonia measurement"
                    else:
                        modified_issue = "Needs to be paired with Ammonia measurement"
                
                evaluation["problematic_parameters"]["found"].append(param_key)
                
                # Only add as issue if not acceptable
                if not is_acceptable:
                    evaluation["problematic_parameters"]["issues"].append({
                        "parameter": param_key,
                        "issue": modified_issue,
                        "problems": param_info.get("problems", [modified_issue])
                    })
                    
                    evaluation["red_flags"].append(
                        f"Uses {param_key.replace('_', ' ')}: {modified_issue}"
                    )
                    
                    evaluation["overall_score"] += self.scoring_weights.get(
                        "problematic_parameter_present", -5
                    )
    
    def _evaluate_calculations(self, doc_data: Dict, evaluation: Dict):
        """Evaluate if critical calculations are performed"""
        calculations = self.rules.get("critical_calculations", {})
        params_found = doc_data.get("parameters_found", {})
        
        # Track related calculations to avoid contradictions
        # If percentage is found, don't mark absolute as missing (it's related)
        percentage_found = {
            "hypoxic_percentage_volume": params_found.get("calc_hypoxic_percentage_volume", False),
            "hypoxic_percentage_area": params_found.get("calc_hypoxic_percentage_area", False)
        }
        
        # Related pairs: percentage <-> absolute
        related_calcs = {
            "hypoxic_water_volume": "hypoxic_percentage_volume",
            "hypoxic_sediment_area": "hypoxic_percentage_area"
        }
        
        for calc_key, calc_info in calculations.items():
            calc_found_key = f"calc_{calc_key}"
            
            if params_found.get(calc_found_key, False):
                evaluation["calculations"]["found"].append({
                    "name": calc_key,
                    "formula": calc_info.get("formula", ""),
                    "importance": calc_info.get("importance", "")
                })
                evaluation["strengths"].append(
                    f"Performs {calc_key.replace('_', ' ')} calculation"
                )
                evaluation["overall_score"] += self.scoring_weights.get(
                    "critical_calculation_present", 15
                )
            else:
                # Check if this is a related calculation where the percentage version was found
                related_key = related_calcs.get(calc_key)
                if related_key and percentage_found.get(related_key, False):
                    # Percentage is found but absolute isn't - partial credit
                    # Don't add to missing, but note that actual values should be calculated
                    evaluation["calculations"]["found"].append({
                        "name": calc_key,
                        "formula": calc_info.get("formula", ""),
                        "importance": calc_info.get("importance", ""),
                        "status": "partial - percentage mentioned but actual values not calculated"
                    })
                    # Give partial credit
                    evaluation["overall_score"] += self.scoring_weights.get(
                        "critical_calculation_present", 15
                    ) * 0.5
                else:
                    evaluation["calculations"]["missing"].append({
                        "name": calc_key,
                        "formula": calc_info.get("formula", ""),
                        "importance": calc_info.get("importance", "")
                    })
                    evaluation["weaknesses"].append(
                        f"Missing calculation: {calc_key.replace('_', ' ')}"
                    )
                    evaluation["overall_score"] += self.scoring_weights.get(
                        "critical_calculation_missing", -15
                    )
    
    def _evaluate_phytoplankton_management(self, doc_data: Dict, evaluation: Dict):
        """
        Evaluate phytoplankton management interventions
        Per client feedback: Algaecides, Herbicides, Phosphorus precipitants are big negatives
        """
        text_content = doc_data.get("text_content", "").lower()
        
        # Get intervention definitions from rules
        interventions_config = self.rules.get("phytoplankton_management_interventions", {})
        
        # If not in rules, use defaults
        if not interventions_config:
            interventions_config = {
                "algaecides": {
                    "issue": "Treats symptoms, not root causes",
                    "severity": "high_negative",
                    "search_terms": ["algaecide", "algicide", "algae treatment", "algae control chemical"]
                },
                "herbicides": {
                    "issue": "Chemical treatment that doesn't address root causes",
                    "severity": "high_negative",
                    "search_terms": ["herbicide", "aquatic herbicide", "weed killer"]
                },
                "phosphorus_precipitants": {
                    "issue": "Chemical binding approach with limited effectiveness",
                    "severity": "high_negative",
                    "search_terms": ["phosphorus precipitant", "alum", "aluminum sulfate", "lanthanum", "phoslock", "P inactivation"]
                }
            }
        
        phyto_management = evaluation.get("phytoplankton_management", {
            "interventions_found": [],
            "concerns": [],
            "is_negative": False
        })
        
        # Check for each intervention type
        for intervention_key, intervention_info in interventions_config.items():
            search_terms = intervention_info.get("search_terms", [])
            
            for term in search_terms:
                if term.lower() in text_content:
                    intervention_name = intervention_key.replace("_", " ").title()
                    issue = intervention_info.get("issue", "Treats symptoms, not root causes")
                    problems = intervention_info.get("problems", [])
                    
                    phyto_management["interventions_found"].append({
                        "name": intervention_name,
                        "issue": issue,
                        "problems": problems
                    })
                    
                    phyto_management["concerns"].append(
                        f"{intervention_name}: {issue}"
                    )
                    
                    phyto_management["is_negative"] = True
                    
                    # Add to red flags
                    evaluation["red_flags"].append(
                        f"Uses {intervention_name} - {issue}"
                    )
                    
                    # Add to weaknesses
                    evaluation["weaknesses"].append(
                        f"Uses {intervention_name} for phytoplankton management - treats symptoms, not root causes"
                    )
                    
                    # Penalize score
                    evaluation["overall_score"] += self.scoring_weights.get(
                        "counter_productive_intervention", -5
                    )
                    
                    # Only count each intervention type once
                    break
        
        # Update evaluation
        evaluation["phytoplankton_management"] = phyto_management
        
        # If interventions found, add recommendation
        if phyto_management["is_negative"]:
            evaluation["recommendations"].append({
                "priority": "HIGH",
                "category": "Phytoplankton Management",
                "recommendation": "REPLACE chemical interventions with root-cause approaches",
                "explanation": "Algaecides, herbicides, and phosphorus precipitants treat symptoms, not causes. Focus on reducing hypoxia instead."
            })
    
    def _generate_parameter_comments(self, doc_data: Dict, evaluation: Dict):
        """
        Generate individual comments for each parameter
        As per Brief: 'Generate a short report or comment on each'
        """
        params_found = doc_data.get("parameters_found", {})
        comments = {}
        
        # Build partial credit mapping for calculations (percentage found but absolute not)
        partial_credit_calcs = {}
        percentage_calcs = {
            "hypoxic_water_volume": "hypoxic_percentage_volume",
            "hypoxic_sediment_area": "hypoxic_percentage_area"
        }
        for abs_calc, pct_calc in percentage_calcs.items():
            abs_found = params_found.get(f"calc_{abs_calc}", False)
            pct_found = params_found.get(f"calc_{pct_calc}", False)
            if pct_found and not abs_found:
                partial_credit_calcs[abs_calc] = True
        
        # Comment on critical parameters
        for param_key, param_info in self.rules["parameters"]["critical_must_have"].items():
            full_key = f"critical_{param_key}"
            found = params_found.get(full_key, False)
            comments[full_key] = self.thinking_manager.generate_parameter_comment(
                full_key, found, param_info
            )
        
        # Comment on problematic parameters  
        for param_key, param_info in self.rules["parameters"]["problematic_avoid"].items():
            full_key = f"problem_{param_key}"
            found = params_found.get(full_key, False)
            comments[full_key] = self.thinking_manager.generate_parameter_comment(
                full_key, found, param_info
            )
        
        # Comment on calculations (account for partial credit)
        for calc_key, calc_info in self.rules["critical_calculations"].items():
            full_key = f"calc_{calc_key}"
            found = params_found.get(full_key, False)
            
            # Check for partial credit status
            partial_credit = partial_credit_calcs.get(calc_key, False)
            
            comments[full_key] = self.thinking_manager.generate_parameter_comment(
                full_key, found, calc_info, partial_credit=partial_credit
            )
        
        evaluation["individual_parameter_comments"] = comments
    
    def _check_parameter_quality(self, doc_data: Dict, param_key: str, param_info: Dict) -> bool:
        """
        Check if a parameter is properly measured according to requirements
        This is a simplified version - full version would use AI
        """
        # Simplified heuristics
        text = doc_data.get("text_content", "").lower()
        requirements = param_info.get("requirements", [])
        
        if param_key == "dissolved_oxygen":
            # Check for depth measurements
            if "depth" in text and "profile" in text:
                return True
            if any(term in text for term in ["0m", "2m", "4m", "surface", "bottom"]):
                return True
        
        elif param_key == "phytoplankton_demographics":
            # Check for taxonomic detail
            if "biovolume" in text or "species" in text or "taxonomy" in text:
                return True
        
        elif param_key == "bathymetry":
            # Check if used for calculations
            if "volume" in text and "bathym" in text:
                return True
        
        # Default: assume basic measurement only
        return False
    
    def _calculate_score(self, evaluation: Dict):
        """Calculate final compliance score"""
        # Ensure score is between 0 and 100
        evaluation["overall_score"] = max(0, min(100, 50 + evaluation["overall_score"]))
        evaluation["compliance_percentage"] = evaluation["overall_score"]
    
    def _generate_recommendations(self, evaluation: Dict):
        """Generate specific, actionable recommendations"""
        recommendations = []
        
        # Priority 1: Missing critical parameters
        for param in evaluation["critical_parameters"]["missing"]:
            recommendations.append({
                "priority": "HIGH",
                "category": "Missing Critical Parameter",
                "recommendation": f"ADD {param['name'].upper().replace('_', ' ')}",
                "explanation": param['importance'],
                "requirements": param.get('requirements', [])
            })
        
        # Priority 2: Missing calculations
        for calc in evaluation["calculations"]["missing"]:
            recommendations.append({
                "priority": "HIGH",
                "category": "Missing Calculation",
                "recommendation": f"CALCULATE {calc['name'].replace('_', ' ')}",
                "explanation": calc['importance'],
                "formula": calc.get('formula', '')
            })
        
        # Priority 3: Improperly measured parameters
        for param in evaluation["critical_parameters"]["found"]:
            if param["name"] not in evaluation["critical_parameters"]["properly_measured"]:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Improve Measurement",
                    "recommendation": f"IMPROVE measurement of {param['name'].replace('_', ' ')}",
                    "explanation": "Parameter found but not properly measured according to best practices"
                })
        
        # Priority 4: Remove problematic parameters
        for issue in evaluation["problematic_parameters"]["issues"]:
            recommendations.append({
                "priority": "LOW",
                "category": "Remove Non-Actionable",
                "recommendation": f"REMOVE or DE-EMPHASIZE {issue['parameter'].replace('_', ' ')}",
                "explanation": issue['issue']
            })
        
        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        evaluation["recommendations"] = recommendations
    
    def _determine_compliance_level(self, percentage: float) -> ComplianceLevel:
        """Determine compliance level based on percentage"""
        if percentage >= 80:
            return ComplianceLevel.EXCELLENT
        elif percentage >= 60:
            return ComplianceLevel.GOOD
        elif percentage >= 40:
            return ComplianceLevel.FAIR
        elif percentage >= 20:
            return ComplianceLevel.POOR
        else:
            return ComplianceLevel.FAILING

class ComplianceReport:
    """Generate human-readable compliance reports"""
    
    @staticmethod
    def generate_summary(evaluation: Dict) -> str:
        """Generate a text summary of the evaluation"""
        summary = f"""
COMPLIANCE EVALUATION SUMMARY
=============================
Overall Score: {evaluation['compliance_percentage']:.1f}%
Compliance Level: {evaluation['compliance_level'].value.upper()}

CRITICAL PARAMETERS:
- Found: {len(evaluation['critical_parameters']['found'])} of 5
- Missing: {len(evaluation['critical_parameters']['missing'])}
- Properly Measured: {len(evaluation['critical_parameters']['properly_measured'])}

PROBLEMATIC PARAMETERS:
- Found: {len(evaluation['problematic_parameters']['found'])}

CALCULATIONS:
- Performed: {len(evaluation['calculations']['found'])}
- Missing: {len(evaluation['calculations']['missing'])}

TOP RECOMMENDATIONS:
"""
        for i, rec in enumerate(evaluation['recommendations'][:3], 1):
            summary += f"{i}. [{rec['priority']}] {rec['recommendation']}\n"
        
        return summary
