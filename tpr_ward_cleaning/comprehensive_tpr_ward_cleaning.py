#!/usr/bin/env python3
"""
Comprehensive TPR Ward Name Cleaning Script
============================================
Author: Bernard Boateng
Date: 2025
Version: 1.0

Description:
This script cleans and standardizes ward names in TPR (Test Positivity Rate) data files
by matching them against the official Nigerian ward shapefile. It uses multiple advanced
matching techniques to achieve maximum accuracy.

Requirements:
- Python 3.7+
- Required packages: pandas, geopandas, fuzzywuzzy, python-Levenshtein, jellyfish

Installation:
pip install pandas geopandas fuzzywuzzy python-Levenshtein jellyfish openpyxl

Usage:
1. Place your TPR Excel files in a directory (e.g., 'tpr_data_by_state/')
2. Ensure you have the ward shapefile in 'complete_names_wards/'
3. Run: python comprehensive_tpr_ward_cleaning.py
4. For specific states (1-18): python comprehensive_tpr_ward_cleaning.py --states 1-18
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import warnings
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process
import re
import argparse
from collections import defaultdict
import sys
import time
import logging
from datetime import datetime

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tpr_cleaning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try importing optional packages
try:
    import jellyfish
    PHONETIC_AVAILABLE = True
except ImportError:
    PHONETIC_AVAILABLE = False
    print("Warning: jellyfish not installed. Phonetic matching will be skipped.")
    print("Install with: pip install jellyfish")


class ComprehensiveTPRCleaner:
    """
    Comprehensive ward name cleaning system for TPR data
    Version 2.0 with enhanced LGA matching and technique tracking
    """
    
    # Known LGA spelling variations
    LGA_VARIATIONS = {
        'Rivers': {
            'Emohua': 'Emuoha',
        },
        # Add more variations as discovered
    }
    
    # Ward number conversion mappings for handling Roman numerals and letters
    ROMAN_TO_ARABIC = {
        'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
        'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
        'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
        'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'
    }
    
    ARABIC_TO_ROMAN = {v: k for k, v in ROMAN_TO_ARABIC.items()}
    
    # Letter to number mappings (A=1, B=2, etc.)
    LETTER_TO_NUMBER = {
        'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5',
        'F': '6', 'G': '7', 'H': '8', 'I': '9', 'J': '10'
    }
    
    NUMBER_TO_LETTER = {v: k for k, v in LETTER_TO_NUMBER.items()}
    
    # State file mappings for all 37 Nigerian states
    STATE_FILE_MAPPINGS = {
        # States 1-18
        'Abia': 'ab_Abia_State_TPR_LLIN_2024.xlsx',
        'Adamawa': 'ad_Adamawa_State_TPR_LLIN_2024.xlsx',
        'Akwa Ibom': 'ak_Akwa_Ibom_State_TPR_LLIN_2024.xlsx',
        'Anambra': 'an_Anambra_state_TPR_LLIN_2024.xlsx',
        'Bauchi': 'ba_Bauchi_State_TPR_LLIN_2024.xlsx',
        'Bayelsa': 'by_Bayelsa_State_TPR_LLIN_2024.xlsx',
        'Benue': 'be_Benue_State_TPR_LLIN_2024.xlsx',
        'Borno': 'bo_Borno_State_TPR_LLIN_2024.xlsx',
        'Cross River': 'cr_Cross_River_State_TPR_LLIN_2024.xlsx',
        'Delta': 'de_Delta_State_TPR_LLIN_2024.xlsx',
        'Ebonyi': 'eb_Ebonyi_State_TPR_LLIN_2024.xlsx',
        'Edo': 'ed_Edo_State_TPR_LLIN_2024.xlsx',
        'Ekiti': 'ek_Ekiti_State_TPR_LLIN_2024.xlsx',
        'Enugu': 'en_Enugu_State_TPR_LLIN_2024.xlsx',
        'Federal Capital Territory': 'fc_Federal_Capital_Territory_TPR_LLIN_2024.xlsx',
        'Gombe': 'go_Gombe_State_TPR_LLIN_2024.xlsx',
        'Imo': 'im_Imo_State_TPR_LLIN_2024.xlsx',
        'Jigawa': 'ji_Jigawa_State_TPR_LLIN_2024.xlsx',
        
        # States 19-37
        'Kaduna': 'kd_Kaduna_State_TPR_LLIN_2024.xlsx',
        'Kano': 'kn_Kano_State_TPR_LLIN_2024.xlsx',
        'Katsina': 'kt_Katsina_State_TPR_LLIN_2024.xlsx',
        'Kebbi': 'ke_Kebbi_State_TPR_LLIN_2024.xlsx',
        'Kogi': 'ko_Kogi_State_TPR_LLIN_2024.xlsx',
        'Kwara': 'kw_Kwara_State_TPR_LLIN_2024.xlsx',
        'Lagos': 'la_Lagos_State_TPR_LLIN_2024.xlsx',
        'Nasarawa': 'na_Nasarawa_State_TPR_LLIN_2024.xlsx',
        'Niger': 'ni_Niger_State_TPR_LLIN_2024.xlsx',
        'Ogun': 'og_Ogun_State_TPR_LLIN_2024.xlsx',
        'Ondo': 'on_Ondo_State_TPR_LLIN_2024.xlsx',
        'Osun': 'os_Osun_State_TPR_LLIN_2024.xlsx',
        'Oyo': 'oy_Oyo_State_TPR_LLIN_2024.xlsx',
        'Plateau': 'pl_Plateau_State_TPR_LLIN_2024.xlsx',
        'Rivers': 'ri_Rivers_State_TPR_LLIN_2024.xlsx',
        'Sokoto': 'so_Sokoto_State_TPR_LLIN_2024.xlsx',
        'Taraba': 'ta_Taraba_State_TPR_LLIN_2024.xlsx',
        'Yobe': 'yo_Yobe_State_TPR_LLIN_2024.xlsx',
        'Zamfara': 'za_Zamfara_State_TPR_LLIN_2024.xlsx'
    }
    
    # State number mapping
    STATE_NUMBERS = {
        1: 'Abia', 2: 'Adamawa', 3: 'Akwa Ibom', 4: 'Anambra', 5: 'Bauchi',
        6: 'Bayelsa', 7: 'Benue', 8: 'Borno', 9: 'Cross River', 10: 'Delta',
        11: 'Ebonyi', 12: 'Edo', 13: 'Ekiti', 14: 'Enugu', 15: 'Federal Capital Territory',
        16: 'Gombe', 17: 'Imo', 18: 'Jigawa', 19: 'Kaduna', 20: 'Kano',
        21: 'Katsina', 22: 'Kebbi', 23: 'Kogi', 24: 'Kwara', 25: 'Lagos',
        26: 'Nasarawa', 27: 'Niger', 28: 'Ogun', 29: 'Ondo', 30: 'Osun',
        31: 'Oyo', 32: 'Plateau', 33: 'Rivers', 34: 'Sokoto', 35: 'Taraba',
        36: 'Yobe', 37: 'Zamfara'
    }
    
    def __init__(self, shapefile_path, tpr_data_dir, output_dir):
        """
        Initialize the cleaner
        
        Args:
            shapefile_path: Path to the ward shapefile directory
            tpr_data_dir: Directory containing TPR Excel files
            output_dir: Directory to save cleaned files
        """
        self.shapefile_path = Path(shapefile_path)
        self.tpr_data_dir = Path(tpr_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Load shapefile
        print("Loading shapefile...")
        shapefile = self.shapefile_path / 'wards.shp'
        if not shapefile.exists():
            raise FileNotFoundError(f"Shapefile not found at {shapefile}")
        
        self.gdf = gpd.read_file(str(shapefile))
        
        # Create state-ward mapping
        self.state_ward_mapping = {}
        for state in self.gdf['StateName'].unique():
            if pd.notna(state):
                state_wards = self.gdf[self.gdf['StateName'] == state]['WardName'].dropna().unique()
                self.state_ward_mapping[state] = list(state_wards)
        
        # Create state-LGA-ward mapping for strict LGA matching
        self.state_lga_ward_mapping = {}
        for state in self.gdf['StateName'].unique():
            if pd.notna(state):
                self.state_lga_ward_mapping[state] = {}
                state_gdf = self.gdf[self.gdf['StateName'] == state]
                
                for lga in state_gdf['LGAName'].unique():
                    if pd.notna(lga):
                        lga_wards = state_gdf[state_gdf['LGAName'] == lga]['WardName'].dropna().unique()
                        self.state_lga_ward_mapping[state][lga] = list(lga_wards)
        
        print(f"Loaded {len(self.state_ward_mapping)} states with ward data")
        print("✓ LGA-aware matching enabled - wards will be matched within their LGA boundaries")
        logger.info(f"Loaded {len(self.state_ward_mapping)} states with ward data")
        
        # Initialize caches
        self.lga_mapping_cache = {}
        self.ward_mapping_cache = {}
        
        # Statistics tracking
        self.overall_stats = {
            'total_rows': 0,
            'total_matched': 0,
            'total_unmatched': 0,
            'states_processed': 0,
            'lga_mismatches_prevented': 0,
            'techniques_used': defaultdict(int)
        }
    
    def clean_lga_name_enhanced(self, lga_name):
        """Enhanced LGA name cleaning with better normalization"""
        if pd.isna(lga_name):
            return ""
        
        # Convert to string and strip
        clean_lga = str(lga_name).strip()
        
        # Remove state prefix (2-letter code)
        clean_lga = re.sub(r'^[a-z]{2}\s+', '', clean_lga, flags=re.IGNORECASE)
        
        # Remove various forms of 'Local Government Area'
        suffixes = [
            'Local Government Area',
            'Local Govt Area',
            'Local Govt. Area',
            'LGA',
            'L.G.A',
            'L.G.A.'
        ]
        for suffix in suffixes:
            clean_lga = re.sub(f'\\s*{re.escape(suffix)}\\s*$', '', clean_lga, flags=re.IGNORECASE)
        
        # Remove extra spaces
        clean_lga = ' '.join(clean_lga.split())
        
        return clean_lga
    
    def clean_lga_name(self, lga_name):
        """Legacy method - redirects to enhanced version"""
        return self.clean_lga_name_enhanced(lga_name)
    
    def find_matching_lga_enhanced(self, tpr_lga, shapefile_lgas, state_name=None):
        """Enhanced LGA matching with spelling variations and better techniques"""
        clean_tpr_lga = self.clean_lga_name_enhanced(tpr_lga)
        
        if not clean_tpr_lga:
            return None, 0
        
        # Check for known variations first
        if state_name and state_name in self.LGA_VARIATIONS:
            if clean_tpr_lga in self.LGA_VARIATIONS[state_name]:
                known_match = self.LGA_VARIATIONS[state_name][clean_tpr_lga]
                if known_match in shapefile_lgas:
                    return known_match, 100
        
        # Try exact match first (case-insensitive)
        for sf_lga in shapefile_lgas:
            if clean_tpr_lga.lower() == str(sf_lga).lower():
                return sf_lga, 100
        
        # Try with normalized separators
        normalized_tpr = clean_tpr_lga.replace('/', '').replace('-', '').replace(' ', '').lower()
        for sf_lga in shapefile_lgas:
            normalized_sf = str(sf_lga).replace('/', '').replace('-', '').replace(' ', '').lower()
            if normalized_tpr == normalized_sf:
                return sf_lga, 95
        
        # Try phonetic matching if available
        if PHONETIC_AVAILABLE:
            try:
                tpr_soundex = jellyfish.soundex(clean_tpr_lga)
                tpr_metaphone = jellyfish.metaphone(clean_tpr_lga)
                
                for sf_lga in shapefile_lgas:
                    sf_soundex = jellyfish.soundex(str(sf_lga))
                    sf_metaphone = jellyfish.metaphone(str(sf_lga))
                    
                    if tpr_soundex == sf_soundex or tpr_metaphone == sf_metaphone:
                        # Verify with fuzzy match
                        score = fuzz.ratio(clean_tpr_lga.lower(), str(sf_lga).lower())
                        if score >= 75:
                            return sf_lga, score
            except:
                pass
        
        # Try fuzzy matching with multiple methods
        best_match = None
        best_score = 0
        
        for sf_lga in shapefile_lgas:
            # Multiple scoring methods
            scores = [
                fuzz.ratio(clean_tpr_lga.lower(), str(sf_lga).lower()),
                fuzz.token_sort_ratio(clean_tpr_lga.lower(), str(sf_lga).lower()),
                fuzz.token_set_ratio(clean_tpr_lga.lower(), str(sf_lga).lower()),
                fuzz.partial_ratio(clean_tpr_lga.lower(), str(sf_lga).lower())
            ]
            max_score = max(scores)
            
            if max_score > best_score and max_score >= 80:  # Lowered threshold slightly
                best_score = max_score
                best_match = sf_lga
        
        if best_match:
            return best_match, best_score
        
        return None, 0
    
    def find_matching_lga(self, tpr_lga, shapefile_lgas):
        """Legacy method - redirects to enhanced version"""
        match, score = self.find_matching_lga_enhanced(tpr_lga, shapefile_lgas)
        return match
    
    def clean_ward_name_basic(self, ward_name):
        """Basic cleaning of ward name"""
        if pd.isna(ward_name):
            return ""
        
        # Convert to string and strip
        ward = str(ward_name).strip()
        
        # Remove state prefixes (e.g., 'kd ', 'ke ', etc.)
        prefixes = ['ab ', 'ad ', 'ak ', 'an ', 'ba ', 'be ', 'bo ', 'by ', 'cr ', 'de ',
                   'eb ', 'ed ', 'ek ', 'en ', 'fc ', 'go ', 'im ', 'ji ', 'kd ', 'ke ',
                   'kn ', 'ko ', 'kt ', 'kw ', 'la ', 'na ', 'ni ', 'og ', 'on ', 'os ',
                   'oy ', 'pl ', 'ri ', 'so ', 'ta ', 'yo ', 'za ']
        
        for prefix in prefixes:
            if ward.lower().startswith(prefix):
                ward = ward[len(prefix):].strip()
                break
        
        # Remove 'Ward' suffix and LGA in parentheses
        ward = re.sub(r'\s*[Ww]ard\s*$', '', ward)
        ward = re.sub(r'\s*\([^)]+\)\s*$', '', ward)
        
        return ward.strip()
    
    def extract_ward_components(self, ward_name):
        """Extract base name and number/letter identifier from ward name"""
        if not ward_name:
            return "", ""
        
        cleaned = self.clean_ward_name_basic(ward_name)
        
        # Pattern 1: "Name Number" or "Name Letter" or "Name Roman"
        pattern1 = re.match(r'^(.+?)\s+([\d]+|[IVXivx]+|[A-Za-z])$', cleaned)
        if pattern1:
            base = pattern1.group(1).strip()
            identifier = pattern1.group(2).strip()
            # Check if identifier is valid
            if identifier.isdigit() or re.match(r'^[IVXivx]+$', identifier) or \
               (len(identifier) == 1 and identifier.upper() in self.LETTER_TO_NUMBER):
                return base, identifier
        
        # Pattern 2: "Name Ward Number" (already cleaned, but check original)
        if 'ward' in ward_name.lower():
            pattern2 = re.search(r'\s+([\d]+|[IVXivx]+|[A-Za-z])\s*(?:ward|$)', ward_name, re.IGNORECASE)
            if pattern2:
                identifier = pattern2.group(1).strip()
                base = re.sub(r'\s+' + re.escape(identifier) + r'.*', '', cleaned).strip()
                return base, identifier
        
        return cleaned, ""
    
    def convert_ward_identifier(self, identifier):
        """Convert between number formats (1->I, A->1, etc.)"""
        if not identifier:
            return []
        
        identifier = identifier.strip()
        variants = []
        
        # Check if it's an Arabic number
        if identifier.isdigit():
            variants.append(identifier)
            # Add Roman numeral variant
            if identifier in self.ARABIC_TO_ROMAN:
                roman = self.ARABIC_TO_ROMAN[identifier]
                variants.extend([roman, roman.lower()])
                if roman == 'IV':
                    variants.append('Iv')
            # Add letter variant if applicable
            if identifier in self.NUMBER_TO_LETTER:
                letter = self.NUMBER_TO_LETTER[identifier]
                variants.extend([letter, letter.lower()])
        
        # Check if it's a Roman numeral
        elif re.match(r'^[IVXivx]+$', identifier):
            upper_roman = identifier.upper()
            variants.extend([upper_roman, identifier.lower()])
            if upper_roman == 'IV':
                variants.append('Iv')
            # Add Arabic variant
            if upper_roman in self.ROMAN_TO_ARABIC:
                arabic = self.ROMAN_TO_ARABIC[upper_roman]
                variants.append(arabic)
                # Add letter variant if applicable
                if arabic in self.NUMBER_TO_LETTER:
                    letter = self.NUMBER_TO_LETTER[arabic]
                    variants.extend([letter, letter.lower()])
        
        # Check if it's a single letter
        elif len(identifier) == 1 and identifier.upper() in self.LETTER_TO_NUMBER:
            upper_letter = identifier.upper()
            variants.extend([upper_letter, identifier.lower()])
            # Add number variant
            if upper_letter in self.LETTER_TO_NUMBER:
                number = self.LETTER_TO_NUMBER[upper_letter]
                variants.append(number)
                # Add Roman variant
                if number in self.ARABIC_TO_ROMAN:
                    roman = self.ARABIC_TO_ROMAN[number]
                    variants.extend([roman, roman.lower()])
                    if roman == 'IV':
                        variants.append('Iv')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                unique_variants.append(v)
        
        return unique_variants
    
    def technique_5_exact_number_matching(self, ward_name, candidate_wards):
        """Exact number/letter matching technique with conversion"""
        if not ward_name or not candidate_wards:
            return None, 0, None
        
        # Extract components from the ward name
        base_name, identifier = self.extract_ward_components(ward_name)
        
        if not identifier:
            # No number/letter to match
            return None, 0, None
        
        # Get all variants of the identifier
        id_variants = self.convert_ward_identifier(identifier)
        
        # Clean base name for comparison
        clean_base = base_name.lower().replace('ward', '').strip()
        
        # Try to find exact match with same base and any variant of identifier
        best_match = None
        best_score = 0
        
        for candidate in candidate_wards:
            # Extract components from candidate
            cand_base, cand_id = self.extract_ward_components(candidate)
            
            if not cand_id:
                continue
            
            # Clean candidate base for comparison
            clean_cand_base = cand_base.lower().replace('ward', '').strip()
            
            # Check if bases match (fuzzy to handle minor variations)
            base_similarity = fuzz.ratio(clean_base, clean_cand_base)
            
            if base_similarity >= 85:  # Bases are similar enough
                # Check if identifiers match (considering conversions)
                if cand_id in id_variants:
                    # Perfect match with conversion!
                    score = min(100, base_similarity + 10)  # Boost score for exact id match
                    if score > best_score:
                        best_score = score
                        best_match = candidate
                elif cand_id.upper() in [v.upper() for v in id_variants]:
                    # Case-insensitive match
                    score = base_similarity
                    if score > best_score:
                        best_score = score
                        best_match = candidate
        
        if best_match:
            return best_match, best_score, 'ExactNumber'
        
        return None, 0, None
    
    def technique_1_fuzzy_matching(self, ward_name, candidate_wards, threshold=75):
        """Fuzzy matching technique"""
        if not ward_name or not candidate_wards:
            return None, 0, None
        
        cleaned_ward = self.clean_ward_name_basic(ward_name)
        if not cleaned_ward:
            return None, 0, None
        
        # Try exact match first
        cleaned_upper = cleaned_ward.upper()
        for candidate in candidate_wards:
            if candidate.upper() == cleaned_upper:
                return candidate, 100, 'Exact'
        
        # Fuzzy matching
        best_match = process.extractOne(
            cleaned_ward,
            candidate_wards,
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0], best_match[1], 'Fuzzy_TokenSort'
        
        # Try token set ratio for compound names
        best_match = process.extractOne(
            cleaned_ward,
            candidate_wards,
            scorer=fuzz.token_set_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0], best_match[1], 'Fuzzy_TokenSet'
        
        return None, 0, None
    
    def technique_2_abbreviation_inference(self, ward_name, shapefile_wards):
        """
        Special technique for Rivers-style abbreviations
        Infers abbreviations like 'Phward' from 'Port Harcourt Ward'
        """
        cleaned = self.clean_ward_name_basic(ward_name)
        
        # Check if it has the pattern "Location Ward N"
        match = re.match(r'^(.+?)\s+Ward\s+(\d+)$', ward_name, re.IGNORECASE)
        if not match:
            return None, 0, None
        
        location = match.group(1).strip()
        number = match.group(2)
        
        # Clean location
        location = re.sub(r'^[a-z]{2}\s+', '', location)
        
        # Generate possible abbreviations
        abbreviations = []
        
        # Method 1: First letters of each word
        words = location.replace('-', ' ').replace('/', ' ').split()
        if words:
            abbrev1 = ''.join(w[0].lower() for w in words)
            abbreviations.append(abbrev1)
        
        # Method 2: First 2-3 letters
        clean_location = re.sub(r'[^a-z]', '', location.lower())
        if len(clean_location) >= 2:
            abbreviations.append(clean_location[:2])
            abbreviations.append(clean_location[:3])
        
        # Method 3: Key consonants
        consonants = ''.join(c for c in location.lower() if c not in 'aeiou' and c.isalpha())
        if len(consonants) >= 2:
            abbreviations.append(consonants[:3])
        
        # Try to find matching abbreviated ward
        for abbrev in abbreviations:
            for sf_ward in shapefile_wards:
                # Check if shapefile ward matches pattern
                sf_match = re.match(r'^([a-z]+)ward\s*(\d+)$', sf_ward.lower())
                if sf_match:
                    sf_abbrev = sf_match.group(1)
                    sf_number = sf_match.group(2)
                    
                    if abbrev.startswith(sf_abbrev[:2]) and number == sf_number:
                        return sf_ward, 90, 'Abbreviation'
        
        return None, 0, None
    
    def technique_3_phonetic_matching(self, ward_name, candidate_wards):
        """Phonetic matching using soundex and metaphone"""
        if not PHONETIC_AVAILABLE:
            return None, 0, None
        
        cleaned = self.clean_ward_name_basic(ward_name)
        if not cleaned:
            return None, 0
        
        try:
            ward_soundex = jellyfish.soundex(cleaned)
            ward_metaphone = jellyfish.metaphone(cleaned)
            
            best_match = None
            best_score = 0
            
            for candidate in candidate_wards:
                cand_soundex = jellyfish.soundex(candidate)
                cand_metaphone = jellyfish.metaphone(candidate)
                
                if ward_soundex == cand_soundex or ward_metaphone == cand_metaphone:
                    fuzz_score = fuzz.ratio(cleaned.lower(), candidate.lower())
                    if fuzz_score > best_score and fuzz_score >= 60:
                        best_score = fuzz_score
                        best_match = candidate
            
            if best_match:
                return best_match, best_score, 'Phonetic'
        except Exception as e:
            logger.error(f"Phonetic matching error: {e}")
        
        return None, 0, None
    
    def technique_4_lga_context(self, ward_name, ward_lga, state_gdf, state_name):
        """Use LGA context for matching"""
        if 'LGAName' not in state_gdf.columns or pd.isna(ward_lga):
            return None, 0, None
        
        # Use enhanced LGA matching
        shapefile_lgas = state_gdf['LGAName'].unique()
        matched_lga, lga_score = self.find_matching_lga_enhanced(ward_lga, shapefile_lgas, state_name)
        
        if matched_lga and lga_score >= 80:
            # Get wards in this LGA
            lga_wards = state_gdf[state_gdf['LGAName'] == matched_lga]['WardName'].unique()
            
            # Try to match within LGA
            best_match, score, sub_technique = self.technique_1_fuzzy_matching(ward_name, lga_wards, threshold=70)
            if best_match:
                return best_match, score, f'LGA_Context_{sub_technique}'
        
        return None, 0, None
    
    def clean_state_data(self, state_name, file_name):
        """
        Clean TPR data for a specific state
        
        Args:
            state_name: Name of the state
            file_name: TPR file name
            
        Returns:
            Cleaned DataFrame or None if error
        """
        file_path = self.tpr_data_dir / file_name
        
        if not file_path.exists():
            print(f"  File not found: {file_path}")
            return None
        
        print(f"\nProcessing {state_name}...")
        logger.info(f"Processing {state_name}")
        start_time = time.time()
        
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            print(f"  Loaded {len(df)} rows")
            
            # Get standard ward names for this state
            if state_name not in self.state_ward_mapping:
                print(f"  Warning: No shapefile data for {state_name}")
                return df
            
            standard_wards = self.state_ward_mapping[state_name]
            print(f"  Found {len(standard_wards)} standard wards for {state_name}")
            
            # Get state geodataframe for LGA context
            state_gdf = self.gdf[self.gdf['StateName'] == state_name]
            
            # Create mapping for this state's wards
            ward_mapping = {}
            technique_mapping = {}  # Track which technique was used
            confidence_mapping = {}  # Track confidence scores
            unmatched = []
            lga_enforced_count = 0
            cross_lga_prevented = 0
            
            unique_tpr_wards = df['WardName'].dropna().unique()
            print(f"  Processing {len(unique_tpr_wards)} unique ward names...")
            
            # Check if LGA column exists
            has_lga = 'LGA' in df.columns
            if has_lga:
                print(f"  ✓ LGA column found - using enhanced LGA-aware matching")
                
                # Pre-process LGA mappings for efficiency
                tpr_lgas = df['LGA'].dropna().unique()
                shapefile_lgas = state_gdf['LGAName'].unique()
                lga_mapping = {}
                
                for tpr_lga in tpr_lgas:
                    matched_lga, score = self.find_matching_lga_enhanced(tpr_lga, shapefile_lgas, state_name)
                    if matched_lga:
                        lga_mapping[tpr_lga] = matched_lga
                        if score < 100:
                            logger.info(f"  LGA matched: '{tpr_lga}' -> '{matched_lga}' (score: {score})")
                
                print(f"  Matched {len(lga_mapping)}/{len(tpr_lgas)} LGAs")
            else:
                print(f"  ⚠ No LGA column - matching without LGA constraint")
                lga_mapping = {}
            
            for tpr_ward in unique_tpr_wards:
                best_match = None
                best_score = 0
                technique_used = None
                candidate_wards = standard_wards  # Default to all wards
                
                # PRIORITY: Try to get LGA-specific wards first
                ward_lga = None
                if has_lga:
                    # Get LGA from TPR data
                    ward_rows = df[df['WardName'] == tpr_ward]
                    if len(ward_rows) > 0:
                        tpr_lga = ward_rows.iloc[0]['LGA']
                        
                        # Use pre-computed LGA mapping
                        matched_lga = lga_mapping.get(tpr_lga)
                        
                        if matched_lga and state_name in self.state_lga_ward_mapping:
                            if matched_lga in self.state_lga_ward_mapping[state_name]:
                                # Restrict candidates to wards in this LGA only
                                candidate_wards = self.state_lga_ward_mapping[state_name][matched_lga]
                                ward_lga = matched_lga
                                lga_enforced_count += 1
                                
                                # Check if this would have matched incorrectly without LGA constraint
                                unconstrained_match, _, _ = self.technique_1_fuzzy_matching(tpr_ward, standard_wards)
                                if unconstrained_match and unconstrained_match not in candidate_wards:
                                    cross_lga_prevented += 1
                
                # Try techniques with LGA-constrained candidates
                
                # NEW PRIORITY: Technique 5: Exact number/letter matching (highest priority)
                match, score, technique = self.technique_5_exact_number_matching(tpr_ward, candidate_wards)
                if match and score > best_score:
                    best_match = match
                    best_score = score
                    technique_used = f"{technique}{'_LGA' if ward_lga else ''}"
                
                # Technique 1: Fuzzy matching (within LGA if available)
                # Only try fuzzy if we don't have a high-confidence exact number match
                if best_score < 95:
                    match, score, technique = self.technique_1_fuzzy_matching(tpr_ward, candidate_wards)
                    if match and score > best_score:
                        best_match = match
                        best_score = score
                        technique_used = f"{technique}{'_LGA' if ward_lga else ''}"
                
                # Technique 2: Abbreviation inference (for Rivers-style)
                if best_score < 100:
                    match, score, technique = self.technique_2_abbreviation_inference(tpr_ward, candidate_wards)
                    if match and score > best_score:
                        best_match = match
                        best_score = score
                        technique_used = f"{technique}{'_LGA' if ward_lga else ''}"
                
                # Technique 3: Phonetic matching (within LGA if available)
                if best_score < 100 and PHONETIC_AVAILABLE:
                    match, score, technique = self.technique_3_phonetic_matching(tpr_ward, candidate_wards)
                    if match and score > best_score:
                        best_match = match
                        best_score = score
                        technique_used = f"{technique}{'_LGA' if ward_lga else ''}"
                
                # Technique 4: LGA context matching (fallback if no LGA constraint was applied)
                if best_score < 100 and not ward_lga and has_lga:
                    # Try once more with explicit LGA context
                    ward_rows = df[df['WardName'] == tpr_ward]
                    if len(ward_rows) > 0:
                        tpr_lga = ward_rows.iloc[0]['LGA']
                        match, score, technique = self.technique_4_lga_context(tpr_ward, tpr_lga, state_gdf, state_name)
                        if match and score > best_score:
                            best_match = match
                            best_score = score
                            technique_used = technique
                
                if best_match:
                    ward_mapping[tpr_ward] = best_match
                    technique_mapping[tpr_ward] = technique_used
                    confidence_mapping[tpr_ward] = best_score
                    
                    # Track technique usage
                    self.overall_stats['techniques_used'][technique_used] += 1
                    
                    if best_score < 100:
                        logger.debug(f"Matched ({technique_used}): '{tpr_ward}' -> '{best_match}' (score: {best_score})")
                else:
                    unmatched.append(tpr_ward)
                    # Keep original if no match found
                    ward_mapping[tpr_ward] = self.clean_ward_name_basic(tpr_ward)
                    technique_mapping[tpr_ward] = 'Unmatched'
                    confidence_mapping[tpr_ward] = 0
            
            # Apply the mapping with enhanced tracking
            df['WardName_Original'] = df['WardName']
            df['WardName'] = df['WardName_Original'].map(lambda x: ward_mapping.get(x, x))
            df['Match_Technique'] = df['WardName_Original'].map(lambda x: technique_mapping.get(x, 'Unknown'))
            df['Match_Confidence'] = df['WardName_Original'].map(lambda x: confidence_mapping.get(x, 0))
            df['Match_Status'] = df['WardName_Original'].map(
                lambda x: technique_mapping.get(x, 'Unknown') if technique_mapping.get(x, 'Unknown') != 'Unmatched' else 'Unmatched'
            )
            
            # Summary statistics
            matched_count = len([w for w in ward_mapping.values() if w in standard_wards])
            elapsed_time = time.time() - start_time
            
            print(f"  Results: {matched_count}/{len(unique_tpr_wards)} wards matched ({matched_count/len(unique_tpr_wards)*100:.1f}%)")
            print(f"  Processing time: {elapsed_time:.2f} seconds")
            
            if has_lga:
                print(f"  LGA enforcement: {lga_enforced_count} wards matched within their LGA")
                if cross_lga_prevented > 0:
                    print(f"  ✓ Prevented {cross_lga_prevented} cross-LGA mismatches")
                    self.overall_stats['lga_mismatches_prevented'] += cross_lga_prevented
            
            # Log technique distribution for this state
            state_techniques = defaultdict(int)
            for technique in technique_mapping.values():
                if technique != 'Unmatched' and technique != 'Unknown':
                    state_techniques[technique] += 1
            
            if state_techniques:
                print(f"  Matching techniques used:")
                for technique, count in sorted(state_techniques.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"    - {technique}: {count}")
            
            if unmatched and len(unmatched) <= 10:
                print(f"  Unmatched wards ({len(unmatched)}):")
                for ward in unmatched[:5]:
                    print(f"    - {ward}")
                if len(unmatched) > 5:
                    print(f"    ... and {len(unmatched) - 5} more")
            
            # Update overall statistics
            self.overall_stats['total_rows'] += len(df)
            self.overall_stats['total_matched'] += len(df[df['Match_Status'] != 'Unmatched'])
            self.overall_stats['total_unmatched'] += len(df[df['Match_Status'] == 'Unmatched'])
            self.overall_stats['states_processed'] += 1
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {str(e)}")
            print(f"  Error processing {file_name}: {str(e)}")
            return None
    
    def validate_cleaned_data(self, df, state_name):
        """Validate the cleaned data for consistency"""
        validation_issues = []
        
        # Check if WardName_Original exists (may not exist if state shapefile is missing)
        if 'WardName_Original' not in df.columns:
            return validation_issues
        
        # Check for duplicate ward assignments
        ward_counts = df['WardName'].value_counts()
        duplicates = ward_counts[ward_counts > 1]
        if not duplicates.empty:
            validation_issues.append(f"Found {len(duplicates)} wards with multiple assignments")
        
        # Check for wards matched to multiple original names
        reverse_mapping = defaultdict(list)
        for orig, cleaned in zip(df['WardName_Original'], df['WardName']):
            if pd.notna(orig) and pd.notna(cleaned):
                reverse_mapping[cleaned].append(orig)
        
        multiple_sources = {k: v for k, v in reverse_mapping.items() if len(set(v)) > 1}
        if multiple_sources:
            validation_issues.append(f"Found {len(multiple_sources)} cleaned wards from multiple sources")
        
        # Check confidence distribution
        if 'Match_Confidence' in df.columns:
            low_confidence = df[df['Match_Confidence'].between(1, 70)]
            if len(low_confidence) > 0:
                validation_issues.append(f"Found {len(low_confidence)} matches with confidence < 70%")
        
        # NEW: Check for number/letter variant duplicates (e.g., Alayi A and Alayi B both mapping to same ward)
        number_letter_wards = {}
        for orig, cleaned in zip(df['WardName_Original'].dropna().unique(), 
                                 df.groupby('WardName_Original')['WardName'].first().values):
            base, identifier = self.extract_ward_components(orig)
            if identifier and base:  # Has a number/letter identifier
                if cleaned not in number_letter_wards:
                    number_letter_wards[cleaned] = []
                number_letter_wards[cleaned].append(orig)
        
        # Find cases where multiple numbered/lettered variants map to same target
        duplicate_number_mappings = {}
        for target, sources in number_letter_wards.items():
            if len(sources) > 1:
                # Check if sources have different identifiers
                identifiers = []
                for source in sources:
                    _, ident = self.extract_ward_components(source)
                    if ident:
                        identifiers.append(ident)
                # If different identifiers map to same target, it's a problem
                if len(set(identifiers)) > 1:
                    duplicate_number_mappings[target] = sources
        
        if duplicate_number_mappings:
            validation_issues.append(f"CRITICAL: {len(duplicate_number_mappings)} wards have multiple number/letter variants mapping to same target")
            for target, sources in list(duplicate_number_mappings.items())[:3]:
                logger.warning(f"  {sources} all map to '{target}'")
        
        if validation_issues:
            logger.warning(f"Validation issues for {state_name}: {'; '.join(validation_issues)}")
        
        return validation_issues
    
    def process_states(self, state_list=None):
        """
        Process specified states or all states
        
        Args:
            state_list: List of state names or numbers to process (None for all)
        """
        print("="*60)
        print("TPR DATA CLEANING PROCESS")
        print("="*60)
        
        # Determine which states to process
        if state_list:
            # Convert state numbers to names if needed
            states_to_process = []
            for item in state_list:
                if isinstance(item, int):
                    if item in self.STATE_NUMBERS:
                        states_to_process.append(self.STATE_NUMBERS[item])
                else:
                    states_to_process.append(str(item))
        else:
            states_to_process = list(self.STATE_FILE_MAPPINGS.keys())
        
        print(f"Processing {len(states_to_process)} states...")
        logger.info(f"Starting processing of {len(states_to_process)} states")
        
        results = {}
        validation_summary = {}
        
        for state_name in states_to_process:
            if state_name not in self.STATE_FILE_MAPPINGS:
                print(f"Warning: No file mapping for {state_name}")
                continue
            
            file_name = self.STATE_FILE_MAPPINGS[state_name]
            cleaned_df = self.clean_state_data(state_name, file_name)
            
            if cleaned_df is not None:
                # Validate the cleaned data
                validation_issues = self.validate_cleaned_data(cleaned_df, state_name)
                validation_summary[state_name] = validation_issues
                
                # Save the cleaned file
                output_filename = f"{state_name.lower().replace(' ', '_')}_tpr_cleaned.csv"
                output_path = self.output_dir / output_filename
                
                cleaned_df.to_csv(output_path, index=False)
                print(f"  Saved: {output_path}")
                
                # Calculate statistics for unique wards (not facilities)
                if 'WardName_Original' in cleaned_df.columns:
                    unique_wards_df = cleaned_df[['WardName_Original', 'Match_Status', 'Match_Technique']].drop_duplicates()
                else:
                    # Skip statistics if shapefile is missing
                    unique_wards_df = pd.DataFrame()
                
                results[state_name] = {
                    'rows': len(cleaned_df),
                    'unique_wards': len(unique_wards_df),
                    'matched': len(unique_wards_df[unique_wards_df['Match_Status'] != 'Unmatched']),
                    'validation_issues': len(validation_issues)
                }
        
        # Print summary
        self.print_summary(results, validation_summary)
        
        return results
    
    def print_summary(self, results, validation_summary):
        """Print enhanced cleaning summary"""
        print("\n" + "="*60)
        print("CLEANING SUMMARY")
        print("="*60)
        
        for state, stats in results.items():
            match_rate = (stats['matched'] / stats['unique_wards'] * 100) if stats['unique_wards'] > 0 else 0
            status = "✓" if match_rate >= 95 else "⚠" if match_rate < 90 else " "
            print(f"{status} {state}: {stats['rows']} rows, {stats['unique_wards']} unique wards, "
                  f"{stats['matched']} matched ({match_rate:.1f}%)")
            
            if stats['validation_issues'] > 0:
                print(f"    ⚠ {stats['validation_issues']} validation issues")
        
        print("\n" + "="*60)
        print("OVERALL STATISTICS")
        print("="*60)
        print(f"States processed: {self.overall_stats['states_processed']}")
        print(f"Total rows: {self.overall_stats['total_rows']:,}")
        print(f"Total matched: {self.overall_stats['total_matched']:,}")
        print(f"Total unmatched: {self.overall_stats['total_unmatched']:,}")
        
        if self.overall_stats.get('lga_mismatches_prevented', 0) > 0:
            print(f"Cross-LGA mismatches prevented: {self.overall_stats['lga_mismatches_prevented']}")
        
        if self.overall_stats['total_rows'] > 0:
            match_rate = (self.overall_stats['total_matched'] / self.overall_stats['total_rows']) * 100
            print(f"Overall match rate: {match_rate:.1f}%")
        
        # Print technique usage statistics
        if self.overall_stats['techniques_used']:
            print("\nMatching Techniques Used:")
            total_techniques = sum(self.overall_stats['techniques_used'].values())
            for technique, count in sorted(self.overall_stats['techniques_used'].items(), 
                                         key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / total_techniques * 100) if total_techniques > 0 else 0
                print(f"  {technique}: {count:,} ({percentage:.1f}%)")
        
        # Save enhanced summary to CSV
        summary_df = pd.DataFrame([
            {
                'State': state,
                'Total_Rows': stats['rows'],
                'Unique_Wards': stats['unique_wards'],
                'Matched_Wards': stats['matched'],
                'Match_Rate_%': (stats['matched'] / stats['unique_wards'] * 100) if stats['unique_wards'] > 0 else 0,
                'Validation_Issues': stats['validation_issues']
            }
            for state, stats in results.items()
        ])
        
        summary_path = self.output_dir / 'cleaning_summary.csv'
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSummary saved to: {summary_path}")
        
        # Save technique statistics
        if self.overall_stats['techniques_used']:
            technique_df = pd.DataFrame([
                {'Technique': technique, 'Count': count, 'Percentage': (count / sum(self.overall_stats['techniques_used'].values()) * 100)}
                for technique, count in self.overall_stats['techniques_used'].items()
            ])
            technique_path = self.output_dir / 'technique_statistics.csv'
            technique_df.to_csv(technique_path, index=False)
            print(f"Technique statistics saved to: {technique_path}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Clean TPR ward names by matching with shapefile - Version 2.0')
    parser.add_argument('--shapefile', default='www/complete_names_wards',
                       help='Path to shapefile directory (default: www/complete_names_wards)')
    parser.add_argument('--tpr-dir', default='www/tpr_data_by_state',
                       help='Directory containing TPR Excel files (default: www/tpr_data_by_state)')
    parser.add_argument('--output-dir', default='tpr_ward_cleaning/all_states_cleaned_final',
                       help='Output directory for cleaned files (default: tpr_ward_cleaning/all_states_cleaned_final)')
    parser.add_argument('--states', nargs='+',
                       help='States to process (names or numbers, e.g., "1-18" or "Kaduna Lagos")')
    
    args = parser.parse_args()
    
    # Parse state range if provided
    states_to_process = None
    if args.states:
        states_to_process = []
        for item in args.states:
            if '-' in item:
                # Handle range like "1-18"
                try:
                    start, end = item.split('-')
                    states_to_process.extend(range(int(start), int(end) + 1))
                except:
                    states_to_process.append(item)
            elif item.isdigit():
                states_to_process.append(int(item))
            else:
                states_to_process.append(item)
    
    # Create cleaner and process
    try:
        cleaner = ComprehensiveTPRCleaner(
            shapefile_path=args.shapefile,
            tpr_data_dir=args.tpr_dir,
            output_dir=args.output_dir
        )
        
        results = cleaner.process_states(states_to_process)
        
        print("\n✅ Cleaning complete!")
        print(f"Cleaned files saved to: {args.output_dir}/")
        print("\nVersion 2.0 Improvements:")
        print("  ✓ Enhanced LGA matching with spelling variations")
        print("  ✓ Technique tracking in output files")
        print("  ✓ Confidence scores for matches")
        print("  ✓ Performance optimizations with caching")
        print("  ✓ Validation of cleaned data")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nPlease ensure:")
        print("1. Shapefile is in 'complete_names_wards/' directory")
        print("2. TPR Excel files are in 'tpr_data_by_state/' directory")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()