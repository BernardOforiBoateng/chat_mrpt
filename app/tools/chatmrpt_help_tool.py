"""
ChatMRPT Help Tool - Provides intelligent help about using ChatMRPT
Explains UI elements, features, workflows, and guides users through the application
"""

from typing import Dict, Any, List, Optional
from app.tools.base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class ChatMRPTHelpTool(BaseTool):
    """
    Tool for providing help and guidance about using ChatMRPT.
    Explains features, UI elements, workflows, and common tasks.
    """
    
    def __init__(self):
        super().__init__(
            name="ChatMRPT Help",
            description="Get help and guidance on using ChatMRPT features and interface"
        )
        
        # Define help topics and responses
        self.help_topics = {
            'general': {
                'keywords': ['how to use', 'what can', 'help', 'guide', 'tutorial', 'get started'],
                'response': self._general_help
            },
            'upload': {
                'keywords': ['upload', 'data', 'csv', 'shapefile', 'files', 'import'],
                'response': self._upload_help
            },
            'analysis': {
                'keywords': ['analyze', 'analysis', 'risk', 'calculate', 'process'],
                'response': self._analysis_help
            },
            'visualization': {
                'keywords': ['map', 'chart', 'visualize', 'view', 'display', 'graph'],
                'response': self._visualization_help
            },
            'report': {
                'keywords': ['report', 'export', 'download', 'pdf', 'generate'],
                'response': self._report_help
            },
            'ui_elements': {
                'keywords': ['button', 'icon', 'tab', 'menu', 'interface', 'where is'],
                'response': self._ui_elements_help
            },
            'features': {
                'keywords': ['features', 'capabilities', 'functions', 'tools'],
                'response': self._features_help
            },
            'tpr': {
                'keywords': ['tpr', 'test positivity', 'nmep', 'facility'],
                'response': self._tpr_help
            }
        }
    
    def can_handle(self, request: str) -> bool:
        """Check if this tool can handle the request."""
        request_lower = request.lower()
        
        # Check for explicit help requests
        help_indicators = ['how to use chatmrpt', 'help', 'guide', 'tutorial', 'explain chatmrpt',
                          'what is chatmrpt', 'how does chatmrpt work', 'chatmrpt features']
        
        # Check for questions about specific UI elements
        ui_questions = ['where is', 'what does', 'how do i', 'which button', 'which tab']
        
        return any(indicator in request_lower for indicator in help_indicators) or \
               any(question in request_lower for question in ui_questions)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the help tool based on the user's request."""
        try:
            request = kwargs.get('request', '').lower()
            session_state = kwargs.get('session_state', {})
            
            # Check if user has data loaded
            has_data = session_state.get('csv_uploaded', False) or \
                      session_state.get('shapefile_uploaded', False)
            
            # Determine the help topic
            topic = self._determine_topic(request)
            
            # Get the appropriate response
            if topic:
                response = self.help_topics[topic]['response'](request, has_data)
            else:
                response = self._general_help(request, has_data)
            
            return {
                'status': 'success',
                'response': response,
                'suggestions': self._get_suggestions(has_data)
            }
            
        except Exception as e:
            logger.error(f"Error in ChatMRPT help tool: {str(e)}")
            return {
                'status': 'error',
                'response': "I encountered an error while preparing the help information. Please try asking your question differently.",
                'error': str(e)
            }
    
    def _determine_topic(self, request: str) -> Optional[str]:
        """Determine which help topic matches the request."""
        for topic, info in self.help_topics.items():
            if any(keyword in request for keyword in info['keywords']):
                return topic
        return None
    
    def _general_help(self, request: str, has_data: bool) -> str:
        """Provide general help about ChatMRPT."""
        if not has_data:
            return """
**Welcome to ChatMRPT! Here's how to get started:**

ChatMRPT is a powerful tool for malaria risk analysis and prioritization. Here's what you can do:

**1. Upload Your Data** 📎
- Click the **paperclip icon** in the bottom left to upload your files
- You'll need two files:
  - A **CSV or Excel file** with ward-level data (demographics, health indicators, etc.)
  - A **Shapefile (ZIP)** with geographical boundaries

**2. Analyze Your Data** 📊
- Once uploaded, I can help you:
  - Identify high-risk areas for malaria
  - Calculate vulnerability scores
  - Analyze environmental and demographic factors
  - Create prioritized intervention lists

**3. Visualize Results** 🗺️
- Generate interactive maps showing risk levels
- Create charts and graphs for data insights
- Compare different variables and their impacts

**4. Generate Reports** 📄
- Click the **document icon** to create comprehensive reports
- Export results in PDF, HTML, or Markdown formats

**Need specific help?** Just ask me:
- "How do I upload my data?"
- "What analysis methods are available?"
- "How can I generate a report?"

**Don't have data yet?** You can explore with our sample dataset by clicking "Load Sample Data" in the upload dialog!
"""
        else:
            return """
**Great! You have data loaded. Here's what you can do now:**

**Available Actions:**

📊 **Run Analysis**
- Ask me to "analyze malaria risk" or "identify vulnerable areas"
- I'll use composite scoring and PCA methods to assess risk levels

🗺️ **Create Visualizations**
- Request "show me a risk map" or "create vulnerability charts"
- Explore different variables with "map [variable name]"

📈 **Explore Your Data**
- Ask about specific wards: "Tell me about [ward name]"
- Compare areas: "Which wards are most at risk?"
- Understand variables: "What factors contribute most to risk?"

📄 **Generate Reports**
- Click the document icon or ask "generate a report"
- Get comprehensive PDF reports with all findings

**Quick Commands:**
- "Analyze my data" - Run full risk analysis
- "Show top 10 risky wards" - Get prioritized list
- "Explain the methodology" - Understand how analysis works
- "What variables do I have?" - See available data fields

**Need help with something specific?** Just ask!
"""
    
    def _upload_help(self, request: str, has_data: bool) -> str:
        """Provide help about uploading data."""
        return """
**How to Upload Data to ChatMRPT:**

**Step 1: Click the Upload Button** 📎
- Find the **paperclip icon** in the bottom-left corner of the chat
- Click it to open the upload dialog

**Step 2: Choose Your Upload Type:**
- **Standard Upload**: For regular ward-level analysis
- **TPR Analysis**: For Test Positivity Rate calculations
- **Download Processed Data**: To retrieve previous analysis results

**Step 3: Upload Your Files:**
For standard analysis, you need:

📊 **CSV/Excel File** (Required)
- Should contain ward-level data
- Include columns like population, health indicators, environmental factors
- Common variables: population density, poverty rates, health facility access, etc.

🗺️ **Shapefile (ZIP)** (Required)
- Must be compressed as a ZIP file
- Should contain ward boundaries matching your CSV data
- Include .shp, .shx, .dbf files at minimum

**File Requirements:**
- CSV/Excel: Maximum 32MB
- Shapefile: Must be in ZIP format
- Ward names must match between files

**No data yet?** Click "Load Sample Data" to explore with our example dataset!

**Having issues?**
- "My file won't upload" - Check file size and format
- "Ward names don't match" - Ensure consistent naming
- "Missing shapefile error" - Make sure to upload both files
"""
    
    def _analysis_help(self, request: str, has_data: bool) -> str:
        """Provide help about analysis features."""
        if not has_data:
            return """
**Analysis Features in ChatMRPT:**

To use analysis features, you first need to upload your data. Click the 📎 icon to get started!

Once you have data, ChatMRPT offers:

**1. Composite Risk Scoring**
- Combines multiple indicators into a single risk score
- Weighs factors like population density, poverty, health access
- Identifies wards with highest malaria vulnerability

**2. PCA (Principal Component Analysis)**
- Advanced statistical method
- Identifies hidden patterns in your data
- Reduces complex datasets to key risk factors

**3. Spatial Analysis**
- Maps risk distribution across wards
- Identifies geographic clusters of high risk
- Analyzes urban vs rural patterns

**4. Variable Relationships**
- Understands how different factors interact
- Identifies which variables contribute most to risk
- Provides evidence-based insights

Upload your data to unlock these powerful analysis tools!
"""
        else:
            return """
**Ready to Analyze Your Data!**

Here are the analysis options available:

**🎯 Quick Start:**
Just say: "Analyze malaria risk in my data"

**📊 Analysis Methods:**

**1. Composite Scoring**
- Say: "Run composite analysis"
- Combines all relevant variables
- Creates overall vulnerability scores
- Best for: Quick risk assessment

**2. PCA Analysis**
- Say: "Use PCA method"
- Finds hidden patterns statistically
- Reduces data complexity
- Best for: Deep insights

**3. Custom Analysis**
- Say: "Analyze using [specific variables]"
- Focus on particular factors
- Compare different scenarios

**📈 What You'll Get:**
- Risk scores for each ward (0-100)
- Ranked list of vulnerable areas
- Key contributing factors
- Interactive visualizations
- Actionable recommendations

**💡 Pro Tips:**
- Ask: "Which analysis method should I use?"
- Try: "Compare top 10 vs bottom 10 wards"
- Request: "Explain why [ward] is high risk"

**Ready?** Just tell me what you'd like to analyze!
"""
    
    def _visualization_help(self, request: str, has_data: bool) -> str:
        """Provide help about visualization features."""
        return """
**Visualization Features in ChatMRPT:**

**📊 Available Visualizations:**

**1. Risk Maps** 🗺️
- Interactive choropleth maps
- Color-coded by risk levels
- Hover for ward details
- Say: "Show me a risk map"

**2. Variable Maps** 🎨
- Map any individual variable
- See spatial distribution
- Say: "Map poverty levels" or "Show population density map"

**3. Box Plots** 📈
- Compare ward distributions
- Identify outliers
- Say: "Create vulnerability box plot"

**4. Comparison Charts** 📊
- Bar charts for top/bottom wards
- Variable contribution analysis
- Say: "Compare high-risk wards"

**🎮 Visualization Controls:**
- **Zoom**: Scroll or pinch to zoom
- **Pan**: Click and drag to move
- **Hover**: See detailed information
- **Expand**: Click the expand icon for fullscreen
- **Navigate**: Use arrow buttons for multi-page visualizations

**💡 Tips:**
- Say "Show me different views" for multiple perspectives
- Ask "Visualize [specific variable]" to focus on one factor
- Request "Side-by-side comparison" for multiple maps

**Export Options:**
- Right-click to save images
- Use report generation for high-quality exports
"""
    
    def _report_help(self, request: str, has_data: bool) -> str:
        """Provide help about report generation."""
        return """
**Report Generation in ChatMRPT:**

**📄 How to Generate Reports:**

**Step 1: Complete Your Analysis**
- Run risk analysis first
- Create your visualizations
- Explore the data

**Step 2: Click the Report Button** 📄
- Find the **document icon** next to the upload button
- Click to open report options

**Step 3: Choose Report Type:**
- **PDF**: Professional document with all findings
- **HTML**: Interactive web-based report
- **Markdown**: Technical documentation format

**📊 Report Contents:**
- Executive summary
- Methodology explanation
- Data quality assessment
- Risk analysis results
- Ward rankings and scores
- Interactive visualizations
- Recommendations

**🎯 Quick Options:**
- Say: "Generate PDF report"
- Or: "Create executive summary"
- Or: "Export analysis results"

**💡 Advanced Features:**
- **Custom Reports**: Visit the Report Builder
- **Selective Sections**: Choose what to include
- **Multiple Formats**: Generate different versions

**📥 After Generation:**
- Download link appears in chat
- Reports saved to your session
- Can regenerate anytime
"""
    
    def _ui_elements_help(self, request: str, has_data: bool) -> str:
        """Provide help about UI elements."""
        return """
**ChatMRPT Interface Guide:**

**🎯 Main Elements:**

**1. Chat Area** 💬
- Center of the screen
- Type your questions here
- View responses and results

**2. Input Bar** (Bottom)
- **📎 Paperclip**: Upload data files
- **📄 Document**: Generate reports
- **Text field**: Type your messages
- **➤ Send**: Submit your message

**3. Navigation Menu** (Left side)
- **☰ Hamburger**: Open/close menu
- **💬 Chat**: Main conversation (you are here)
- **🌙 Dark Mode**: Toggle theme
- **🌐 Language**: Change language

**4. Visualization Areas**
- Appear in chat after analysis
- **⤢ Expand icon**: View fullscreen
- **◀ ▶ Arrows**: Navigate pages
- Hover for details

**🎨 Visual Indicators:**
- **Green**: Success/Low risk
- **Yellow**: Warning/Medium risk  
- **Red**: Alert/High risk
- **Blue**: Information/Neutral

**⌨️ Tips:**
- Press Enter to send messages
- Drag and drop files to upload
- Click any visualization to interact

**Can't find something?** Just ask: "Where is the [feature name]?"
"""
    
    def _features_help(self, request: str, has_data: bool) -> str:
        """Provide help about ChatMRPT features."""
        return """
**ChatMRPT Features Overview:**

**🔬 Core Capabilities:**

**1. Data Analysis**
- Malaria risk assessment
- Vulnerability scoring
- Multi-factor analysis
- Statistical processing

**2. Geospatial Intelligence**
- Ward-level mapping
- Spatial clustering
- Urban/rural classification
- Settlement analysis

**3. Smart Visualizations**
- Interactive maps
- Statistical charts
- Comparative analysis
- Real-time rendering

**4. Report Generation**
- Automated insights
- Professional PDFs
- Custom templates
- Export options

**🤖 AI-Powered Features:**
- Natural language understanding
- Intelligent recommendations
- Contextual explanations
- Adaptive responses

**📊 Analysis Methods:**
- Composite scoring
- PCA (Principal Component Analysis)
- Correlation analysis
- Trend identification

**🔄 Workflow Support:**
- Data validation
- Error handling
- Progress tracking
- Session management

**🌍 Multi-language Support:**
- English, Hausa, Yoruba, Igbo
- French, Arabic
- Automatic translation

**💡 Special Features:**
- TPR analysis for test data
- Settlement footprint analysis
- Variable selection guidance
- Methodology explanations
"""
    
    def _tpr_help(self, request: str, has_data: bool) -> str:
        """Provide help about TPR analysis."""
        return """
**TPR (Test Positivity Rate) Analysis:**

**📊 What is TPR?**
Test Positivity Rate = (Positive Tests / Total Tests) × 100

**📁 How to Use TPR Analysis:**

**Step 1: Upload NMEP Data**
- Click the 📎 upload button
- Select "TPR Analysis" tab
- Upload your NMEP Excel file

**Step 2: Configure Analysis**
- Select your state
- Choose facilities to include
- Pick age groups (Under 5, Over 5, Pregnant)
- Select time period

**Step 3: Run Analysis**
The system will:
- Calculate TPR for each ward
- Extract environmental variables
- Generate risk assessments
- Create visualizations

**📈 What You Get:**
- Ward-level TPR percentages
- Facility performance metrics
- Age-stratified analysis
- Environmental correlations
- Downloadable results

**🎯 Key Features:**
- Handles both RDT and microscopy data
- Automatic data validation
- Missing data handling
- Geopolitical zone mapping

**💡 Tips:**
- Ensure facility names are consistent
- Check date formats (YYYY-MM)
- Include all testing data available
- Review facility coverage

**Need help with your NMEP file?** Ask: "Show me NMEP file format"
"""
    
    def _get_suggestions(self, has_data: bool) -> List[str]:
        """Get contextual suggestions based on user state."""
        if not has_data:
            return [
                "Upload your data",
                "Load sample data",
                "Learn about analysis methods",
                "View feature overview"
            ]
        else:
            return [
                "Analyze malaria risk",
                "Show me a risk map",
                "Generate report",
                "Explain the methodology"
            ]
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of this tool."""
        return [
            "Explain how to use ChatMRPT",
            "Guide through data upload process",
            "Describe analysis features",
            "Help with visualization tools",
            "Explain report generation",
            "Describe UI elements and buttons",
            "Provide workflow guidance",
            "Answer questions about features"
        ]