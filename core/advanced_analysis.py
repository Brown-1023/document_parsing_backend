"""
Advanced Analysis Module
Implements the sophisticated analysis requirements from client feedback:
1. Extract actual data values from documents
2. Detect hypsographic tables
3. Calculate hypoxic volume/area if data available
4. Calculate Phytoplankton Biomass Potential
5. Perform multi-year trend analysis
6. Provide detailed checklist-based assessment
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


# ============================================
# Pydantic Models for Structured Data Extraction
# ============================================

class ExtractedDOData(BaseModel):
    """Extracted Dissolved Oxygen data from document"""
    has_do_measurements: bool = Field(default=False, description="Whether DO measurements are present")
    do_values: List[float] = Field(default_factory=list, description="DO values found (mg/L)")
    depths_measured: List[float] = Field(default_factory=list, description="Depths at which DO was measured (m)")
    measurement_locations: List[str] = Field(default_factory=list, description="Location names where measured")
    oxycline_depth: Optional[float] = Field(default=None, description="Depth where DO drops below 2.5 mg/L")
    minimum_do: Optional[float] = Field(default=None, description="Minimum DO value found")
    measured_to_bottom: bool = Field(default=False, description="Whether measurements extend to lake bottom")
    measurement_frequency: str = Field(default="unknown", description="How often DO is measured")
    summer_months_covered: List[str] = Field(default_factory=list, description="Summer months with data")


class ExtractedNutrientData(BaseModel):
    """Extracted nutrient data from document"""
    has_orthophosphate: bool = Field(default=False, description="Whether SRP/orthophosphate is measured")
    has_ammonia: bool = Field(default=False, description="Whether ammonia is measured")
    orthophosphate_values: List[float] = Field(default_factory=list, description="SRP values (mg/L)")
    ammonia_values: List[float] = Field(default_factory=list, description="Ammonia values (mg/L)")
    srp_below_oxycline: Optional[float] = Field(default=None, description="SRP value below oxycline")
    ammonia_below_oxycline: Optional[float] = Field(default=None, description="Ammonia value below oxycline")
    measured_at_depth: bool = Field(default=False, description="Whether nutrients measured at depth")
    hypolimnion_srp: Optional[float] = Field(default=None, description="SRP in hypolimnion (mg/L)")


class ExtractedPhytoplanktonData(BaseModel):
    """Extracted phytoplankton data from document"""
    has_taxonomy: bool = Field(default=False, description="Whether taxonomic data is provided")
    has_biovolume: bool = Field(default=False, description="Whether biovolume is measured")
    has_cell_counts: bool = Field(default=False, description="Whether cell counts are provided")
    cyanobacteria_percentage: Optional[float] = Field(default=None, description="Percentage of cyanobacteria")
    toxin_producers_identified: bool = Field(default=False, description="Whether toxin producers are identified")
    beneficial_algae_percentage: Optional[float] = Field(default=None, description="Percentage of beneficial algae")
    species_list: List[str] = Field(default_factory=list, description="Species identified")
    total_biovolume: Optional[float] = Field(default=None, description="Total phytoplankton biovolume")


class HypsographicData(BaseModel):
    """Hypsographic (depth-area-volume) data from document"""
    has_hypsographic_table: bool = Field(default=False, description="Whether hypsographic table is present")
    has_bathymetry_map: bool = Field(default=False, description="Whether bathymetry map is present")
    max_depth: Optional[float] = Field(default=None, description="Maximum lake depth (m)")
    total_volume: Optional[float] = Field(default=None, description="Total lake volume (m³)")
    total_surface_area: Optional[float] = Field(default=None, description="Total surface area (m² or hectares)")
    depth_volume_pairs: List[Dict[str, float]] = Field(default_factory=list, description="Depth:Volume pairs")
    depth_area_pairs: List[Dict[str, float]] = Field(default_factory=list, description="Depth:Area pairs")
    can_calculate_hypoxic_volume: bool = Field(default=False, description="Whether hypoxic volume can be calculated")


class MultiYearData(BaseModel):
    """Multi-year data for trend analysis"""
    years_with_data: List[int] = Field(default_factory=list, description="Years with available data")
    has_trend_data: bool = Field(default=False, description="Whether multi-year trend data is available")
    data_span_years: int = Field(default=0, description="Number of years data spans")
    parameter_trends: Dict[str, str] = Field(default_factory=dict, description="Trend direction for each parameter")


class CalculatedMetrics(BaseModel):
    """Calculated metrics based on extracted data"""
    hypoxic_water_volume: Optional[float] = Field(default=None, description="Volume where DO < 2.5 mg/L (m³)")
    hypoxic_volume_percentage: Optional[float] = Field(default=None, description="Percentage of lake that is hypoxic")
    hypoxic_sediment_area: Optional[float] = Field(default=None, description="Sediment area under hypoxic water (m²)")
    hypoxic_area_percentage: Optional[float] = Field(default=None, description="Percentage of sediment under hypoxic water")
    phytoplankton_biomass_potential: Optional[float] = Field(default=None, description="Potential algal biomass (kg)")
    biomass_potential_tonnes: Optional[float] = Field(default=None, description="Potential algal biomass (tonnes)")
    calculation_notes: List[str] = Field(default_factory=list, description="Notes about calculations performed")


class DetailedChecklist(BaseModel):
    """Detailed checklist per client requirements"""
    # Dissolved Oxygen checklist
    do_measured_to_bottom: bool = Field(default=False)
    do_measurement_frequency: str = Field(default="unknown")
    do_summer_months_complete: bool = Field(default=False)
    do_multi_year_available: bool = Field(default=False)
    do_hypoxia_depth_identified: bool = Field(default=False)
    
    # Nutrients checklist
    srp_measured: bool = Field(default=False)
    srp_below_oxycline: bool = Field(default=False)
    ammonia_measured: bool = Field(default=False)
    ammonia_below_oxycline: bool = Field(default=False)
    nutrients_summer_months: bool = Field(default=False)
    nutrients_multi_year: bool = Field(default=False)
    
    # Phytoplankton checklist
    phyto_taxonomy: bool = Field(default=False)
    phyto_biovolume_by_taxa: bool = Field(default=False)
    phyto_cell_count_by_taxa: bool = Field(default=False)
    phyto_summer_months: bool = Field(default=False)
    phyto_multi_year: bool = Field(default=False)
    
    # Data availability
    hypsographic_available: bool = Field(default=False)
    can_calculate_hypoxic_volume: bool = Field(default=False)
    can_calculate_biomass_potential: bool = Field(default=False)


class ComprehensiveDataExtraction(BaseModel):
    """Complete data extraction result"""
    do_data: ExtractedDOData = Field(default_factory=ExtractedDOData)
    nutrient_data: ExtractedNutrientData = Field(default_factory=ExtractedNutrientData)
    phytoplankton_data: ExtractedPhytoplanktonData = Field(default_factory=ExtractedPhytoplanktonData)
    hypsographic_data: HypsographicData = Field(default_factory=HypsographicData)
    multi_year_data: MultiYearData = Field(default_factory=MultiYearData)
    calculated_metrics: CalculatedMetrics = Field(default_factory=CalculatedMetrics)
    checklist: DetailedChecklist = Field(default_factory=DetailedChecklist)
    extraction_quality: str = Field(default="basic", description="Quality of data extraction")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from data")
    data_gaps: List[str] = Field(default_factory=list, description="Important data gaps identified")
    value_not_extracted: List[str] = Field(default_factory=list, description="Available data not fully utilized")


# ============================================
# Analysis Functions
# ============================================

class AdvancedDataExtractor:
    """Extract detailed data from lake management documents"""
    
    def __init__(self):
        self.summer_months = ['june', 'july', 'august', 'september']
    
    def extract_all_data(self, doc_data: Dict[str, Any]) -> ComprehensiveDataExtraction:
        """
        Extract all relevant data from a document.
        Returns comprehensive extraction with calculations.
        """
        text_content = doc_data.get('text_content', '').lower()
        metrics = doc_data.get('metrics', {})
        
        result = ComprehensiveDataExtraction()
        
        # Extract different data types
        result.do_data = self._extract_do_data(text_content, metrics)
        result.nutrient_data = self._extract_nutrient_data(text_content, metrics)
        result.phytoplankton_data = self._extract_phytoplankton_data(text_content, metrics)
        result.hypsographic_data = self._extract_hypsographic_data(text_content, metrics)
        result.multi_year_data = self._extract_multi_year_data(text_content)
        
        # Perform calculations if possible
        result.calculated_metrics = self._perform_calculations(
            result.do_data,
            result.nutrient_data,
            result.hypsographic_data
        )
        
        # Generate checklist
        result.checklist = self._generate_checklist(result)
        
        # Identify insights and gaps
        result.key_insights = self._identify_key_insights(result)
        result.data_gaps = self._identify_data_gaps(result)
        result.value_not_extracted = self._identify_missed_value(result)
        
        # Assess extraction quality
        result.extraction_quality = self._assess_extraction_quality(result)
        
        return result
    
    def _extract_do_data(self, text: str, metrics: Dict) -> ExtractedDOData:
        """Extract dissolved oxygen data"""
        data = ExtractedDOData()
        
        # Check for DO measurements
        do_patterns = [
            r'dissolved oxygen[:\s]+(\d+\.?\d*)\s*mg/?l',
            r'do[:\s]+(\d+\.?\d*)\s*mg/?l',
            r'(\d+\.?\d*)\s*mg/?l\s+(?:dissolved oxygen|do)',
            r'oxygen[:\s]+(\d+\.?\d*)\s*mg/?l'
        ]
        
        do_values = []
        for pattern in do_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            do_values.extend([float(m) for m in matches])
        
        if do_values or metrics.get('dissolved_oxygen_values'):
            data.has_do_measurements = True
            data.do_values = do_values or metrics.get('dissolved_oxygen_values', [])
            if data.do_values:
                data.minimum_do = min(data.do_values)
        
        # Extract depths
        depth_patterns = [
            r'(\d+\.?\d*)\s*(?:m|meter|metre)s?\s*(?:depth|deep)',
            r'depth[:\s]+(\d+\.?\d*)\s*(?:m|meter)',
            r'at\s+(\d+\.?\d*)\s*(?:m|meter)'
        ]
        
        for pattern in depth_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            data.depths_measured.extend([float(m) for m in matches])
        
        # Check if measured to bottom
        bottom_indicators = ['bottom', 'deepest', 'maximum depth', 'near-bottom', 'benthic']
        data.measured_to_bottom = any(ind in text for ind in bottom_indicators)
        
        # Check measurement frequency
        if 'monthly' in text:
            data.measurement_frequency = 'monthly'
        elif 'weekly' in text:
            data.measurement_frequency = 'weekly'
        elif 'quarterly' in text:
            data.measurement_frequency = 'quarterly'
        elif 'annual' in text or 'yearly' in text:
            data.measurement_frequency = 'annual'
        
        # Check summer months coverage
        for month in self.summer_months:
            if month in text:
                data.summer_months_covered.append(month)
        
        # Calculate oxycline depth if possible
        if data.do_values and data.depths_measured and len(data.do_values) == len(data.depths_measured):
            for i, do_val in enumerate(data.do_values):
                if do_val < 2.5:
                    data.oxycline_depth = data.depths_measured[i]
                    break
        
        return data
    
    def _extract_nutrient_data(self, text: str, metrics: Dict) -> ExtractedNutrientData:
        """Extract nutrient data (phosphorus, nitrogen)"""
        data = ExtractedNutrientData()
        
        # Check for orthophosphate/SRP
        srp_patterns = [
            r'(?:ortho-?phosphate|srp|soluble reactive phosphorus)[:\s]+(\d+\.?\d*)\s*(?:mg/?l|µg/?l|ug/?l)',
            r'(\d+\.?\d*)\s*(?:mg/?l|µg/?l)\s+(?:ortho-?phosphate|srp)',
            r'po4[:\s]+(\d+\.?\d*)\s*(?:mg/?l|µg/?l)'
        ]
        
        for pattern in srp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                data.has_orthophosphate = True
                data.orthophosphate_values.extend([float(m) for m in matches])
        
        # Check for ammonia
        ammonia_patterns = [
            r'ammonia[:\s]+(\d+\.?\d*)\s*(?:mg/?l|µg/?l)',
            r'nh[34][:\s]+(\d+\.?\d*)\s*(?:mg/?l|µg/?l)',
            r'ammonium[:\s]+(\d+\.?\d*)\s*(?:mg/?l|µg/?l)'
        ]
        
        for pattern in ammonia_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                data.has_ammonia = True
                data.ammonia_values.extend([float(m) for m in matches])
        
        # Check if measured at depth
        depth_indicators = ['hypolimnion', 'bottom', 'below thermocline', 'below oxycline', 'deep water']
        data.measured_at_depth = any(ind in text for ind in depth_indicators)
        
        # Look for specific bottom/hypolimnion values
        hypo_srp_pattern = r'(?:hypolimnion|bottom|deep)[^.]*(?:ortho-?phosphate|srp)[:\s]+(\d+\.?\d*)'
        hypo_matches = re.findall(hypo_srp_pattern, text, re.IGNORECASE)
        if hypo_matches:
            data.hypolimnion_srp = float(hypo_matches[0])
            data.srp_below_oxycline = data.hypolimnion_srp
        elif data.orthophosphate_values and data.measured_at_depth:
            # Use max value as likely hypolimnion value
            data.hypolimnion_srp = max(data.orthophosphate_values)
        
        return data
    
    def _extract_phytoplankton_data(self, text: str, metrics: Dict) -> ExtractedPhytoplanktonData:
        """Extract phytoplankton data"""
        data = ExtractedPhytoplanktonData()
        
        # Check for taxonomy
        taxonomy_indicators = ['taxonomy', 'taxonomic', 'species', 'genus', 'genera', 'identified']
        data.has_taxonomy = any(ind in text for ind in taxonomy_indicators)
        
        # Check for biovolume
        biovolume_indicators = ['biovolume', 'bio-volume', 'biomass', 'µm³', 'um3']
        data.has_biovolume = any(ind in text for ind in biovolume_indicators)
        
        # Check for cell counts
        cell_count_indicators = ['cell count', 'cells/ml', 'cells per', 'cell density']
        data.has_cell_counts = any(ind in text for ind in cell_count_indicators)
        
        # Check for toxin producer identification
        toxin_indicators = ['toxin', 'microcystin', 'anatoxin', 'cylindrospermopsin', 'toxic']
        data.toxin_producers_identified = any(ind in text for ind in toxin_indicators)
        
        # Extract cyanobacteria percentage if mentioned
        cyano_pct_pattern = r'cyanobacteria[:\s]+(\d+\.?\d*)\s*%'
        cyano_matches = re.findall(cyano_pct_pattern, text, re.IGNORECASE)
        if cyano_matches:
            data.cyanobacteria_percentage = float(cyano_matches[0])
        
        # Look for common species names
        common_species = [
            'microcystis', 'anabaena', 'aphanizomenon', 'cylindrospermopsis',
            'planktothrix', 'dolichospermum', 'oscillatoria', 'nostoc'
        ]
        for species in common_species:
            if species in text:
                data.species_list.append(species)
        
        return data
    
    def _extract_hypsographic_data(self, text: str, metrics: Dict) -> HypsographicData:
        """Extract hypsographic (depth-area-volume) data"""
        data = HypsographicData()
        
        # Check for hypsographic table indicators
        hypso_indicators = [
            'hypsographic', 'depth-area', 'depth-volume', 'area-volume',
            'morphometric', 'bathymetric table', 'volume at depth'
        ]
        data.has_hypsographic_table = any(ind in text for ind in hypso_indicators)
        
        # Check for bathymetry map
        bathy_indicators = ['bathymetry', 'bathymetric map', 'depth contour', 'isobath']
        data.has_bathymetry_map = any(ind in text for ind in bathy_indicators)
        
        # Extract max depth
        max_depth_pattern = r'(?:maximum|max|deepest|greatest)\s*depth[:\s]+(\d+\.?\d*)\s*(?:m|meter|ft|feet)'
        depth_matches = re.findall(max_depth_pattern, text, re.IGNORECASE)
        if depth_matches:
            data.max_depth = float(depth_matches[0])
        
        # Extract total volume
        volume_patterns = [
            r'(?:total|lake)\s*volume[:\s]+(\d+[\d,\.]*)\s*(?:m³|m3|cubic meter|acre-feet)',
            r'volume[:\s]+(\d+[\d,\.]*)\s*(?:m³|m3|cubic meter)'
        ]
        for pattern in volume_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Remove commas and convert
                vol_str = matches[0].replace(',', '')
                data.total_volume = float(vol_str)
                break
        
        # Extract surface area
        area_patterns = [
            r'(?:surface|lake)\s*area[:\s]+(\d+[\d,\.]*)\s*(?:ha|hectare|acre|m²|km²)',
            r'area[:\s]+(\d+[\d,\.]*)\s*(?:ha|hectare|acre)'
        ]
        for pattern in area_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                area_str = matches[0].replace(',', '')
                data.total_surface_area = float(area_str)
                break
        
        # Determine if hypoxic volume can be calculated
        data.can_calculate_hypoxic_volume = (
            data.has_hypsographic_table or 
            (data.total_volume is not None and data.max_depth is not None)
        )
        
        return data
    
    def _extract_multi_year_data(self, text: str) -> MultiYearData:
        """Extract multi-year trend data"""
        data = MultiYearData()
        
        # Find years mentioned
        year_pattern = r'\b(20[0-2][0-9])\b'
        years_found = set(int(y) for y in re.findall(year_pattern, text))
        
        if years_found:
            data.years_with_data = sorted(list(years_found))
            data.data_span_years = max(years_found) - min(years_found) + 1
            data.has_trend_data = len(years_found) >= 2
        
        # Look for trend indicators
        trend_patterns = {
            'increasing': ['increas', 'rising', 'went up', 'higher than'],
            'decreasing': ['decreas', 'declining', 'went down', 'lower than', 'reduced'],
            'stable': ['stable', 'unchanged', 'similar to', 'consistent']
        }
        
        parameters = ['phosphorus', 'nitrogen', 'dissolved oxygen', 'do', 'clarity', 'cyanobacteria']
        
        for param in parameters:
            if param in text:
                for trend, indicators in trend_patterns.items():
                    # Look for trend near parameter mention
                    for indicator in indicators:
                        pattern = f'{param}[^.]*{indicator}|{indicator}[^.]*{param}'
                        if re.search(pattern, text, re.IGNORECASE):
                            data.parameter_trends[param] = trend
                            break
        
        return data
    
    def _perform_calculations(
        self,
        do_data: ExtractedDOData,
        nutrient_data: ExtractedNutrientData,
        hypso_data: HypsographicData
    ) -> CalculatedMetrics:
        """
        Perform actual calculations based on extracted data.
        This is the key improvement per client feedback.
        """
        metrics = CalculatedMetrics()
        
        # Calculate hypoxic volume if possible
        if hypso_data.can_calculate_hypoxic_volume and do_data.oxycline_depth is not None:
            if hypso_data.total_volume and hypso_data.max_depth:
                # Simplified calculation: estimate hypoxic volume based on oxycline depth
                # More sophisticated would use actual hypsographic curve
                hypoxic_depth_fraction = (hypso_data.max_depth - do_data.oxycline_depth) / hypso_data.max_depth
                
                # Lakes typically have cone-like shape, so volume fraction is cubic
                estimated_hypoxic_fraction = hypoxic_depth_fraction ** 2  # Approximation
                
                metrics.hypoxic_water_volume = hypso_data.total_volume * estimated_hypoxic_fraction
                metrics.hypoxic_volume_percentage = estimated_hypoxic_fraction * 100
                
                metrics.calculation_notes.append(
                    f"Hypoxic volume estimated based on oxycline depth ({do_data.oxycline_depth}m) "
                    f"and total volume ({hypso_data.total_volume:,.0f} m³)"
                )
        
        # Calculate hypoxic sediment area if possible
        if hypso_data.total_surface_area and metrics.hypoxic_volume_percentage:
            # Estimate sediment area based on hypoxic fraction
            # In reality, this should use actual bathymetric contours
            estimated_area_fraction = (metrics.hypoxic_volume_percentage / 100) ** 0.5
            metrics.hypoxic_sediment_area = hypso_data.total_surface_area * estimated_area_fraction
            metrics.hypoxic_area_percentage = estimated_area_fraction * 100
            
            metrics.calculation_notes.append(
                f"Hypoxic sediment area estimated: {metrics.hypoxic_sediment_area:,.0f} m²"
            )
        
        # Calculate Phytoplankton Biomass Potential
        # Per client: Hypoxic volume × SRP concentration = Potential P available
        # P × 100 = Potential algal biomass
        if metrics.hypoxic_water_volume and nutrient_data.hypolimnion_srp:
            # Convert SRP from mg/L to g/m³ (they're equivalent)
            srp_g_per_m3 = nutrient_data.hypolimnion_srp
            
            # Total available phosphorus in hypoxic layer (grams)
            total_p_grams = metrics.hypoxic_water_volume * srp_g_per_m3
            
            # Convert to kg
            total_p_kg = total_p_grams / 1000
            
            # Potential biomass (using ~100:1 ratio for algae C:P by mass)
            # This is a simplified calculation based on Redfield ratios
            metrics.phytoplankton_biomass_potential = total_p_kg * 100
            metrics.biomass_potential_tonnes = metrics.phytoplankton_biomass_potential / 1000
            
            metrics.calculation_notes.append(
                f"Phytoplankton Biomass Potential: {metrics.biomass_potential_tonnes:.2f} tonnes "
                f"(based on {total_p_kg:.1f} kg available P in hypoxic layer)"
            )
        elif nutrient_data.hypolimnion_srp and not metrics.hypoxic_water_volume:
            metrics.calculation_notes.append(
                "Cannot calculate Biomass Potential: SRP data available but hypoxic volume unknown. "
                "Need hypsographic table to calculate volume."
            )
        elif metrics.hypoxic_water_volume and not nutrient_data.hypolimnion_srp:
            metrics.calculation_notes.append(
                "Cannot calculate Biomass Potential: Hypoxic volume available but no SRP data "
                "from below oxycline. Need orthophosphate measurements at depth."
            )
        
        return metrics
    
    def _generate_checklist(self, result: ComprehensiveDataExtraction) -> DetailedChecklist:
        """Generate detailed assessment checklist per client requirements"""
        checklist = DetailedChecklist()
        
        # DO checklist
        checklist.do_measured_to_bottom = result.do_data.measured_to_bottom
        checklist.do_measurement_frequency = result.do_data.measurement_frequency
        checklist.do_summer_months_complete = len(result.do_data.summer_months_covered) >= 3
        checklist.do_multi_year_available = result.multi_year_data.has_trend_data
        checklist.do_hypoxia_depth_identified = result.do_data.oxycline_depth is not None
        
        # Nutrient checklist
        checklist.srp_measured = result.nutrient_data.has_orthophosphate
        checklist.srp_below_oxycline = result.nutrient_data.srp_below_oxycline is not None
        checklist.ammonia_measured = result.nutrient_data.has_ammonia
        checklist.ammonia_below_oxycline = result.nutrient_data.ammonia_below_oxycline is not None
        checklist.nutrients_multi_year = result.multi_year_data.has_trend_data
        
        # Phytoplankton checklist
        checklist.phyto_taxonomy = result.phytoplankton_data.has_taxonomy
        checklist.phyto_biovolume_by_taxa = result.phytoplankton_data.has_biovolume
        checklist.phyto_cell_count_by_taxa = result.phytoplankton_data.has_cell_counts
        checklist.phyto_multi_year = result.multi_year_data.has_trend_data
        
        # Data availability
        checklist.hypsographic_available = result.hypsographic_data.has_hypsographic_table
        checklist.can_calculate_hypoxic_volume = result.calculated_metrics.hypoxic_water_volume is not None
        checklist.can_calculate_biomass_potential = result.calculated_metrics.phytoplankton_biomass_potential is not None
        
        return checklist
    
    def _identify_key_insights(self, result: ComprehensiveDataExtraction) -> List[str]:
        """Identify key insights from the extracted data"""
        insights = []
        
        # DO insights
        if result.do_data.minimum_do is not None:
            if result.do_data.minimum_do < 2:
                insights.append(f"CRITICAL: Severe hypoxia detected (minimum DO: {result.do_data.minimum_do} mg/L)")
            elif result.do_data.minimum_do < 4:
                insights.append(f"WARNING: Moderate hypoxia detected (minimum DO: {result.do_data.minimum_do} mg/L)")
        
        if result.do_data.oxycline_depth:
            insights.append(f"Oxycline identified at {result.do_data.oxycline_depth}m depth")
        
        # Nutrient insights
        if result.nutrient_data.hypolimnion_srp:
            if result.nutrient_data.hypolimnion_srp > 0.1:
                insights.append(f"High SRP in hypolimnion ({result.nutrient_data.hypolimnion_srp} mg/L) indicates significant P loading")
        
        # Calculation insights
        if result.calculated_metrics.biomass_potential_tonnes:
            insights.append(
                f"Calculated {result.calculated_metrics.biomass_potential_tonnes:.1f} tonnes of potential algal bloom capacity "
                f"stored in hypoxic water"
            )
        
        # Trend insights
        if result.multi_year_data.has_trend_data:
            for param, trend in result.multi_year_data.parameter_trends.items():
                insights.append(f"Multi-year trend for {param}: {trend}")
        
        return insights
    
    def _identify_data_gaps(self, result: ComprehensiveDataExtraction) -> List[str]:
        """Identify important data gaps"""
        gaps = []
        
        # DO gaps
        if not result.do_data.has_do_measurements:
            gaps.append("No dissolved oxygen data found")
        elif not result.do_data.measured_to_bottom:
            gaps.append("DO not measured to lake bottom - missing critical benthic data")
        
        if result.do_data.measurement_frequency not in ['monthly', 'weekly']:
            gaps.append(f"DO measurement frequency ({result.do_data.measurement_frequency}) is insufficient - monthly required")
        
        # Nutrient gaps
        if not result.nutrient_data.has_orthophosphate:
            gaps.append("Missing orthophosphate (SRP) measurements - critical for understanding P availability")
        elif not result.nutrient_data.measured_at_depth:
            gaps.append("SRP not measured below oxycline - missing critical hypolimnetic P data")
        
        if not result.nutrient_data.has_ammonia:
            gaps.append("Missing ammonia measurements in hypoxic zone")
        
        # Phytoplankton gaps
        if not result.phytoplankton_data.has_taxonomy:
            gaps.append("Missing detailed phytoplankton taxonomy")
        if not result.phytoplankton_data.has_biovolume:
            gaps.append("Missing phytoplankton biovolume data - cell counts alone are insufficient")
        if not result.phytoplankton_data.toxin_producers_identified:
            gaps.append("Toxin-producing species not identified")
        
        # Hypsographic gaps
        if not result.hypsographic_data.has_hypsographic_table:
            gaps.append("No hypsographic table available - cannot calculate hypoxic volume")
        
        # Multi-year gaps
        if not result.multi_year_data.has_trend_data:
            gaps.append("Only single year data available - cannot assess trends")
        
        return gaps
    
    def _identify_missed_value(self, result: ComprehensiveDataExtraction) -> List[str]:
        """
        Identify where full value is NOT being extracted from available data.
        This is per client feedback about extracting full value.
        """
        missed = []
        
        # DO data available but not fully utilized
        if result.do_data.has_do_measurements and not result.do_data.oxycline_depth:
            missed.append("DO data available but oxycline depth not calculated")
        
        # Hypsographic data available but not used for calculations
        if result.hypsographic_data.has_hypsographic_table:
            if not result.calculated_metrics.hypoxic_water_volume:
                missed.append("Hypsographic table available but hypoxic volume not calculated")
            if not result.calculated_metrics.hypoxic_sediment_area:
                missed.append("Hypsographic table available but hypoxic sediment area not calculated")
        
        # Both DO and hypsographic available but no integration
        if result.do_data.has_do_measurements and result.hypsographic_data.total_volume:
            if not result.calculated_metrics.hypoxic_volume_percentage:
                missed.append("Both DO profile and lake volume available - should calculate hypoxic percentage")
        
        # SRP and hypoxic volume available but biomass not calculated
        if result.nutrient_data.hypolimnion_srp and result.calculated_metrics.hypoxic_water_volume:
            if not result.calculated_metrics.phytoplankton_biomass_potential:
                missed.append("Both SRP and hypoxic volume available - should calculate biomass potential")
        
        # Multi-year data available but no trend analysis
        if len(result.multi_year_data.years_with_data) >= 3:
            if not result.multi_year_data.parameter_trends:
                missed.append("Multiple years of data available but no trend analysis performed")
        
        return missed
    
    def _assess_extraction_quality(self, result: ComprehensiveDataExtraction) -> str:
        """Assess overall quality of data extraction"""
        score = 0
        
        # DO quality
        if result.do_data.has_do_measurements:
            score += 1
        if result.do_data.measured_to_bottom:
            score += 1
        if result.do_data.oxycline_depth:
            score += 1
        
        # Nutrient quality
        if result.nutrient_data.has_orthophosphate:
            score += 1
        if result.nutrient_data.measured_at_depth:
            score += 1
        
        # Phytoplankton quality
        if result.phytoplankton_data.has_taxonomy:
            score += 1
        if result.phytoplankton_data.has_biovolume:
            score += 1
        
        # Calculation quality
        if result.calculated_metrics.hypoxic_water_volume:
            score += 2
        if result.calculated_metrics.phytoplankton_biomass_potential:
            score += 2
        
        # Multi-year
        if result.multi_year_data.has_trend_data:
            score += 1
        
        # Determine quality level
        if score >= 10:
            return "excellent"
        elif score >= 7:
            return "good"
        elif score >= 4:
            return "fair"
        else:
            return "basic"


# Singleton instance
advanced_extractor = AdvancedDataExtractor()

