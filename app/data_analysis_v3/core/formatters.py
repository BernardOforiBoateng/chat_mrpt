"""
Message Formatters

Handles formatting of messages for various stages of the data analysis workflow.
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MessageFormatter:
    """Formats messages for different workflow stages."""
    
    def __init__(self, session_id: str):
        """
        Initialize the message formatter.
        
        Args:
            session_id: Session identifier
        """
        self.session_id = session_id
    
    def format_state_selection(self, analysis: Dict) -> str:
        """Format state selection message with statistics."""
        message = "Great! I'll guide you through the TPR calculation process.\n\n"
        
        # Check if there's only one state (should not happen since we skip this)
        if analysis.get('total_states') == 1:
            # This shouldn't be called if single state, but just in case
            single_state = list(analysis['states'].keys())[0]
            message += f"I see you have data for **{single_state}**.\n\n"
            return message
        
        message += "**Which state would you like to analyze?**\n\n"
        
        if 'states' in analysis and analysis['states']:
            message += "Based on your data, I found:\n\n"
            for idx, (state, info) in enumerate(analysis['states'].items(), 1):
                message += f"**{idx}. {info['name']}**\n"
                message += f"   • {info['total_records']:,} records\n"
                message += f"   • {info['facilities']:,} facilities\n"
                message += f"   • {info['total_tests']:,} total tests\n\n"
            
            message += "Which state would you like to analyze? (Enter the number or state name)"
            
            # Add recommendation if available
            if analysis.get('recommended'):
                message += f"\n\n💡 Tip: {analysis['recommended']} has the most complete data"
        
        return message
    
    def format_facility_selection(self, state: str, analysis: Dict) -> str:
        """Format facility level selection message."""
        message = f"Analyzing **{state}**.\n\n"
        message += "**Which facility level would you like to analyze?**\n\n"
        
        if 'levels' in analysis and analysis['levels']:
            # Order: Primary, Secondary, Tertiary, All
            order = ['primary', 'secondary', 'tertiary', 'all']
            
            for idx, key in enumerate(order, 1):
                if key in analysis['levels']:
                    level = analysis['levels'][key]
                    message += f"**{idx}. {level['name']}**"
                    
                    # Add recommended marker for Primary
                    if level.get('recommended'):
                        message += " ⭐ Recommended"
                    
                    message += "\n"  # Line break after title
                    message += f"   • {level['count']:,} facilities ({level['percentage']:.1f}% of total)\n"
                    
                    # Add test type stats if available
                    if level.get('rdt_tests', 0) > 0 or level.get('microscopy_tests', 0) > 0:
                        message += f"   • RDT tests: {level.get('rdt_tests', 0):,}\n"
                        message += f"   • Microscopy tests: {level.get('microscopy_tests', 0):,}\n"
                    
                    message += f"   • {level['description']}\n\n"  # Double line break after each option
        else:
            message += "All facilities will be analyzed.\n"
        
        message += "Which level? (1-4 or type the level name):"
        
        return message
    
    def format_facility_selection_only(self, analysis: Dict) -> str:
        """Format facility selection when state is auto-selected."""
        message = "Great! I'll guide you through the TPR calculation process.\n\n"
        
        # Since state was auto-selected, mention it
        state_name = analysis.get('state_name', 'your state')
        message += f"I see you have data for **{state_name}**.\n\n"
        
        message += "**Which facility level would you like to analyze?**\n\n"
        
        if 'levels' in analysis and analysis['levels']:
            # Order: Primary, Secondary, Tertiary, All
            order = ['primary', 'secondary', 'tertiary', 'all']
            
            for idx, key in enumerate(order, 1):
                if key in analysis['levels']:
                    level = analysis['levels'][key]
                    message += f"**{idx}. {level['name']}**"
                    
                    # Add recommended marker for Primary
                    if level.get('recommended'):
                        message += " ⭐ Recommended"
                    
                    message += "\n"  # Line break after title
                    message += f"   • {level['count']:,} facilities ({level['percentage']:.1f}% of total)\n"
                    
                    # Add test type stats if available
                    if level.get('rdt_tests', 0) > 0 or level.get('microscopy_tests', 0) > 0:
                        message += f"   • RDT tests: {level.get('rdt_tests', 0):,}\n"
                        message += f"   • Microscopy tests: {level.get('microscopy_tests', 0):,}\n"
                    
                    message += f"   • {level['description']}\n\n"  # Double line break after each option
        else:
            message += "All facilities will be analyzed.\n"
        
        message += "Which level? (1-4 or type the level name):"
        
        return message
    
    def format_age_group_selection(self, analysis: Dict) -> str:
        """Format age group selection message."""
        # Get state and facility from the analysis dict
        state = analysis.get('state', 'the selected state')
        
        # Format facility level properly
        facility_raw = analysis.get('facility_level', 'selected facilities')
        if facility_raw and facility_raw != 'selected facilities':
            # Convert underscore format to readable format
            if facility_raw == 'primary':
                facility = 'Primary health centers'
            elif facility_raw == 'secondary':
                facility = 'Secondary health facilities'
            elif facility_raw == 'tertiary':
                facility = 'Tertiary hospitals'
            elif facility_raw == 'all':
                facility = 'All facility levels'
            else:
                facility = facility_raw.replace('_', ' ').title()
        else:
            facility = 'selected facilities'
        
        message = f"Analyzing **{facility}** in **{state}**.\n\n"
        message += "**Which age group should I calculate TPR for?**\n\n"
        
        if 'age_groups' in analysis:
            age_groups = analysis['age_groups']
            
            # Order of display - ONLY 3 groups per user requirement
            order = ['under_5', 'over_5', 'pregnant']
            
            message += "Based on your data:\n\n"
            
            available_options = []
            option_number = 1
            
            for key in order:
                if key in age_groups and age_groups[key]['has_data']:
                    group = age_groups[key]
                    available_options.append(str(option_number))
                    
                    message += f"**{option_number}. {group['name']}** {group.get('icon', '')}"
                    
                    # Mark as recommended if it is
                    if group.get('recommended'):
                        message += " ⭐ Recommended"
                    
                    message += "\n"  # Line break after title
                    
                    # Add statistics with proper line breaks INCLUDING test type breakdown
                    message += f"   • {group['tests_available']:,} total tests available\n"
                    
                    # Add test type breakdown if available
                    if group.get('rdt_tests', 0) > 0:
                        message += f"   • RDT: {group['rdt_tests']:,} tests, {group.get('rdt_tpr', 0):.1f}% positive\n"
                    if group.get('microscopy_tests', 0) > 0:
                        message += f"   • Microscopy: {group['microscopy_tests']:,} tests, {group.get('microscopy_tpr', 0):.1f}% positive\n"
                    
                    message += f"   • Overall positivity: {group['positivity_rate']:.1f}%\n"
                    message += f"   • {group['facilities_reporting']} facilities reporting\n"
                    message += f"   • {group['description']}\n\n"  # Double line break after each option
                    
                    option_number += 1
            
            # Add tip for Under 5 if it exists
            if 'under_5' in age_groups and age_groups['under_5']['has_data']:
                message += "💡 Tip: 'Under 5 Years' is the highest risk group for severe malaria\n"
            
            # Update prompt to match actual available options
            if len(available_options) == 1:
                message += f"\nEnter {available_options[0]} to proceed:"
            elif len(available_options) == 2:
                message += f"\nWhich age group? ({available_options[0]} or {available_options[1]}):"
            else:
                message += f"\nWhich age group? ({available_options[0]}-{available_options[-1]}):"
        else:
            message += "All age groups will be analyzed.\n"
        
        return message
    
    def format_tool_tpr_results(self, tool_output: str) -> str:
        """Format TPR tool results for display."""
        # The tool already returns well-formatted text, just pass it through with minor enhancements
        if "TPR Calculation Complete!" in tool_output:
            # The tool output is already well formatted, just use it
            message = tool_output
            
            # Check if map was NOT created (no shapefile)
            if "iframe" not in tool_output and "tpr_distribution_map.html" not in tool_output:
                message += "\n\n📍 Note: Map visualization requires shapefile data. Upload shapefile to enable geographic visualization."
            
            # Add production-style next step prompt
            message += "\n\n**Next Step:**\n"
            message += "I've finished the TPR analysis. Would you like to proceed to the risk analysis to rank wards and plan for ITN distribution?"
            
            # Set flag that TPR is complete and ready for risk analysis
            import os
            flag_file = f"instance/uploads/{self.session_id}/.tpr_complete"
            Path(flag_file).touch()
            
            return message
        else:
            # Fallback formatting if tool output is unexpected
            return tool_output