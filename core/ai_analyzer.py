"""
AI-powered analysis using GPT-4 for intelligent document evaluation
"""
from openai import AsyncOpenAI
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import json
import logging
import asyncio
from config import settings
from .our_thinking_loader import OurThinkingManager

logger = logging.getLogger(__name__)

# ============================================
# Pydantic Models for Structured Outputs
# ============================================

class TimeReferences(BaseModel):
    """Time references found in the document"""
    past_data_years: List[str] = Field(default_factory=list, description="Years mentioned for past data")
    current_year_data: bool = Field(default=False, description="Whether current year data is present")
    future_plans_mentioned: bool = Field(default=False, description="Whether future plans are mentioned")

class ContentBreakdown(BaseModel):
    """Breakdown of content types in the document"""
    historical_data_present: bool = Field(default=False, description="Whether historical data is present")
    measurements_present: bool = Field(default=False, description="Whether measurements are present")
    recommendations_present: bool = Field(default=False, description="Whether recommendations are present")
    action_plans_present: bool = Field(default=False, description="Whether action plans are present")
    intervention_proposals_present: bool = Field(default=False, description="Whether intervention proposals are present")

class DocumentTypeDetection(BaseModel):
    """Structured output for document type detection"""
    primary_type: str = Field(description="Primary document type: 'plan', 'report', or 'hybrid'")
    plan_percentage: int = Field(ge=0, le=100, description="Percentage of content that is forward-looking/planning")
    report_percentage: int = Field(ge=0, le=100, description="Percentage of content that is retrospective/reporting")
    time_references: TimeReferences = Field(default_factory=TimeReferences)
    content_breakdown: ContentBreakdown = Field(default_factory=ContentBreakdown)
    summary: str = Field(description="Brief 1-2 sentence summary of document nature")

class RetrospectiveAnalysis(BaseModel):
    """Analysis of historical/retrospective data in the document"""
    data_quality_score: int = Field(ge=0, le=10, description="Quality score for historical data (0-10)")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from historical data")
    data_gaps: List[str] = Field(default_factory=list, description="Identified gaps in data")
    problems_identified: List[str] = Field(default_factory=list, description="Problems identified from data")
    time_coverage: str = Field(default="unknown", description="Description of time period covered")

class ForwardLookingAnalysis(BaseModel):
    """Analysis of future plans/recommendations in the document"""
    plan_quality_score: int = Field(ge=0, le=10, description="Quality score for future plans (0-10)")
    proposed_actions: List[str] = Field(default_factory=list, description="Proposed actions identified")
    addresses_root_causes: bool = Field(default=False, description="Whether plans address root causes like hypoxia")
    timeline_present: bool = Field(default=False, description="Whether implementation timeline is present")
    monitoring_included: bool = Field(default=False, description="Whether monitoring plans are included")
    concerning_proposals: List[str] = Field(default_factory=list, description="Any problematic interventions proposed")

class AlignmentAssessment(BaseModel):
    """Assessment of alignment between data and plans"""
    plans_match_data: bool = Field(default=False, description="Whether plans address issues found in data")
    alignment_score: int = Field(ge=0, le=10, description="Alignment score (0-10)")
    gaps_between_data_and_plans: List[str] = Field(default_factory=list, description="Gaps between data findings and plans")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations to improve alignment")

class HybridAnalysis(BaseModel):
    """Complete hybrid analysis of document from both perspectives"""
    retrospective_analysis: RetrospectiveAnalysis
    forward_looking_analysis: ForwardLookingAnalysis
    alignment_assessment: AlignmentAssessment
    overall_hybrid_score: int = Field(ge=0, le=10, description="Overall hybrid analysis score (0-10)")
    executive_summary: str = Field(description="2-3 sentence summary of both aspects")

class FocusAnalysis(BaseModel):
    """Analysis of document focus (symptoms vs root causes)"""
    focus: str = Field(description="Primary focus: 'symptoms', 'root_causes', or 'mixed'")
    root_cause_percentage: int = Field(ge=0, le=100, description="Percentage addressing root causes")
    symptom_percentage: int = Field(ge=0, le=100, description="Percentage addressing symptoms")
    key_findings: List[str] = Field(default_factory=list, description="Key findings about focus")
    recommendation_quality: str = Field(description="Quality: 'treating_symptoms', 'addressing_causes', or 'mixed'")
    alignment_with_our_thinking: str = Field(description="Alignment level: 'strong', 'moderate', 'weak', or 'none'")

class DissolvedOxygenQuality(BaseModel):
    """Quality assessment for dissolved oxygen measurements"""
    multiple_depths: bool = Field(default=False)
    complete_profile: bool = Field(default=False)
    hypoxic_calculations: bool = Field(default=False)
    quality_score: int = Field(ge=0, le=10, default=0)

class NutrientQuality(BaseModel):
    """Quality assessment for nutrient measurements"""
    orthophosphate_separate: bool = Field(default=False)
    below_thermocline: bool = Field(default=False)
    ammonia_in_hypoxic: bool = Field(default=False)
    quality_score: int = Field(ge=0, le=10, default=0)

class PhytoplanktonQuality(BaseModel):
    """Quality assessment for phytoplankton measurements"""
    taxonomic_detail: bool = Field(default=False)
    biovolume_measured: bool = Field(default=False)
    cyanobacteria_distinguished: bool = Field(default=False)
    quality_score: int = Field(ge=0, le=10, default=0)

class ParameterQualityAnalysis(BaseModel):
    """Complete parameter quality analysis"""
    dissolved_oxygen_quality: DissolvedOxygenQuality
    nutrient_quality: NutrientQuality
    phytoplankton_quality: PhytoplanktonQuality

class CalculationsCheck(BaseModel):
    """Check for critical calculations in the document"""
    hypoxic_volume: str = Field(description="Status: 'calculated', 'data_available', or 'not_possible'")
    hypoxic_volume_percentage: str = Field(description="Status: 'calculated', 'data_available', or 'not_possible'")
    hypoxic_area: str = Field(description="Status: 'calculated', 'data_available', or 'not_possible'")
    hypoxic_area_percentage: str = Field(description="Status: 'calculated', 'data_available', or 'not_possible'")
    oxycline_depth: str = Field(description="Status: 'calculated', 'data_available', or 'not_possible'")
    calculations_summary: str = Field(description="Brief explanation of what calculations are missing")

class InterventionsAnalysis(BaseModel):
    """Analysis of interventions mentioned in the document"""
    counter_productive: List[str] = Field(default_factory=list, description="Counter-productive interventions found")
    symptomatic: List[str] = Field(default_factory=list, description="Symptomatic treatments found")
    effective: List[str] = Field(default_factory=list, description="Effective interventions found")
    intervention_score: int = Field(ge=0, le=10, description="Overall intervention quality score")
    main_concern: str = Field(default="", description="Brief explanation of biggest intervention issue")

class OverallQuality(BaseModel):
    """Overall quality assessment of the document"""
    actionable_insights: int = Field(ge=0, le=10, description="Score for actionable insights")
    transparency: int = Field(ge=0, le=10, description="Score for data transparency")
    clarity_for_owner: int = Field(ge=0, le=10, description="Score for clarity for lake owner")
    best_practices_adherence: int = Field(ge=0, le=10, description="Score for best practices adherence")
    overall_quality: int = Field(ge=0, le=10, description="Overall quality score")
    strengths: List[str] = Field(default_factory=list, description="Document strengths")
    major_gaps: List[str] = Field(default_factory=list, description="Major gaps identified")
    executive_summary: str = Field(description="2-3 sentence overall assessment")

# Timeout for AI API calls (seconds)
AI_TIMEOUT = 120


class ExtractedDataValues(BaseModel):
    """AI-extracted numerical data values from the document"""
    # Dissolved Oxygen - simplified to avoid Dict types that cause schema issues
    minimum_do_value: Optional[float] = Field(default=None, description="Minimum DO value found")
    minimum_do_depth: Optional[float] = Field(default=None, description="Depth where minimum DO was found")
    oxycline_depth: Optional[float] = Field(default=None, description="Depth where DO < 2.5 mg/L")
    do_measured_at_bottom: bool = Field(default=False, description="Whether DO measured at lake bottom")
    do_profile_description: str = Field(default="", description="Description of DO profile with depths and values")
    
    # Nutrients - simplified
    srp_in_hypolimnion: Optional[float] = Field(default=None, description="SRP concentration below oxycline (mg/L)")
    srp_at_surface: Optional[float] = Field(default=None, description="SRP at surface (mg/L)")
    ammonia_in_hypolimnion: Optional[float] = Field(default=None, description="Ammonia below oxycline (mg/L)")
    ammonia_at_surface: Optional[float] = Field(default=None, description="Ammonia at surface (mg/L)")
    nutrient_profile_description: str = Field(default="", description="Description of nutrient values at various depths")
    
    # Lake morphometry
    max_depth: Optional[float] = Field(default=None, description="Maximum lake depth (m)")
    lake_volume: Optional[float] = Field(default=None, description="Total lake volume (m³)")
    lake_surface_area: Optional[float] = Field(default=None, description="Surface area (hectares or m²)")
    has_hypsographic_table: bool = Field(default=False, description="Whether hypsographic data is present")
    
    # Sampling info
    sampling_locations: List[str] = Field(default_factory=list, description="Named sampling locations")
    deepest_sampling_location: Optional[str] = Field(default=None, description="Deepest/most meaningful sampling point")
    years_with_data: List[int] = Field(default_factory=list, description="Years for which data exists")
    summer_months_sampled: List[str] = Field(default_factory=list, description="Summer months with samples")


class AdvancedCalculations(BaseModel):
    """Calculations that could be performed with available data"""
    hypoxic_volume_calculated: bool = Field(default=False, description="Whether hypoxic volume is calculated in doc")
    hypoxic_volume_could_be_calculated: bool = Field(default=False, description="Whether data exists to calculate")
    hypoxic_area_calculated: bool = Field(default=False, description="Whether hypoxic area is calculated in doc")
    hypoxic_area_could_be_calculated: bool = Field(default=False, description="Whether data exists to calculate")
    biomass_potential_could_be_calculated: bool = Field(default=False, description="Whether P biomass potential can be calc")
    
    # What's missing for calculations
    missing_for_hypoxic_volume: List[str] = Field(default_factory=list, description="Data needed for hypoxic volume calc")
    missing_for_biomass_potential: List[str] = Field(default_factory=list, description="Data needed for biomass calc")
    
    # Values extracted that aren't being used
    underutilized_data: List[str] = Field(default_factory=list, description="Available data not being fully utilized")


class TrendAnalysis(BaseModel):
    """Multi-year trend analysis"""
    has_multi_year_data: bool = Field(default=False, description="Whether multiple years of data exist")
    years_analyzed: List[int] = Field(default_factory=list, description="Years covered")
    
    # Specific parameter trends
    do_trend: str = Field(default="unknown", description="DO trend: improving/declining/stable/unknown")
    phosphorus_trend: str = Field(default="unknown", description="P trend: improving/declining/stable/unknown")
    cyanobacteria_trend: str = Field(default="unknown", description="Cyano trend: improving/declining/stable/unknown")
    water_quality_trend: str = Field(default="unknown", description="Overall WQ trend")
    
    # Key year-over-year changes mentioned
    key_changes: List[str] = Field(default_factory=list, description="Significant changes noted between years")


class DataQualityChecklist(BaseModel):
    """Comprehensive checklist per client's specific questions"""
    
    # Dissolved Oxygen checklist
    do_measured_at_intervals_to_bottom: bool = Field(default=False, description="DO measured at regular intervals to bottom?")
    do_measurement_frequency: str = Field(default="unknown", description="How often DO measured per year")
    do_summer_months_covered: List[str] = Field(default_factory=list, description="Which summer months have DO data")
    do_multi_year_available: bool = Field(default=False, description="Multiple years of DO data for trends?")
    oxycline_depth_identified: bool = Field(default=False, description="Depth where DO <2.5mg/L identified?")
    hypsographic_table_available: bool = Field(default=False, description="Hypsographic table available?")
    hypoxic_volume_calculated: bool = Field(default=False, description="Hypoxic water volume calculated?")
    hypoxic_area_calculated: bool = Field(default=False, description="Hypoxic sediment area calculated?")
    
    # Nutrient checklist
    srp_measured: bool = Field(default=False, description="Orthophosphate (SRP) measured?")
    srp_below_oxycline: bool = Field(default=False, description="SRP measured below oxycline?")
    srp_summer_months_covered: List[str] = Field(default_factory=list, description="Summer months with SRP data")
    srp_multi_year_available: bool = Field(default=False, description="Multiple years of SRP for trends?")
    ammonia_measured: bool = Field(default=False, description="Ammonia measured?")
    ammonia_below_oxycline: bool = Field(default=False, description="Ammonia measured below oxycline?")
    ammonia_summer_months_covered: List[str] = Field(default_factory=list, description="Summer months with ammonia data")
    ammonia_multi_year_available: bool = Field(default=False, description="Multiple years of ammonia for trends?")
    biomass_potential_calculated: bool = Field(default=False, description="Phytoplankton Biomass Potential calculated?")
    
    # Phytoplankton checklist
    phytoplankton_taxonomy_detailed: bool = Field(default=False, description="Detailed taxonomy provided?")
    phytoplankton_biovolume_by_taxa: bool = Field(default=False, description="Biovolume by taxa provided?")
    phytoplankton_cell_count_by_taxa: bool = Field(default=False, description="Cell count by taxa provided?")
    phytoplankton_summer_months_covered: List[str] = Field(default_factory=list, description="Summer months with phyto data")
    phytoplankton_multi_year_available: bool = Field(default=False, description="Multiple years of phyto for trends?")
    
    # Calculated values (when we can calculate them)
    calculated_hypoxic_volume_m3: Optional[float] = Field(default=None, description="Calculated hypoxic volume in m³")
    calculated_hypoxic_percentage: Optional[float] = Field(default=None, description="Calculated hypoxic percentage")
    calculated_available_p_kg: Optional[float] = Field(default=None, description="Calculated available P in kg")
    calculated_biomass_potential_tonnes: Optional[float] = Field(default=None, description="Calculated biomass potential in tonnes")
    
    # Criticisms
    criticisms: List[str] = Field(default_factory=list, description="Specific criticisms of the report's analysis")


class LakeBackground(BaseModel):
    """History and background information about the lake"""
    lake_name: str = Field(default="", description="Name of the lake")
    management_start_year: Optional[int] = Field(default=None, description="Year management began")
    management_history: str = Field(default="", description="Brief history of lake management")
    nutrient_sources: List[str] = Field(default_factory=list, description="Identified nutrient sources")
    current_systems: List[str] = Field(default_factory=list, description="Current aeration/treatment systems")
    system_issues: List[str] = Field(default_factory=list, description="Problems with current systems")
    stated_objectives: List[str] = Field(default_factory=list, description="Stated management objectives")
    hab_history: str = Field(default="", description="History of HAB events")
    key_concerns: List[str] = Field(default_factory=list, description="Key concerns mentioned")


class SpecificDataValues(BaseModel):
    """Specific data values extracted from the document for reporting"""
    # Location-specific values - using strings to describe values by year
    deepest_location_name: Optional[str] = Field(default=None, description="Name of deepest sampling location")
    do_values_by_year: str = Field(default="", description="DO values at deepest location described by year, e.g., '2021: 0.5mg/L, 2022: 1.2mg/L'")
    srp_values_by_year: str = Field(default="", description="SRP values at depth described by year, e.g., '2021: 0.27mg/L, 2023: 0.025mg/L'")
    ammonia_values_by_year: str = Field(default="", description="Ammonia values at depth described by year")
    
    # Year-over-year changes (for trend reporting) - these are the key values per client feedback
    key_parameter_changes: List[str] = Field(default_factory=list, description="Specific changes like 'SRP reduced from 0.27 mg/L (2021) to 0.025 mg/L (2023)'")
    
    # Hypsographic data
    hypoxic_volume_m3: Optional[float] = Field(default=None, description="Hypoxic water volume in m³")
    hypoxic_percentage: Optional[float] = Field(default=None, description="Percentage of lake that is hypoxic")
    biomass_potential_tonnes: Optional[float] = Field(default=None, description="Calculated biomass potential in tonnes")


class ComprehensiveAnalysisResult(BaseModel):
    """Complete advanced analysis result"""
    extracted_data: ExtractedDataValues = Field(default_factory=ExtractedDataValues)
    calculations_assessment: AdvancedCalculations = Field(default_factory=AdvancedCalculations)
    trend_analysis: TrendAnalysis = Field(default_factory=TrendAnalysis)
    lake_background: LakeBackground = Field(default_factory=LakeBackground)
    specific_values: SpecificDataValues = Field(default_factory=SpecificDataValues)
    
    # Key insights
    critical_findings: List[str] = Field(default_factory=list, description="Most important findings")
    data_quality_issues: List[str] = Field(default_factory=list, description="Problems with data quality/completeness")
    value_not_extracted: List[str] = Field(default_factory=list, description="Data available but not fully used")
    recommended_calculations: List[str] = Field(default_factory=list, description="Calculations that should be performed")


class AIAnalyzer:
    """Use GPT-4 for intelligent document analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured - AI analysis will be limited")
        
        # Load "Our Thinking" principles for comparison (Brief requirement)
        self.our_thinking = OurThinkingManager.get_our_thinking_principles()
    
    async def analyze_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform AI-powered analysis of the document
        
        Returns detailed AI insights about the document
        """
        if not self.client:
            return {
                "error": "OpenAI API not configured",
                "ai_analysis_available": False
            }
        
        try:
            # Prepare context from document
            context = self._prepare_context(doc_data)
            
            # Multiple targeted analyses with timeout
            try:
                analyses = await asyncio.wait_for(
                    self._run_all_analyses(context),
                    timeout=AI_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(f"AI analysis timed out after {AI_TIMEOUT}s - using basic analysis")
                return {
                    "ai_analysis_available": False,
                    "error": f"AI analysis timed out after {AI_TIMEOUT} seconds",
                    "focus_analysis": {"focus": "unknown"},
                    "parameter_quality": {},
                    "calculations_check": {},
                    "interventions": {},
                    "overall_quality": {}
                }
            
            return {
                "ai_analysis_available": True,
                **analyses
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                "error": str(e),
                "ai_analysis_available": False
            }
    
    def _prepare_context(self, doc_data: Dict) -> str:
        """Prepare document context for AI analysis"""
        # Take first 3000 characters for context (to manage tokens)
        text_sample = doc_data.get("text_content", "")[:3000]
        
        # Include extracted metrics if available
        metrics = doc_data.get("metrics", {})
        
        context = f"""
Document: {doc_data.get('filename', 'Unknown')}
Pages: {doc_data.get('page_count', 'Unknown')}

Parameters Found:
{json.dumps(doc_data.get('parameters_found', {}), indent=2)}

Extracted Metrics:
{json.dumps(metrics, indent=2)}

Document Text Sample:
{text_sample}
"""
        return context
    
    async def _run_all_analyses(self, context: str) -> Dict[str, Any]:
        """Run all AI analyses with individual timeouts"""
        analyses = {}
        
        # First, detect document type (this informs other analyses)
        try:
            analyses["document_type_detection"] = await asyncio.wait_for(
                self._detect_document_type(context), timeout=30
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Document type detection failed: {e}")
            analyses["document_type_detection"] = {
                "primary_type": "hybrid",
                "plan_percentage": 50,
                "report_percentage": 50,
                "error": str(e)
            }
        
        # Run analyses with individual error handling
        try:
            analyses["focus_analysis"] = await asyncio.wait_for(
                self._analyze_focus(context), timeout=30
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Focus analysis failed: {e}")
            analyses["focus_analysis"] = {"focus": "unknown", "error": str(e)}
        
        try:
            analyses["parameter_quality"] = await asyncio.wait_for(
                self._analyze_parameter_quality(context), timeout=30
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Parameter quality analysis failed: {e}")
            analyses["parameter_quality"] = {"error": str(e)}
        
        try:
            analyses["calculations_check"] = await asyncio.wait_for(
                self._check_calculations(context), timeout=30
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Calculations check failed: {e}")
            analyses["calculations_check"] = {"error": str(e)}
        
        try:
            analyses["interventions"] = await asyncio.wait_for(
                self._identify_interventions(context), timeout=30
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Interventions analysis failed: {e}")
            analyses["interventions"] = {"error": str(e)}
        
        try:
            analyses["overall_quality"] = await asyncio.wait_for(
                self._assess_overall_quality(context), timeout=30
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Overall quality analysis failed: {e}")
            analyses["overall_quality"] = {"error": str(e)}
        
        # Run hybrid analysis (retrospective + forward-looking)
        try:
            analyses["hybrid_analysis"] = await asyncio.wait_for(
                self._analyze_hybrid_aspects(context), timeout=45
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Hybrid analysis failed: {e}")
            analyses["hybrid_analysis"] = {"error": str(e)}
        
        # Run comprehensive data extraction and calculations assessment
        # This is the key improvement per client feedback
        try:
            analyses["comprehensive_analysis"] = await asyncio.wait_for(
                self.perform_comprehensive_analysis(context), timeout=60
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Comprehensive analysis failed: {e}")
            analyses["comprehensive_analysis"] = {"error": str(e)}
        
        return analyses
    
    async def _detect_document_type(self, context: str) -> Dict[str, Any]:
        """
        AI-powered document type detection using structured outputs.
        Determines whether the document is primarily a plan, report, or hybrid.
        """
        system_prompt = """You are an expert in analyzing lake management documents.
        
Most lake documents are HYBRIDS - containing both historical data/reports AND future plans.
Your job is to identify:
1. What percentage of the content is RETROSPECTIVE (reporting past data, measurements, observations)
2. What percentage of the content is FORWARD-LOOKING (future plans, recommendations, proposed actions)

Look for:
RETROSPECTIVE indicators: "was measured", "data shows", "observed", "collected in [year]", "results indicate", actual numerical data, dates in the past
FORWARD-LOOKING indicators: "will implement", "plan to", "recommend", "should", "proposed", "objectives", future dates

Set primary_type based on percentages:
- If report_percentage > 70: primary_type = "report"
- If plan_percentage > 70: primary_type = "plan"  
- Otherwise: primary_type = "hybrid"
"""
        
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this document:\n\n{context}"}
                ],
                response_format=DocumentTypeDetection,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Document type detection failed: {e}")
            return {
                "primary_type": "hybrid",
                "plan_percentage": 50,
                "report_percentage": 50,
                "error": str(e)
            }
    
    async def _analyze_hybrid_aspects(self, context: str) -> Dict[str, Any]:
        """
        Analyze the document from both retrospective and forward-looking perspectives
        using structured outputs. This is key to the hybrid analysis approach.
        """
        system_prompt = """You are an expert in lake ecology analyzing documents from multiple perspectives.

Analyze this lake management document from TWO perspectives:

1. AS A RETROSPECTIVE REPORT (analyzing past data):
   - What data/measurements are reported?
   - What time period does the data cover?
   - What trends or patterns are visible in the historical data?
   - What problems or issues were identified from the data?
   - Is the data collection frequency adequate (monthly preferred)?
   - Are depth profiles included?

2. AS A FORWARD-LOOKING PLAN (analyzing future actions):
   - What actions or interventions are proposed?
   - Do the proposed actions address ROOT CAUSES (hypoxia) or just symptoms (algae)?
   - Is there a clear timeline for implementation?
   - Are there monitoring plans for evaluating success?
   - Do the plans align with the problems identified in the data?

3. ALIGNMENT ANALYSIS:
   - Do the future plans actually address the problems shown in the historical data?
   - Are there data gaps that should be filled before planning?
   - Are there proposed solutions that ignore the root cause data?
"""
        
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this document:\n\n{context}"}
                ],
                response_format=HybridAnalysis,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Hybrid analysis failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_focus(self, context: str) -> Dict[str, Any]:
        """Analyze if document focuses on symptoms vs root causes - comparing against Our Thinking"""
        
        # Include Our Thinking principles in the prompt
        our_thinking_summary = json.dumps(self.our_thinking["core_philosophy"], indent=2)
        
        system_prompt = f"""You are an expert in lake ecology and water quality management.
Compare this report against OUR THINKING principles:

OUR THINKING:
{our_thinking_summary}

Based on the document content, determine:

1. Does this report focus on SYMPTOMS or ROOT CAUSES?
   - Symptoms: Water clarity, algae blooms, fish kills, aesthetics, TSI, chlorophyll-a
   - Root Causes: Hypoxia, nutrient cycling, benthic processes, DO profiles, orthophosphate below oxycline

2. What percentage of the content addresses root causes vs symptoms?

3. Are the recommendations targeting the actual problems or just treating symptoms?

4. How well does this align with Our Thinking that hypoxia drives HABs?
"""
        
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this document:\n\n{context}"}
                ],
                response_format=FocusAnalysis,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Focus analysis failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_parameter_quality(self, context: str) -> Dict[str, Any]:
        """Analyze how well parameters are measured using structured outputs"""
        
        system_prompt = """You are an expert in lake water quality assessment.
        
Analyze the quality of parameter measurements in this lake report:

For Dissolved Oxygen:
- Are measurements taken at multiple depths?
- Is there a complete DO profile?
- Is hypoxic volume calculated?

For Nutrients:
- Is orthophosphate measured separately from total phosphorus?
- Are measurements taken below the thermocline/oxycline?
- Is ammonia measured in hypoxic zones?

For Phytoplankton:
- Is taxonomic identification provided?
- Is biovolume measured (not just cell counts)?
- Are cyanobacteria distinguished from beneficial algae?
"""
        
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this document:\n\n{context}"}
                ],
                response_format=ParameterQualityAnalysis,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Parameter quality analysis failed: {e}")
            return {"error": str(e)}
    
    async def _check_calculations(self, context: str) -> Dict[str, Any]:
        """Check if critical calculations are performed using structured outputs"""
        
        system_prompt = """You are an expert in lake water quality assessment.
        
Check if the following critical calculations are performed in this lake report:

1. Hypoxic water volume (volume where DO < 2 mg/L)
2. Percentage of water volume that is hypoxic
3. Hypoxic sediment surface area
4. Percentage of sediment area that is hypoxic
5. Depth of oxycline/thermocline

For each calculation, determine if it's:
- "calculated": Explicitly calculated and reported
- "data_available": Data available but not calculated
- "not_possible": Cannot be determined from available data
"""
        
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this document:\n\n{context}"}
                ],
                response_format=CalculationsCheck,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Calculations check failed: {e}")
            return {"error": str(e)}
    
    async def _identify_interventions(self, context: str) -> Dict[str, Any]:
        """Identify counter-productive or ineffective interventions using structured outputs"""
        
        system_prompt = """You are an expert in lake management interventions.
        
Identify any interventions or recommendations in this lake report and classify them:

Counter-productive interventions (make problems worse):
- Chemical treatments without addressing hypoxia
- Algaecides that increase nutrient release
- Dredging that resuspends nutrients

Symptomatic treatments (don't address root cause):
- Surface skimming for algae
- Aesthetic improvements
- Fish stocking without habitat improvement

Effective interventions (address root causes):
- Hypolimnetic aeration
- Nutrient inactivation in sediments
- Watershed management
"""
        
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this document:\n\n{context}"}
                ],
                response_format=InterventionsAnalysis,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Intervention analysis failed: {e}")
            return {"error": str(e)}
    
    async def _assess_overall_quality(self, context: str) -> Dict[str, Any]:
        """Overall assessment of report quality using structured outputs"""
        
        system_prompt = """You are an expert in evaluating lake management reports.
        
Provide an overall assessment of this lake management report:

1. Does it provide actionable insights or just data?
2. Is the data presented transparently and clearly?
3. Would a lake owner understand what to do based on this report?
4. Does it follow evidence-based best practices?

Rate each aspect on a scale of 0-10 and provide specific examples.
"""
        
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this document:\n\n{context}"}
                ],
                response_format=OverallQuality,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Overall quality assessment failed: {e}")
            return {"error": str(e)}
    
    async def extract_data_values(self, context: str) -> Dict[str, Any]:
        """
        Extract actual numerical data values from the document.
        This is the key improvement per client feedback - not just checking if parameters
        are present, but extracting the actual values for analysis.
        """
        system_prompt = """You are an expert data analyst extracting specific numerical values from lake reports.

IMPORTANT: Extract ACTUAL NUMERICAL VALUES from the document, not just whether parameters are mentioned.

Look for and extract:

1. DISSOLVED OXYGEN DATA:
   - The minimum DO value found anywhere
   - The depth where minimum DO was found
   - The depth where DO drops below 2.5 mg/L (oxycline)
   - Whether measurements go all the way to the lake bottom
   - Describe the DO profile in 'do_profile_description' (e.g., "Surface 8.5mg/L, 5m 6.2mg/L, 10m 1.2mg/L")

2. NUTRIENT DATA:
   - SRP/Orthophosphate values at depth (hypolimnion) and surface
   - Ammonia values at depth (hypolimnion) and surface
   - Describe the nutrient profile in 'nutrient_profile_description'

3. LAKE MORPHOMETRY:
   - Maximum depth
   - Lake volume (in m³ or acre-feet)
   - Surface area (in hectares or acres)
   - Whether there's a hypsographic table (depth-area-volume relationships)

4. SAMPLING INFORMATION:
   - Names of sampling locations (e.g., "Deep Basin 4", "Station A")
   - Which location is deepest (most meaningful data)
   - Years for which data exists
   - Which summer months were sampled

Be specific with values. Extract actual numbers from the document."""

        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract all numerical data values from this document:\n\n{context}"}
                ],
                response_format=ExtractedDataValues,
                temperature=0.2  # Lower temperature for more precise extraction
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Data value extraction failed: {e}")
            return {"error": str(e)}
    
    async def assess_calculations(self, context: str, extracted_data: Dict) -> Dict[str, Any]:
        """
        Assess what calculations have been done and what COULD be done with available data.
        Per client feedback: identify when full value is not being extracted from the data.
        """
        # Include extracted data in the prompt for context
        data_summary = json.dumps(extracted_data, indent=2, default=str)
        
        system_prompt = f"""You are an expert in lake water quality calculations.

Based on the document and the extracted data below, assess:

1. WHAT CALCULATIONS ARE DONE in the document:
   - Is hypoxic water volume calculated? (Volume where DO < 2.5 mg/L)
   - Is hypoxic sediment area calculated?
   - Are trends analyzed year-over-year?

2. WHAT CALCULATIONS COULD BE DONE with the available data:
   - If the document has both DO profile AND hypsographic table, hypoxic volume COULD be calculated
   - If SRP data exists below oxycline AND hypoxic volume is known, Biomass Potential COULD be calculated
   
3. WHAT'S MISSING to perform important calculations:
   - For hypoxic volume: need DO profile + hypsographic table (or volume data)
   - For biomass potential: need hypoxic volume + SRP in hypolimnion

4. UNDERUTILIZED DATA - data that IS in the report but NOT being fully used:
   - Example: "DO profile exists but hypoxic volume not calculated"
   - Example: "Multiple years of data but no trend analysis"
   - Example: "SRP at depth available but not used to calculate biomass potential"

EXTRACTED DATA SUMMARY:
{data_summary}
"""

        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Assess calculations in this document:\n\n{context}"}
                ],
                response_format=AdvancedCalculations,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Calculations assessment failed: {e}")
            return {"error": str(e)}
    
    async def analyze_trends(self, context: str) -> Dict[str, Any]:
        """
        Analyze multi-year trends in the data.
        Per client feedback: provide trend analysis when multiple years available.
        """
        system_prompt = """You are an expert in analyzing long-term lake water quality trends.

Analyze this document for MULTI-YEAR TRENDS:

1. Does the document contain data from multiple years?
2. What years are covered?

3. For each major parameter, identify the TREND:
   - Dissolved Oxygen: improving (DO increasing), declining (DO decreasing), or stable?
   - Phosphorus: improving (P decreasing), declining (P increasing), or stable?
   - Cyanobacteria: improving (cyano decreasing), declining (cyano increasing), or stable?
   - Overall water quality: improving, declining, or stable?

4. Note any KEY YEAR-OVER-YEAR CHANGES mentioned in the document.
   - Example: "OP reduced from 0.27 mg/L (2021) to 0.025 mg/L (2023)"
   - Example: "Ammonia declined from 1.8 mg/L to 0.074 mg/L over 2 years"

Look for specific statements about trends, comparisons between years, and percentage changes."""

        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze trends in this document:\n\n{context}"}
                ],
                response_format=TrendAnalysis,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {"error": str(e)}
    
    async def extract_lake_background(self, context: str) -> Dict[str, Any]:
        """
        Extract History & Background information about the lake.
        Per client feedback: reports should include context about management history.
        """
        system_prompt = """You are an expert in analyzing lake management documents.

Extract HISTORY & BACKGROUND information from this document:

1. Lake name
2. When management started (year)
3. Brief history of lake management activities
4. Identified nutrient sources (e.g., septic systems, runoff, internal loading)
5. Current treatment/aeration systems in place (e.g., POAS, hypolimnetic oxygenation, etc.)
6. Any issues or problems with current systems
7. Stated management objectives/goals
8. History of HAB (Harmful Algal Bloom) events
9. Key concerns mentioned in the document

Focus on extracting FACTUAL information stated in the document."""

        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract background information:\n\n{context}"}
                ],
                response_format=LakeBackground,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Lake background extraction failed: {e}")
            return {"error": str(e)}
    
    async def extract_data_quality_checklist(self, context: str) -> Dict[str, Any]:
        """
        Extract comprehensive data quality checklist per client's specific requirements.
        This answers the exact questions the client wants answered about each report.
        """
        system_prompt = """You are an expert in analyzing lake water quality reports.

Answer this COMPREHENSIVE CHECKLIST about the document. Be specific and accurate.

DISSOLVED OXYGEN:
1. Is DO measured at regular intervals all the way to the bottom at the deepest part?
2. How often is it measured each year? (e.g., "monthly", "3 times/year", "unknown")
3. Which summer months have DO data? (June, July, August)
4. Is there multi-year DO data for trend analysis?
5. Is the oxycline depth (where DO < 2.5 mg/L) clearly identified?
6. Is a hypsographic table available (depth vs volume/area)?
7. Is hypoxic water volume actually calculated and reported?
8. Is hypoxic sediment surface area actually calculated and reported?

NUTRIENTS - PHOSPHORUS:
9. Is orthophosphate (SRP) measured?
10. Is SRP measured below the oxycline (in deep hypoxic water)?
11. Which summer months have SRP data?
12. Is there multi-year SRP data?
13. Is Phytoplankton Biomass Potential calculated?

NUTRIENTS - NITROGEN:
14. Is ammonia measured?
15. Is ammonia measured below the oxycline (in deep hypoxic water)?
16. Which summer months have ammonia data?
17. Is there multi-year ammonia data?

PHYTOPLANKTON:
18. Is detailed taxonomy provided (species identification)?
19. Is biovolume provided by taxa?
20. Is cell count provided by taxa?
21. Which summer months have phytoplankton data?
22. Is there multi-year phytoplankton data?

CALCULATIONS (if data allows us to calculate):
- If hypsographic table + oxycline depth available: Can we calculate hypoxic volume?
- If hypoxic volume + SRP in hypolimnion available: Can we calculate biomass potential?

CRITICISMS (important - be specific):
List specific criticisms of the report's analysis approach, such as:
- "Uses mean/average values which provide poor insight"
- "Fails to analyze deep water (benthic) nutrients"
- "Only surface measurements, no depth profile"
- "Sampling frequency inadequate for summer conditions"
"""

        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this report for the checklist:\n\n{context}"}
                ],
                response_format=DataQualityChecklist,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Data quality checklist extraction failed: {e}")
            return {"error": str(e)}

    async def extract_specific_values(self, context: str) -> Dict[str, Any]:
        """
        Extract SPECIFIC data values that should be highlighted in reports.
        Per client feedback: Need to show actual values like "SRP at Deep Basin 4: 0.27mg/L in 2021"
        """
        system_prompt = """You are an expert in analyzing lake water quality data.

Extract SPECIFIC DATA VALUES that should be highlighted in analysis:

1. LOCATION-SPECIFIC VALUES:
   - What is the deepest or most important sampling location? (e.g., "Deep Basin 4", "Station 1")
   - What are the DO values at that location for each year mentioned?
   - What are SRP/orthophosphate values at depth for each year?
   - What are ammonia values at depth for each year?

2. KEY YEAR-OVER-YEAR CHANGES:
   - Extract specific statements like "OP has reduced from 0.27mg/L in August 2021 to 0.025mg/L in August 2023"
   - Format as clear change statements with before/after values

3. CALCULATED VALUES (if present):
   - Hypoxic water volume (in m³)
   - Hypoxic percentage of lake
   - Any phytoplankton biomass potential calculations

IMPORTANT: Extract ACTUAL NUMERICAL VALUES from the document, not general statements."""

        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract specific values:\n\n{context}"}
                ],
                response_format=SpecificDataValues,
                temperature=0.3
            )
            
            result = response.choices[0].message.parsed
            return result.model_dump()
        except Exception as e:
            logger.error(f"Specific values extraction failed: {e}")
            return {"error": str(e)}

    async def perform_comprehensive_analysis(self, context: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis combining data extraction, calculations assessment,
        and trend analysis. This is the main entry point for advanced analysis.
        """
        result = {
            "extracted_data": {},
            "calculations_assessment": {},
            "trend_analysis": {},
            "lake_background": {},
            "specific_values": {},
            "critical_findings": [],
            "data_quality_issues": [],
            "value_not_extracted": [],
            "recommended_calculations": []
        }
        
        try:
            # Step 1: Extract data values
            extracted_data = await self.extract_data_values(context)
            result["extracted_data"] = extracted_data
            
            # Step 2: Assess calculations (using extracted data)
            calc_assessment = {}
            if not extracted_data.get("error"):
                calc_assessment = await self.assess_calculations(context, extracted_data)
                result["calculations_assessment"] = calc_assessment
            
            # Step 3: Analyze trends
            trend_analysis = await self.analyze_trends(context)
            result["trend_analysis"] = trend_analysis
            
            # Step 4: Extract lake background (NEW)
            lake_background = await self.extract_lake_background(context)
            result["lake_background"] = lake_background
            
            # Step 5: Extract specific values for reporting (NEW)
            specific_values = await self.extract_specific_values(context)
            result["specific_values"] = specific_values
            
            # Step 6: Extract comprehensive data quality checklist (NEW)
            checklist = await self.extract_data_quality_checklist(context)
            result["data_quality_checklist"] = checklist
            
            # Step 7: Generate critical findings
            result["critical_findings"] = self._generate_critical_findings(
                extracted_data, calc_assessment, trend_analysis
            )
            
            # Step 8: Identify data quality issues
            result["data_quality_issues"] = self._identify_data_quality_issues(extracted_data)
            
            # Step 9: Identify value not being extracted
            if not extracted_data.get("error") and not calc_assessment.get("error"):
                result["value_not_extracted"] = calc_assessment.get("underutilized_data", [])
            
            # Step 7: Generate recommended calculations
            result["recommended_calculations"] = self._generate_recommended_calculations(
                extracted_data, calc_assessment if not extracted_data.get("error") else {}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            result["error"] = str(e)
            return result
    
    def _generate_critical_findings(
        self, 
        extracted_data: Dict, 
        calc_assessment: Dict,
        trend_analysis: Dict
    ) -> List[str]:
        """Generate list of critical findings from the analysis"""
        findings = []
        
        # Check for severe hypoxia
        min_do = extracted_data.get("minimum_do_value")
        if min_do is not None:
            if min_do < 2:
                findings.append(f"CRITICAL: Severe hypoxia detected (DO = {min_do} mg/L)")
            elif min_do < 4:
                findings.append(f"WARNING: Moderate hypoxia detected (DO = {min_do} mg/L)")
        
        # Check for high SRP in hypolimnion
        srp_hypo = extracted_data.get("srp_in_hypolimnion")
        if srp_hypo is not None and srp_hypo > 0.1:
            findings.append(f"High phosphorus in deep water (SRP = {srp_hypo} mg/L) - significant P loading")
        
        # Check for calculations that could be done but aren't
        if calc_assessment.get("hypoxic_volume_could_be_calculated") and not calc_assessment.get("hypoxic_volume_calculated"):
            findings.append("DATA AVAILABLE but hypoxic volume NOT calculated - this should be calculated")
        
        if calc_assessment.get("biomass_potential_could_be_calculated"):
            findings.append("Phytoplankton Biomass Potential COULD be calculated from available data")
        
        # Check trends
        if trend_analysis.get("has_multi_year_data"):
            do_trend = trend_analysis.get("do_trend", "unknown")
            if do_trend == "declining":
                findings.append("CONCERNING: Dissolved oxygen trend is DECLINING over multiple years")
            elif do_trend == "improving":
                findings.append("POSITIVE: Dissolved oxygen trend is IMPROVING over multiple years")
            
            cyano_trend = trend_analysis.get("cyanobacteria_trend", "unknown")
            if cyano_trend == "declining":
                findings.append("CONCERNING: Cyanobacteria trend is INCREASING over multiple years")
            elif cyano_trend == "improving":
                findings.append("POSITIVE: Cyanobacteria trend is DECREASING over multiple years")
        
        return findings
    
    def _identify_data_quality_issues(self, extracted_data: Dict) -> List[str]:
        """Identify issues with data quality or completeness"""
        issues = []
        
        if not extracted_data.get("do_measured_at_bottom"):
            issues.append("DO not measured at lake bottom - missing critical benthic data")
        
        if not extracted_data.get("srp_in_hypolimnion"):
            issues.append("No SRP/orthophosphate data from deep water (hypolimnion)")
        
        if not extracted_data.get("ammonia_in_hypolimnion"):
            issues.append("No ammonia data from deep water (hypolimnion)")
        
        if not extracted_data.get("has_hypsographic_table"):
            issues.append("No hypsographic table - cannot calculate hypoxic volume/area")
        
        summer_months = extracted_data.get("summer_months_sampled", [])
        if len(summer_months) < 3:
            issues.append(f"Only {len(summer_months)} summer months sampled - need June, July, August minimum")
        
        years = extracted_data.get("years_with_data", [])
        if len(years) < 2:
            issues.append("Only single year of data - cannot assess trends")
        
        return issues
    
    def _generate_recommended_calculations(
        self, 
        extracted_data: Dict, 
        calc_assessment: Dict
    ) -> List[str]:
        """Generate list of recommended calculations"""
        recommendations = []
        
        # If hypoxic volume not calculated but could be
        if calc_assessment.get("hypoxic_volume_could_be_calculated") and not calc_assessment.get("hypoxic_volume_calculated"):
            recommendations.append(
                "Calculate hypoxic water volume using DO profile and lake morphometry data"
            )
        
        # If hypoxic area not calculated but could be
        if calc_assessment.get("hypoxic_area_could_be_calculated") and not calc_assessment.get("hypoxic_area_calculated"):
            recommendations.append(
                "Calculate hypoxic sediment surface area to quantify benthic stress"
            )
        
        # If biomass potential could be calculated
        if calc_assessment.get("biomass_potential_could_be_calculated"):
            recommendations.append(
                "Calculate Phytoplankton Biomass Potential: (Hypoxic Volume × SRP) × 100 = potential algal biomass in tonnes"
            )
        
        # Missing data for calculations
        missing_hypoxic = calc_assessment.get("missing_for_hypoxic_volume", [])
        if missing_hypoxic:
            recommendations.append(
                f"To calculate hypoxic volume, need: {', '.join(missing_hypoxic)}"
            )
        
        missing_biomass = calc_assessment.get("missing_for_biomass_potential", [])
        if missing_biomass:
            recommendations.append(
                f"To calculate biomass potential, need: {', '.join(missing_biomass)}"
            )
        
        return recommendations

class AIEnhancedCompliance:
    """Combine rule-based compliance with AI insights"""
    
    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
    
    async def enhanced_evaluation(self, doc_data: Dict, compliance_eval: Dict) -> Dict:
        """Enhance compliance evaluation with AI insights"""
        
        # Get AI analysis
        ai_analysis = await self.ai_analyzer.analyze_document(doc_data)
        
        # Merge insights
        enhanced = {
            **compliance_eval,
            "ai_insights": ai_analysis
        }
        
        # Adjust score based on AI findings
        if ai_analysis.get("ai_analysis_available"):
            # Adjust for focus on root causes
            focus = ai_analysis.get("focus_analysis", {})
            if focus.get("focus") == "root_causes":
                enhanced["overall_score"] += 10
                enhanced["strengths"].append("Focuses on root causes rather than symptoms")
            elif focus.get("focus") == "symptoms":
                enhanced["overall_score"] -= 10
                enhanced["weaknesses"].append("Primarily focuses on symptoms rather than root causes")
            
            # Adjust for intervention quality
            interventions = ai_analysis.get("interventions", {})
            if interventions.get("counter_productive"):
                enhanced["overall_score"] -= 5 * len(interventions["counter_productive"])
                enhanced["red_flags"].extend([
                    f"Counter-productive intervention: {i}" 
                    for i in interventions["counter_productive"]
                ])
            
            # NEW: Process comprehensive analysis results
            comp_analysis = ai_analysis.get("comprehensive_analysis", {})
            if comp_analysis and not comp_analysis.get("error"):
                # Add critical findings to evaluation
                critical_findings = comp_analysis.get("critical_findings", [])
                for finding in critical_findings:
                    if "CRITICAL" in finding or "CONCERNING" in finding:
                        enhanced["red_flags"].append(finding)
                    elif "POSITIVE" in finding:
                        enhanced["strengths"].append(finding)
                    elif "DATA AVAILABLE" in finding:
                        enhanced["weaknesses"].append(finding)
                
                # Add data quality issues
                data_issues = comp_analysis.get("data_quality_issues", [])
                for issue in data_issues:
                    enhanced["weaknesses"].append(f"Data quality: {issue}")
                
                # Add value not extracted
                value_missed = comp_analysis.get("value_not_extracted", [])
                for missed in value_missed:
                    enhanced["weaknesses"].append(f"Underutilized data: {missed}")
                
                # Add recommended calculations to recommendations
                recommended_calcs = comp_analysis.get("recommended_calculations", [])
                for rec_calc in recommended_calcs:
                    enhanced["recommendations"].append({
                        "priority": "HIGH",
                        "category": "Missing Calculation",
                        "recommendation": rec_calc,
                        "explanation": "This calculation could be performed with available data"
                    })
                
                # Add trend analysis results
                trend_analysis = comp_analysis.get("trend_analysis", {})
                if trend_analysis.get("has_multi_year_data"):
                    enhanced["strengths"].append(
                        f"Multi-year data available ({len(trend_analysis.get('years_analyzed', []))} years)"
                    )
                    key_changes = trend_analysis.get("key_changes", [])
                    for change in key_changes[:3]:  # Top 3 changes
                        enhanced["strengths"].append(f"Year-over-year change: {change}")
                
                # Store comprehensive analysis for report generation
                enhanced["comprehensive_analysis"] = comp_analysis
                
                # Store extracted data values for report
                extracted_data = comp_analysis.get("extracted_data", {})
                enhanced["extracted_data_values"] = extracted_data
                
                # Adjust score based on data completeness
                if extracted_data.get("do_measured_at_bottom"):
                    enhanced["overall_score"] += 5
                if extracted_data.get("srp_in_hypolimnion"):
                    enhanced["overall_score"] += 5
                if extracted_data.get("has_hypsographic_table"):
                    enhanced["overall_score"] += 5
                
                # Penalty for calculations that could be done but aren't
                calc_assessment = comp_analysis.get("calculations_assessment", {})
                if calc_assessment.get("hypoxic_volume_could_be_calculated") and not calc_assessment.get("hypoxic_volume_calculated"):
                    enhanced["overall_score"] -= 10
                    enhanced["weaknesses"].append("Hypoxic volume COULD be calculated but ISN'T - major gap")
        
        # Recalculate percentage
        enhanced["compliance_percentage"] = max(0, min(100, enhanced["overall_score"]))
        
        return enhanced
    
    async def analyze_document_with_type(self, doc_data: Dict, compliance_eval: Dict, document_type: str) -> Dict:
        """Enhanced AI analysis that considers document type"""
        
        # Add document type context
        doc_data_with_type = {**doc_data, "document_type": document_type}
        
        # Get standard AI analysis
        ai_analysis = await self.ai_analyzer.analyze_document(doc_data_with_type)
        
        # Add type-specific insights
        if document_type == 'plan':
            ai_analysis['plan_analysis'] = {
                'addresses_root_causes': self._check_plan_root_causes(doc_data),
                'intervention_quality': self._assess_planned_interventions(doc_data),
                'timeline_feasibility': self._check_timeline(doc_data)
            }
        else:  # report
            ai_analysis['report_analysis'] = {
                'data_quality': self._assess_data_quality(doc_data),
                'trend_indicators': self._identify_trends(doc_data),
                'urgency_level': self._assess_urgency(doc_data, compliance_eval)
            }
        
        return ai_analysis
    
    def _check_plan_root_causes(self, doc_data: Dict) -> str:
        """Check if plan addresses root causes"""
        text = doc_data.get('text_content', '').lower()
        if 'hypoxia' in text or 'dissolved oxygen' in text:
            return "Addresses hypoxia - good focus on root causes"
        return "Does not address hypoxia - missing root cause focus"
    
    def _assess_planned_interventions(self, doc_data: Dict) -> str:
        """Assess quality of planned interventions"""
        text = doc_data.get('text_content', '').lower()
        good_interventions = ['aeration', 'destratification', 'oxygenation']
        bad_interventions = ['algaecide', 'chemical', 'copper sulfate']
        
        if any(term in text for term in good_interventions):
            return "Includes appropriate interventions targeting root causes"
        elif any(term in text for term in bad_interventions):
            return "Relies on chemical treatments - only addresses symptoms"
        return "Intervention strategy unclear"
    
    def _check_timeline(self, doc_data: Dict) -> str:
        """Check if plan has realistic timeline"""
        text = doc_data.get('text_content', '').lower()
        if 'timeline' in text or 'schedule' in text or 'phase' in text:
            return "Has implementation timeline"
        return "No clear timeline specified"
    
    def _assess_data_quality(self, doc_data: Dict) -> str:
        """Assess quality of data in report"""
        metrics = doc_data.get('metrics', {})
        if metrics.get('dissolved_oxygen_values'):
            return "Contains quantitative measurements"
        return "Lacks quantitative data"
    
    def _identify_trends(self, doc_data: Dict) -> str:
        """Identify trends in data"""
        text = doc_data.get('text_content', '').lower()
        if 'increase' in text or 'decrease' in text or 'trend' in text:
            return "Shows temporal trends"
        return "No trend analysis"
    
    def _assess_urgency(self, doc_data: Dict, compliance_eval: Dict) -> str:
        """Assess urgency level based on findings"""
        score = compliance_eval.get('compliance_percentage', 100)
        if score < 40:
            return "URGENT - Immediate action needed"
        elif score < 60:
            return "MODERATE - Action needed soon"
        return "ROUTINE - Continue monitoring"
