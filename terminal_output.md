127.0.0.1 - - [20/Jul/2025 20:45:27] "POST /send_message_streaming HTTP/1.1" 200 -
[2025-07-20 20:45:31,243] INFO in events: Logged LLM interaction: standard in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:45:31,244] DEBUG in analysis_routes: Sending streaming chunk: {"content": "Your dataset includes 31 variables, categorized into health indicators, environmental factors, socioeconomic variables, and geographic identifiers. Key variables for malaria risk include:\n\n- **pfpr (Plasmodium falciparum prevalence rate)**: Indicates malaria transmission intensity.\n- **mean_rainfall**: High values suggest potential mosquito breeding sites.\n- **housing_quality**: Poor scores indicate vulnerability to mosquito entry.\n\nIn this dataset, pfpr is crucial for assessing malaria prevalence, while environmental factors like rainfall and socioeconomic indicators such as housing quality provide context for transmission dynamics. For instance, high rainfall combined with poor housing can significantly increase malaria risk.\n\n**Action Suggestion**: Focus on wards with high pfpr and poor housing quality for targeted interventions, such as distributing insecticide-treated nets (ITNs) and improving housing infrastructure to reduce mosquito entry. Would you like me to run a detailed malaria risk analysis on this data?", "status": "success", "done": true}
[2025-07-20 20:45:31,273] INFO in core: Logged assistant message for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:45:43,732] DEBUG in development: Request: POST http://localhost:5015/send_message_streaming
[2025-07-20 20:45:43,732] INFO in decorators: send_message_streaming executed in 0.00 seconds
[2025-07-20 20:45:43,753] INFO in analysis_routes: Processing streaming message: 'Run malaria risk analysis to rank wards...'
[2025-07-20 20:45:43,753] INFO in analysis_routes: Using real streaming system with proper line break preservation
[2025-07-20 20:45:43,753] INFO in request_interpreter: 🎯 Permission flag found! User message: 'Run malaria risk analysis to rank wards'
[2025-07-20 20:45:44,571] INFO in events: Logged LLM interaction: streaming_function_calling in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:45:44,572] DEBUG in request_interpreter: Tool call detected: run_complete_analysis with args: {"session_id":"current"}
[2025-07-20 20:45:44,572] DEBUG in request_interpreter: Executing tool: run_complete_analysis with args: {'session_id': '6e90b139-5d30-40fd-91ad-4af66fec5f00'}
[2025-07-20 20:45:44,596] INFO in events: Logged tool_execution_start event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:45:44,597] INFO in complete_analysis_tools: Starting complete dual-method analysis for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:45:44,597] INFO in complete_analysis_tools: Custom variables - Composite: None, PCA: None
[2025-07-20 20:45:44,625] INFO in events: Logged variable_validation event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:45:44,626] INFO in complete_analysis_tools: 🚀 Starting composite analysis...
[2025-07-20 20:45:44,654] INFO in events: Logged composite_analysis_start event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:45:44,716] INFO in __init__: ⚠️ FALLBACK: Loaded raw data from raw_data.csv (will need cleaning)
[2025-07-20 20:45:44,800] INFO in __init__: Reloaded shapefile data from raw.shp (new workflow)
[2025-07-20 20:45:44,821] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:45:44,824] WARNING in unified_dataset_builder: Files not found (attempt 1), waiting...
[2025-07-20 20:45:45,829] WARNING in unified_dataset_builder: Files not found (attempt 2), waiting...
[2025-07-20 20:45:46,833] ERROR in unified_dataset_builder: ❌ All load attempts failed for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:45:46,833] WARNING in __init__: load_unified_dataset returned None
[2025-07-20 20:45:46,833] INFO in __init__: DataHandler initialized with modular architecture - Session: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:45:46,833] INFO in engine: 📊 Starting standalone composite analysis (settlement integration removed)

PIPELINE DEBUG: Starting run_full_analysis_pipeline
PIPELINE DEBUG: session_id=6e90b139-5d30-40fd-91ad-4af66fec5f00
PIPELINE DEBUG: selected_variables=None
PIPELINE DEBUG: na_methods=None
PIPELINE DEBUG: custom_relationships=None
PIPELINE DEBUG: llm_manager=False
PIPELINE DEBUG: metadata=False
PIPELINE DEBUG: interaction_logger=False
[2025-07-20 20:45:46,834] INFO in data_preparation: Step 1: Deferred cleaning (raw data → ward fixes + spatial imputation)
[2025-07-20 20:45:46,834] INFO in data_preparation: Checking for ward name mismatches...
[2025-07-20 20:45:46,835] INFO in validation: No ward name mismatches found
[2025-07-20 20:45:46,835] INFO in data_preparation: No ward name mismatches detected
[2025-07-20 20:45:46,835] INFO in data_preparation: Checking for duplicate ward names...
[2025-07-20 20:45:46,835] INFO in data_preparation: 🔧 Found 38 duplicate ward names - fixing with WardCode format
[2025-07-20 20:45:46,849] INFO in data_preparation: ✅ Successfully fixed all duplicate ward names using WardCode format
[2025-07-20 20:45:46,849] INFO in data_preparation: 📝 Fixed 17 ward groups: Dawaki, Falgore, Goron Dutse, Gurjiya, Gwarmai, Kadawa, Kanwa, Karfi, Maraku, Sabon Gari, Shuwaki, Tarauni, Tsakuwa, Unguwar Rimi, Wangara, Yalwa, Zango
[2025-07-20 20:45:46,849] INFO in data_preparation: Applying spatial neighbor imputation for missing values...
[2025-07-20 20:45:51,925] WARNING in validation: Found 55 ward name mismatches
[2025-07-20 20:45:51,949] INFO in pipeline: Step 1.5: Applying unified variable selection
[2025-07-20 20:45:51,949] INFO in variable_selection_coordinator: 🌍 Checking for region-aware variable selection
[2025-07-20 20:45:51,950] INFO in region_aware_selection: Detected zone 'North_West' from StateCode: KN
[2025-07-20 20:45:51,950] INFO in region_aware_selection: 📊 COLUMN ANALYSIS: Total columns in data: 31
[2025-07-20 20:45:51,950] INFO in region_aware_selection: 🔍 IDENTIFIER COLUMNS: ['WardName', 'StateCode', 'WardCode', 'LGACode', 'ward_name', 'ward_code', 'X', 'X.1', 'X.2', 'X.3', 'X.4', 'X.5', 'index', 'Unnamed: 0', 'country_na', 'country_co', 'country_name', 'country_code', 'state_name', 'state_code', 'lga_name', 'lga_code', 'global_id', 'source', 'source_dat', 'properties', 'geometry', 'Shape_Area', 'Shape_Leng']
[2025-07-20 20:45:51,950] INFO in region_aware_selection: ✅ ANALYSIS VARIABLES: 25 available - ['Urban', 'Source', 'Timestamp', 'GlobalID', 'AMAPCODE', 'mean_EVI', 'mean_NDVI', 'mean_rainfall', 'distance_to_water', 'RH_mean']...
[2025-07-20 20:45:51,951] INFO in region_aware_selection: 🔍 Fuzzy matched 'evi' to 'mean_EVI'
[2025-07-20 20:45:51,952] INFO in region_aware_selection: 🔍 Fuzzy matched 'distance_to_waterbodies' to 'distance_to_water'
[2025-07-20 20:45:51,953] INFO in region_aware_selection: 🔍 Fuzzy matched 'soil_wetness' to 'mean_soil_wetness'
[2025-07-20 20:45:51,955] INFO in region_aware_selection: ✅ Validated 7/7 variables
[2025-07-20 20:45:51,955] INFO in region_aware_selection: Zone North_West: Selected 7/7 scientifically-validated variables
[2025-07-20 20:45:51,955] INFO in variable_selection_coordinator: 🎯 ZONE DETECTED: North_West - using scientifically-validated variables
[2025-07-20 20:45:51,955] INFO in variable_selection_coordinator: 🔬 ZONE VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:45:51,955] INFO in variable_selection_coordinator: ✅ UNIFIED SELECTION: 7 variables selected via region_specific
[2025-07-20 20:45:51,955] INFO in variable_selection_coordinator: 📋 VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:45:51,955] INFO in pipeline: ✅ UNIFIED SELECTION: North_West zone, 7 variables selected via region_specific
[2025-07-20 20:45:51,960] INFO in pipeline: 💾 Saved unified variable metadata to instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/unified_variable_metadata.json
[2025-07-20 20:45:51,960] INFO in data_preparation: Step 2: Determining variable relationships
[2025-07-20 20:45:51,960] INFO in data_preparation: 🔧 CUSTOM ANALYSIS: Looking for variables ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness'] in cleaned data
[2025-07-20 20:45:51,960] INFO in data_preparation: 🔧 Available columns: ['X.1', 'X', 'WardName', 'StateCode', 'WardCode', 'LGACode', 'Urban', 'Source', 'Timestamp', 'GlobalID', 'AMAPCODE', 'mean_EVI', 'mean_NDVI', 'mean_rainfall', 'distance_to_water', 'RH_mean', 'temp_mean', 'housing_quality', 'pfpr', 'avgRAD', 'flood', 'NDWI', 'NDMI', 'elevation', 'mean_soil_wetness', 'settlement_type', 'u5_tpr_rdt', 'totalArea', 'urbanArea', 'urbanPercentage', 'building_height']
[2025-07-20 20:45:51,960] INFO in data_preparation: ✅ Exact match: pfpr
[2025-07-20 20:45:51,960] INFO in data_preparation: ✅ Exact match: u5_tpr_rdt
[2025-07-20 20:45:51,960] INFO in data_preparation: ✅ Exact match: housing_quality
[2025-07-20 20:45:51,960] INFO in data_preparation: ✅ Exact match: elevation
[2025-07-20 20:45:51,961] INFO in data_preparation: ✅ Exact match: mean_EVI
[2025-07-20 20:45:51,961] INFO in data_preparation: ✅ Exact match: distance_to_water
[2025-07-20 20:45:51,961] INFO in data_preparation: ✅ Exact match: mean_soil_wetness
[2025-07-20 20:45:51,961] INFO in data_preparation: Using 7 selected variables for relationships: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:45:51,961] INFO in data_preparation: Step 3: Normalizing data
[2025-07-20 20:45:51,961] INFO in data_preparation: Custom analysis: normalizing ALL variables, will select ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness'] for scoring later
[2025-07-20 20:46:07,759] INFO in scoring_stages: Step 4: Calculating composite scores
[2025-07-20 20:46:07,759] INFO in scoring_stages: ✅ COMPOSITE MATCH: 'pfpr' → 'pfpr'
[2025-07-20 20:46:07,760] INFO in scoring_stages: ✅ COMPOSITE MATCH: 'u5_tpr_rdt' → 'u5_tpr_rdt'
[2025-07-20 20:46:07,760] INFO in scoring_stages: ✅ COMPOSITE MATCH: 'housing_quality' → 'housing_quality'
[2025-07-20 20:46:07,760] INFO in scoring_stages: ✅ COMPOSITE MATCH: 'elevation' → 'elevation'
[2025-07-20 20:46:07,760] INFO in scoring_stages: ✅ COMPOSITE MATCH: 'mean_EVI' → 'mean_evi'
[2025-07-20 20:46:07,760] INFO in scoring_stages: ✅ COMPOSITE MATCH: 'distance_to_water' → 'distance_to_water'
[2025-07-20 20:46:07,760] INFO in scoring_stages: ✅ COMPOSITE MATCH: 'mean_soil_wetness' → 'mean_soil_wetness'
[2025-07-20 20:46:07,760] INFO in scoring_stages: 🔄 COMPOSITE METHOD: Using 7 unified variables: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_evi', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:07,761] WARNING in scoring: Too many variables (7), limiting to essential combinations
[2025-07-20 20:46:07,761] INFO in scoring: Generating 16 composite score models from 5 variables
[2025-07-20 20:46:07,786] INFO in scoring: Successfully generated 16 composite score models
PIPELINE DEBUG: Composite scoring completed successfully
PIPELINE DEBUG: Variables used: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_evi', 'distance_to_water', 'mean_soil_wetness']
PIPELINE DEBUG: Applying composite_scores fix immediately...
PIPELINE DEBUG: About to apply composite_scores fix...
PIPELINE DEBUG: composite_scores_mean exists and is not None
PIPELINE DEBUG: composite_scores_mean type: <class 'dict'>
PIPELINE DEBUG: Set data_handler.composite_scores = full dict with scores (shape: (484, 17)) and formulas
PIPELINE DEBUG: composite_scores fix applied successfully!
PIPELINE DEBUG: Continuing with remaining stages...
[2025-07-20 20:46:07,787] INFO in scoring_stages: Step 5: Calculating vulnerability rankings

🧮 PIPELINE DEBUG: Starting vulnerability ranking calculation...
📊 PIPELINE DEBUG: Composite scores available: True
📈 PIPELINE DEBUG: Composite scores shape: (484, 17)
🤖 PIPELINE DEBUG: Found 16 model columns: ['model_1', 'model_2', 'model_3', 'model_4', 'model_5', 'model_6', 'model_7', 'model_8', 'model_9', 'model_10', 'model_11', 'model_12', 'model_13', 'model_14', 'model_15', 'model_16']

🔍 VULNERABILITY DEBUG: Starting analyze_vulnerability function
📊 VULNERABILITY DEBUG: n_categories=3
🔧 VULNERABILITY DEBUG: composite_scores type: <class 'dict'>
📈 VULNERABILITY DEBUG: Scores DataFrame shape: (484, 17)
📋 VULNERABILITY DEBUG: Scores DataFrame columns: ['WardName', 'model_1', 'model_2', 'model_3', 'model_4', 'model_5', 'model_6', 'model_7', 'model_8', 'model_9', 'model_10', 'model_11', 'model_12', 'model_13', 'model_14', 'model_15', 'model_16']
🤖 VULNERABILITY DEBUG: Found 16 model columns: ['model_1', 'model_2', 'model_3', 'model_4', 'model_5', 'model_6', 'model_7', 'model_8', 'model_9', 'model_10', 'model_11', 'model_12', 'model_13', 'model_14', 'model_15', 'model_16']
🏘️ VULNERABILITY DEBUG: Result DataFrame initialized with 484 wards
📊 VULNERABILITY DEBUG: Median scores calculated, range: 0.073 to 0.719
🏆 VULNERABILITY DEBUG: Ranking completed, top ward: Kafin Dabga (score: 0.719)
🎯 RISK CATEGORIZATION: Using simplified High/Medium/Low Risk system
📊 Total wards: 484
🚨 High Risk: 161 wards
📋 Medium Risk: 162 wards
✅ Low Risk: 161 wards
✅ RISK CATEGORIZATION: Complete!
🎯 Risk distribution: {'Medium Risk': np.int64(162), 'High Risk': np.int64(161), 'Low Risk': np.int64(161)}
🎉 VULNERABILITY DEBUG: Analysis complete, returning DataFrame with shape: (484, 4)
✅ PIPELINE DEBUG: Vulnerability rankings calculated, shape: (484, 4)
🎯 PIPELINE DEBUG: Category distribution: {'Medium Risk': np.int64(162), 'High Risk': np.int64(161), 'Low Risk': np.int64(161)}
💾 PIPELINE DEBUG: Stored vulnerability rankings in data_handler
🏆 PIPELINE DEBUG: Top 5 vulnerable wards: ['Kafin Dabga', 'Dugabau', 'Tamawa', 'Durmawa', 'Durun']
[2025-07-20 20:46:07,810] INFO in scoring_stages: Step 6: Processing urban extent
[2025-07-20 20:46:07,828] INFO in pipeline: Step 7: Validating variable consistency
[2025-07-20 20:46:07,828] INFO in variable_comparison_validator: 🔍 VALIDATION: Checking variable consistency
[2025-07-20 20:46:07,828] INFO in variable_comparison_validator:    📊 Composite variables: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_evi', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:07,829] INFO in variable_comparison_validator:    🔬 PCA variables: None
[2025-07-20 20:46:07,829] WARNING in pipeline: ⚠️ CONSISTENCY: No variables found for PCA method
[2025-07-20 20:46:07,829] INFO in pipeline: Analysis pipeline complete
PIPELINE DEBUG: About to apply composite_scores fix...
PIPELINE DEBUG: About to apply composite_scores fix...
PIPELINE DEBUG: composite_scores_mean exists and is not None
PIPELINE DEBUG: composite_scores_mean type: <class 'dict'>
PIPELINE DEBUG: Set data_handler.composite_scores = full dict with scores (shape: (484, 17)) and formulas
PIPELINE DEBUG: composite_scores fix applied, creating summary...
PIPELINE DEBUG: Saving analysis results to disk...
[2025-07-20 20:46:07,950] INFO in analysis: Analysis results saved successfully
PIPELINE DEBUG: Analysis results saved via coordinator
PIPELINE DEBUG: Creating unified dataset with region metadata...
🔧 Building comprehensive unified GeoParquet dataset...
[2025-07-20 20:46:08,007] INFO in __init__: ✅ PRIORITIZED: Loaded cleaned data from analysis_cleaned_data.csv (analysis-ready)
[2025-07-20 20:46:08,082] INFO in __init__: Reloaded shapefile data from raw.shp (new workflow)
[2025-07-20 20:46:08,116] INFO in __init__: Reloaded cleaned_data from analysis_cleaned_data.csv
[2025-07-20 20:46:08,138] INFO in __init__: Reloaded normalized_data from analysis_normalized_data.csv
[2025-07-20 20:46:08,146] INFO in __init__: Reloaded vulnerability_rankings from analysis_vulnerability_rankings.csv
[2025-07-20 20:46:08,168] INFO in __init__: Reloaded composite_scores_mean from composite_scores.csv
[2025-07-20 20:46:08,186] INFO in __init__: Reloaded composite_scores from analysis_composite_scores.csv
[2025-07-20 20:46:08,187] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:08,191] WARNING in unified_dataset_builder: Files not found (attempt 1), waiting...
[2025-07-20 20:46:09,196] WARNING in unified_dataset_builder: Files not found (attempt 2), waiting...
[2025-07-20 20:46:10,202] ERROR in unified_dataset_builder: ❌ All load attempts failed for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:10,202] WARNING in __init__: load_unified_dataset returned None
[2025-07-20 20:46:10,202] INFO in __init__: DataHandler initialized with modular architecture - Session: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00
📊 CSV loaded: 484 rows, 31 columns
🗺️ Shapefile loaded: 484 features
📈 Composite results loaded: analysis_vulnerability_rankings.csv
🎯 Model scores loaded: 16 individual models from composite_scores.csv
📋 Model formulas loaded: 16 model definitions from model_formulas.csv
🔬 No PCA results found - attempting dynamic PCA analysis...
[2025-07-20 20:46:10,328] INFO in __init__: ✅ PRIORITIZED: Loaded cleaned data from analysis_cleaned_data.csv (analysis-ready)
[2025-07-20 20:46:10,395] INFO in __init__: Reloaded shapefile data from raw.shp (new workflow)
[2025-07-20 20:46:10,421] INFO in __init__: Reloaded cleaned_data from analysis_cleaned_data.csv
[2025-07-20 20:46:10,435] INFO in __init__: Reloaded normalized_data from analysis_normalized_data.csv
[2025-07-20 20:46:10,444] INFO in __init__: Reloaded vulnerability_rankings from analysis_vulnerability_rankings.csv
[2025-07-20 20:46:10,471] INFO in __init__: Reloaded composite_scores_mean from composite_scores.csv
[2025-07-20 20:46:10,488] INFO in __init__: Reloaded composite_scores from analysis_composite_scores.csv
[2025-07-20 20:46:10,488] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:10,493] WARNING in unified_dataset_builder: Files not found (attempt 1), waiting...
[2025-07-20 20:46:11,497] WARNING in unified_dataset_builder: Files not found (attempt 2), waiting...
[2025-07-20 20:46:12,501] ERROR in unified_dataset_builder: ❌ All load attempts failed for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:12,501] WARNING in __init__: load_unified_dataset returned None
[2025-07-20 20:46:12,501] INFO in __init__: DataHandler initialized with modular architecture - Session: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:12,501] INFO in pca_pipeline: 🔬 PCA PIPELINE: Initialized for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:12,502] INFO in pca_pipeline: 🚀 PCA PIPELINE: Starting complete PCA analysis
[2025-07-20 20:46:12,502] INFO in pca_pipeline: 📊 PCA DATA: Loaded cleaned data with shape (484, 31)
[2025-07-20 20:46:12,502] INFO in pca_pipeline: 🔄 PCA PIPELINE: Applying unified variable selection
[2025-07-20 20:46:12,502] INFO in variable_selection_coordinator: 🌍 Checking for region-aware variable selection
[2025-07-20 20:46:12,502] INFO in region_aware_selection: Detected zone 'North_West' from StateCode: KN
[2025-07-20 20:46:12,502] INFO in region_aware_selection: 📊 COLUMN ANALYSIS: Total columns in data: 31
[2025-07-20 20:46:12,503] INFO in region_aware_selection: 🔍 IDENTIFIER COLUMNS: ['WardName', 'StateCode', 'WardCode', 'LGACode', 'ward_name', 'ward_code', 'X', 'X.1', 'X.2', 'X.3', 'X.4', 'X.5', 'index', 'Unnamed: 0', 'country_na', 'country_co', 'country_name', 'country_code', 'state_name', 'state_code', 'lga_name', 'lga_code', 'global_id', 'source', 'source_dat', 'properties', 'geometry', 'Shape_Area', 'Shape_Leng']
[2025-07-20 20:46:12,503] INFO in region_aware_selection: ✅ ANALYSIS VARIABLES: 25 available - ['Urban', 'Source', 'Timestamp', 'GlobalID', 'AMAPCODE', 'mean_EVI', 'mean_NDVI', 'mean_rainfall', 'distance_to_water', 'RH_mean']...
[2025-07-20 20:46:12,503] INFO in region_aware_selection: 🔍 Fuzzy matched 'evi' to 'mean_EVI'
[2025-07-20 20:46:12,504] INFO in region_aware_selection: 🔍 Fuzzy matched 'distance_to_waterbodies' to 'distance_to_water'
[2025-07-20 20:46:12,504] INFO in region_aware_selection: 🔍 Fuzzy matched 'soil_wetness' to 'mean_soil_wetness'
[2025-07-20 20:46:12,505] INFO in region_aware_selection: ✅ Validated 7/7 variables
[2025-07-20 20:46:12,505] INFO in region_aware_selection: Zone North_West: Selected 7/7 scientifically-validated variables
[2025-07-20 20:46:12,505] INFO in variable_selection_coordinator: 🎯 ZONE DETECTED: North_West - using scientifically-validated variables
[2025-07-20 20:46:12,506] INFO in variable_selection_coordinator: 🔬 ZONE VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:12,506] INFO in variable_selection_coordinator: ✅ UNIFIED SELECTION: 7 variables selected via region_specific
[2025-07-20 20:46:12,506] INFO in variable_selection_coordinator: 📋 VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:12,506] INFO in pca_pipeline: ✅ PCA UNIFIED SELECTION: North_West zone, 7 variables selected via region_specific
[2025-07-20 20:46:12,506] INFO in pca_pipeline: 🧹 PCA CLEANING: Starting data cleaning and preparation
[2025-07-20 20:46:12,506] INFO in pca_pipeline: 🏘️ PCA WARD: Found ward column: WardName
[2025-07-20 20:46:12,506] INFO in pca_pipeline: 📋 PCA SELECTION: Using 7 user-specified variables
[2025-07-20 20:46:12,507] INFO in pca_pipeline: ✅ PCA MISSING: No missing values found
[2025-07-20 20:46:12,507] INFO in pca_pipeline: ✅ PCA CLEANING: Prepared data with 7 variables and 484 wards
[2025-07-20 20:46:12,507] INFO in pca_pipeline: 📋 PCA VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:12,507] INFO in pca_pipeline: 📊 PCA STANDARDIZATION: Applying Z-score standardization
[2025-07-20 20:46:12,511] INFO in pca_pipeline: ✅ PCA STANDARDIZATION: Standardized 7 variables
[2025-07-20 20:46:12,513] INFO in pca_pipeline: 📊 PCA STATS: Mean ≈ 0.000, Std ≈ 1.001
[2025-07-20 20:46:12,513] INFO in pca_pipeline: 🔬 PCA ANALYSIS: Running principal component analysis
[2025-07-20 20:46:12,632] INFO in pca_pipeline: 📊 PCA IMPORTANCE: Top variables - ['distance_to_water', 'mean_EVI', 'pfpr']
[2025-07-20 20:46:12,632] INFO in pca_pipeline: ✅ PCA ANALYSIS: Completed with 5 components explaining 94.4% variance
[2025-07-20 20:46:12,632] INFO in pca_pipeline: 🏆 PCA RANKINGS: Creating vulnerability rankings from PCA scores
[2025-07-20 20:46:12,634] INFO in pca_pipeline: 📊 PCA CATEGORIES: 161 High Risk, 162 Medium Risk, 161 Low Risk
[2025-07-20 20:46:12,635] INFO in pca_pipeline: ✅ PCA RANKINGS: Created rankings for 484 wards
[2025-07-20 20:46:12,635] INFO in pca_pipeline: 🏆 PCA TOP 5: ['Kabuwaya', 'Dala', 'Kantudu', 'Jakara', 'Adakawa']
[2025-07-20 20:46:12,649] INFO in pca_pipeline: 💾 PCA SAVE: Saved PCA rankings to instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/analysis_vulnerability_rankings_pca.csv
[2025-07-20 20:46:12,673] INFO in pca_pipeline: 💾 PCA SAVE: Saved all PCA analysis files to session folder
[2025-07-20 20:46:12,673] INFO in pca_pipeline: ✅ PCA STORAGE: Stored PCA results in data handler with correct format
[2025-07-20 20:46:12,673] INFO in pca_pipeline: 📊 PCA RANKINGS: 484 wards with vulnerability categories
[2025-07-20 20:46:12,674] INFO in pca_pipeline: ✅ PCA PIPELINE: Complete PCA analysis finished successfully
✅ Extracted PCA rankings from 'pca_rankings': 484 wards
✅ Extracted PCA loadings from 'variable_importance'
✅ Successfully ran PCA using app.analysis.pca_pipeline.run_independent_pca_analysis
🔧 Preserved original column names: ['X.1', 'X', 'WardName', 'StateCode', 'WardCode']...
✅ No duplicate ward names found in WardName
🔧 Found 38 duplicate ward names in WardName - fixing with WardCode...
✅ Fixed all duplicate ward names - all 484 wards now have unique names
🔑 Using 'WardName' for merge (unique names)
🔑 Using 'WardName' for merge (unique names)
🔑 Using WardCode and WardCode for precise geometry matching
🎯 Matched geometry for 484/484 wards using WardCode
✅ Preserved all 484 CSV wards with geometry where possible
🔗 Preserved CSV wards with geometry: 484 wards (maintaining original 484)
🏷️ Smart metadata created for 32 columns:
   other: 16 columns
   identification: 4 columns
   infrastructure: 4 columns
   environmental: 5 columns
   health: 1 columns
   spatial: 2 columns
🔑 Using 'WardName' for merge (unique names)
🔍 WARD COUNT DEBUG: Starting integration with 484 wards
🔍 Attempting to reconstruct region metadata from analysis files...
[2025-07-20 20:46:12,756] INFO in __init__: ✅ PRIORITIZED: Loaded cleaned data from analysis_cleaned_data.csv (analysis-ready)
[2025-07-20 20:46:12,816] INFO in __init__: Reloaded shapefile data from raw.shp (new workflow)
[2025-07-20 20:46:12,839] INFO in __init__: Reloaded cleaned_data from analysis_cleaned_data.csv
[2025-07-20 20:46:12,853] INFO in __init__: Reloaded normalized_data from analysis_normalized_data.csv
[2025-07-20 20:46:12,863] INFO in __init__: Reloaded vulnerability_rankings from analysis_vulnerability_rankings.csv
[2025-07-20 20:46:12,873] INFO in __init__: Reloaded vulnerability_rankings_pca from analysis_vulnerability_rankings_pca.csv
[2025-07-20 20:46:12,896] INFO in __init__: Reloaded composite_scores_mean from composite_scores.csv
[2025-07-20 20:46:12,913] INFO in __init__: Reloaded composite_scores from analysis_composite_scores.csv
[2025-07-20 20:46:12,913] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:12,919] WARNING in unified_dataset_builder: Files not found (attempt 1), waiting...
[2025-07-20 20:46:13,924] WARNING in unified_dataset_builder: Files not found (attempt 2), waiting...
[2025-07-20 20:46:14,928] ERROR in unified_dataset_builder: ❌ All load attempts failed for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:14,928] WARNING in __init__: load_unified_dataset returned None
[2025-07-20 20:46:14,929] INFO in __init__: DataHandler initialized with modular architecture - Session: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:14,929] INFO in region_aware_selection: Detected zone 'North_West' from StateCode: KN
🔍 Reconstructed region metadata: North_West zone via StateCode: KN
🔍 WARD COUNT DEBUG: After region metadata: 484 wards (change: +0)
⚠️ No ward code column found - skipping duplicate fix
🔑 Using 'WardName' for merge (unique names)
🔍 COMPOSITE MERGE DEBUG: Before merge - GDF: 484 rows, Analysis: 484 rows
🔍 COMPOSITE MERGE DEBUG: Ward key 'WardName' duplicates in GDF: 0
🔍 COMPOSITE MERGE DEBUG: Comp key 'WardName' duplicates in analysis: 0
🔍 COMPOSITE MERGE DEBUG: After merge - GDF: 484 rows (change: +0)
📈 Integrated composite analysis: 5 columns -> composite_score, composite_rank, composite_category, overall_rank, vulnerability_category
⚠️ Could not add composite variables metadata: No module named 'app.data.data_handler'
⚠️ No ward code column found - skipping duplicate fix
🔑 Using 'WardName' for merge (unique names)
🔍 PCA MERGE DEBUG: Before merge - GDF: 484 rows, PCA: 484 rows
🔍 PCA MERGE DEBUG: Ward key 'WardName' duplicates in GDF: 0
🔍 PCA MERGE DEBUG: PCA key 'WardName' duplicates in analysis: 0
🔍 PCA MERGE DEBUG: After merge - GDF: 484 rows (change: +0)
🔍 Integrated PCA analysis: 3 columns -> pca_score, pca_rank, pca_category
🔍 WARD COUNT DEBUG: Final integration result: 484 wards (total change: +0)
🔑 Using 'WardName' for merge (unique names)
🎯 PCA coverage: 484/484 wards (100.0%)
🔑 Using 'WardName' for merge (unique names)
🔑 Using 'WardName' for merge (unique names)
🔍 Detected 16 model score columns: ['model_1', 'model_2', 'model_3', 'model_4', 'model_5']...
🎯 Integrated 16 individual model scores
📊 Added model consensus statistics based on 16 models
📋 Processing model metadata from 16 model definitions...
🔍 Available formula columns: ['model', 'variables', 'method']
📊 Processed 16 model formulas
📋 ✅ Model metadata integrated:
   📊 16 total models, 16 processed
   🔢 Average complexity: 1.00
   📈 Complexity range: 1.0 - 1.0
   🔤 5 unique variables used
   🏆 Top variables: ['pfpr', 'u5_tpr_rdt', 'housing_quality']
🌍 Added spatial metrics: area_km2, centroid coordinates, perimeter_km
🔍 Added enhanced method comparison metrics
   - Rank differences: 222.3 average absolute difference
   - Method consensus: 0.540 average consensus score
⚖️ Added consensus_risk_level harmonization
⚡ Optimized dataset structure for tool access
💾 Saved GeoParquet: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/unified_dataset.geoparquet
📄 Saved CSV backup: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/unified_dataset.csv
⚠️ Could not save pickle backup: local variable 'pickle_path' referenced before assignment
✅ Comprehensive unified dataset created: 484 wards, 80 columns
📁 Saved as: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/unified_dataset.geoparquet
PIPELINE DEBUG: ✅ Unified dataset created successfully: Comprehensive unified GeoParquet dataset ready with 484 wards and 80 columns
[2025-07-20 20:46:42,636] INFO in unified_dataset_builder: ✅ Loaded CSV (no geometry needed): (484, 79) - 580.3KB
PIPELINE DEBUG: ✅ Unified dataset loaded and assigned to data_handler: 484 rows, 79 columns
[2025-07-20 20:46:42,636] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:42,658] INFO in unified_dataset_builder: ✅ Loaded CSV (no geometry needed): (484, 79) - 580.3KB
[2025-07-20 20:46:42,658] INFO in __init__: ✅ Successfully loaded unified dataset: 484 rows, 79 columns
PIPELINE DEBUG: ✅ Force reloaded unified dataset through data handler
[2025-07-20 20:46:42,787] INFO in events: Logged composite_analysis_complete event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:46:42,788] INFO in complete_analysis_tools: ✅ Composite analysis completed successfully
[2025-07-20 20:46:42,790] INFO in complete_analysis_tools: 🔬 Starting PCA analysis...
[2025-07-20 20:46:42,815] INFO in events: Logged pca_analysis_start event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:46:42,874] INFO in __init__: ✅ PRIORITIZED: Loaded cleaned data from analysis_cleaned_data.csv (analysis-ready)
[2025-07-20 20:46:42,937] INFO in __init__: Reloaded shapefile data from raw.shp (new workflow)
[2025-07-20 20:46:42,961] INFO in __init__: Reloaded cleaned_data from analysis_cleaned_data.csv
[2025-07-20 20:46:42,974] INFO in __init__: Reloaded normalized_data from analysis_normalized_data.csv
[2025-07-20 20:46:42,983] INFO in __init__: Reloaded vulnerability_rankings from analysis_vulnerability_rankings.csv
[2025-07-20 20:46:42,991] INFO in __init__: Reloaded vulnerability_rankings_pca from analysis_vulnerability_rankings_pca.csv
[2025-07-20 20:46:43,013] INFO in __init__: Reloaded composite_scores_mean from composite_scores.csv
[2025-07-20 20:46:43,030] INFO in __init__: Reloaded composite_scores from analysis_composite_scores.csv
[2025-07-20 20:46:43,030] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:43,052] INFO in unified_dataset_builder: ✅ Loaded CSV (no geometry needed): (484, 79) - 580.3KB
[2025-07-20 20:46:43,053] INFO in __init__: ✅ Successfully loaded unified dataset: 484 rows, 79 columns
[2025-07-20 20:46:43,153] INFO in __init__: DataHandler initialized with modular architecture - Session: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:43,153] INFO in pca_pipeline: 🔬 PCA PIPELINE: Initialized for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:43,153] INFO in pca_pipeline: 🚀 PCA PIPELINE: Starting complete PCA analysis
[2025-07-20 20:46:43,153] INFO in pca_pipeline: 📊 PCA DATA: Loaded cleaned data with shape (484, 31)
[2025-07-20 20:46:43,154] INFO in pca_pipeline: 🔄 PCA PIPELINE: Applying unified variable selection
[2025-07-20 20:46:43,154] INFO in variable_selection_coordinator: 🌍 Checking for region-aware variable selection
[2025-07-20 20:46:43,154] INFO in region_aware_selection: Detected zone 'North_West' from StateCode: KN
[2025-07-20 20:46:43,154] INFO in region_aware_selection: 📊 COLUMN ANALYSIS: Total columns in data: 31
[2025-07-20 20:46:43,154] INFO in region_aware_selection: 🔍 IDENTIFIER COLUMNS: ['WardName', 'StateCode', 'WardCode', 'LGACode', 'ward_name', 'ward_code', 'X', 'X.1', 'X.2', 'X.3', 'X.4', 'X.5', 'index', 'Unnamed: 0', 'country_na', 'country_co', 'country_name', 'country_code', 'state_name', 'state_code', 'lga_name', 'lga_code', 'global_id', 'source', 'source_dat', 'properties', 'geometry', 'Shape_Area', 'Shape_Leng']
[2025-07-20 20:46:43,154] INFO in region_aware_selection: ✅ ANALYSIS VARIABLES: 25 available - ['Urban', 'Source', 'Timestamp', 'GlobalID', 'AMAPCODE', 'mean_EVI', 'mean_NDVI', 'mean_rainfall', 'distance_to_water', 'RH_mean']...
[2025-07-20 20:46:43,155] INFO in region_aware_selection: 🔍 Fuzzy matched 'evi' to 'mean_EVI'
[2025-07-20 20:46:43,155] INFO in region_aware_selection: 🔍 Fuzzy matched 'distance_to_waterbodies' to 'distance_to_water'
[2025-07-20 20:46:43,156] INFO in region_aware_selection: 🔍 Fuzzy matched 'soil_wetness' to 'mean_soil_wetness'
[2025-07-20 20:46:43,156] INFO in region_aware_selection: ✅ Validated 7/7 variables
[2025-07-20 20:46:43,156] INFO in region_aware_selection: Zone North_West: Selected 7/7 scientifically-validated variables
[2025-07-20 20:46:43,157] INFO in variable_selection_coordinator: 🎯 ZONE DETECTED: North_West - using scientifically-validated variables
[2025-07-20 20:46:43,157] INFO in variable_selection_coordinator: 🔬 ZONE VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:43,157] INFO in variable_selection_coordinator: ✅ UNIFIED SELECTION: 7 variables selected via region_specific
[2025-07-20 20:46:43,157] INFO in variable_selection_coordinator: 📋 VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:43,157] INFO in pca_pipeline: ✅ PCA UNIFIED SELECTION: North_West zone, 7 variables selected via region_specific
[2025-07-20 20:46:43,157] INFO in pca_pipeline: 🧹 PCA CLEANING: Starting data cleaning and preparation
[2025-07-20 20:46:43,157] INFO in pca_pipeline: 🏘️ PCA WARD: Found ward column: WardName
[2025-07-20 20:46:43,157] INFO in pca_pipeline: 📋 PCA SELECTION: Using 7 user-specified variables
[2025-07-20 20:46:43,158] INFO in pca_pipeline: ✅ PCA MISSING: No missing values found
[2025-07-20 20:46:43,158] INFO in pca_pipeline: ✅ PCA CLEANING: Prepared data with 7 variables and 484 wards
[2025-07-20 20:46:43,159] INFO in pca_pipeline: 📋 PCA VARIABLES: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:43,159] INFO in pca_pipeline: 📊 PCA STANDARDIZATION: Applying Z-score standardization
[2025-07-20 20:46:43,161] INFO in pca_pipeline: ✅ PCA STANDARDIZATION: Standardized 7 variables
[2025-07-20 20:46:43,162] INFO in pca_pipeline: 📊 PCA STATS: Mean ≈ 0.000, Std ≈ 1.001
[2025-07-20 20:46:43,162] INFO in pca_pipeline: 🔬 PCA ANALYSIS: Running principal component analysis
[2025-07-20 20:46:43,164] INFO in pca_pipeline: 📊 PCA IMPORTANCE: Top variables - ['distance_to_water', 'mean_EVI', 'pfpr']
[2025-07-20 20:46:43,164] INFO in pca_pipeline: ✅ PCA ANALYSIS: Completed with 5 components explaining 94.4% variance
[2025-07-20 20:46:43,164] INFO in pca_pipeline: 🏆 PCA RANKINGS: Creating vulnerability rankings from PCA scores
[2025-07-20 20:46:43,168] INFO in pca_pipeline: 📊 PCA CATEGORIES: 161 High Risk, 162 Medium Risk, 161 Low Risk
[2025-07-20 20:46:43,168] INFO in pca_pipeline: ✅ PCA RANKINGS: Created rankings for 484 wards
[2025-07-20 20:46:43,169] INFO in pca_pipeline: 🏆 PCA TOP 5: ['Kabuwaya', 'Dala', 'Kantudu', 'Jakara', 'Adakawa']
[2025-07-20 20:46:43,187] INFO in pca_pipeline: 💾 PCA SAVE: Saved PCA rankings to instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/analysis_vulnerability_rankings_pca.csv
[2025-07-20 20:46:43,206] INFO in pca_pipeline: 💾 PCA SAVE: Saved all PCA analysis files to session folder
[2025-07-20 20:46:43,206] INFO in pca_pipeline: ✅ PCA STORAGE: Stored PCA results in data handler with correct format
[2025-07-20 20:46:43,206] INFO in pca_pipeline: 📊 PCA RANKINGS: 484 wards with vulnerability categories
[2025-07-20 20:46:43,207] INFO in pca_pipeline: ✅ PCA PIPELINE: Complete PCA analysis finished successfully
[2025-07-20 20:46:43,233] INFO in events: Logged pca_analysis_complete event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:46:43,234] INFO in complete_analysis_tools: ✅ PCA analysis completed successfully
[2025-07-20 20:46:43,234] INFO in complete_analysis_tools: 🔄 Both analyses completed sequentially in 58.61 seconds
[2025-07-20 20:46:43,258] INFO in events: Logged sequential_analysis_complete event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:46:43,258] INFO in complete_analysis_tools: 📊 Creating unified dataset...
🔧 Building comprehensive unified GeoParquet dataset...
[2025-07-20 20:46:43,312] INFO in __init__: ✅ PRIORITIZED: Loaded cleaned data from analysis_cleaned_data.csv (analysis-ready)
[2025-07-20 20:46:43,377] INFO in __init__: Reloaded shapefile data from raw.shp (new workflow)
[2025-07-20 20:46:43,401] INFO in __init__: Reloaded cleaned_data from analysis_cleaned_data.csv
[2025-07-20 20:46:43,413] INFO in __init__: Reloaded normalized_data from analysis_normalized_data.csv
[2025-07-20 20:46:43,422] INFO in __init__: Reloaded vulnerability_rankings from analysis_vulnerability_rankings.csv
[2025-07-20 20:46:43,431] INFO in __init__: Reloaded vulnerability_rankings_pca from analysis_vulnerability_rankings_pca.csv
[2025-07-20 20:46:43,453] INFO in __init__: Reloaded composite_scores_mean from composite_scores.csv
[2025-07-20 20:46:43,472] INFO in __init__: Reloaded composite_scores from analysis_composite_scores.csv
[2025-07-20 20:46:43,472] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:43,492] INFO in unified_dataset_builder: ✅ Loaded CSV (no geometry needed): (484, 79) - 580.3KB
[2025-07-20 20:46:43,492] INFO in __init__: ✅ Successfully loaded unified dataset: 484 rows, 79 columns
[2025-07-20 20:46:43,593] INFO in __init__: DataHandler initialized with modular architecture - Session: instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00
📊 CSV loaded: 484 rows, 31 columns
🗺️ Shapefile loaded: 484 features
📈 Composite results loaded: analysis_vulnerability_rankings.csv
🎯 Model scores loaded: 16 individual models from composite_scores.csv
📋 Model formulas loaded: 16 model definitions from model_formulas.csv
🔍 PCA rankings loaded: analysis_vulnerability_rankings_pca.csv
🧮 PCA components loaded: 5 components from analysis_pca_scores.csv
[2025-07-20 20:46:43,654] ERROR in unified_dataset_builder: Error loading data sources: The truth value of a DataFrame is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
[2025-07-20 20:46:43,655] WARNING in complete_analysis_tools: ❌ Unified dataset creation failed: Error loading data: The truth value of a DataFrame is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
[2025-07-20 20:46:43,656] INFO in complete_analysis_tools: 📋 Generating dual-method comparison summary...
[2025-07-20 20:46:43,656] WARNING in complete_analysis_tools: Failed to mark analysis complete: Working outside of request context.

This typically means that you attempted to use functionality that needed
an active HTTP request. Consult the documentation on testing for
information about how to avoid this problem.
[2025-07-20 20:46:43,681] INFO in unified_dataset_builder: ✅ Loaded CSV (no geometry needed): (484, 79) - 580.3KB
🔍 SUMMARY DEBUG: Unified dataset loaded: 484 wards, 79 columns
🔍 SUMMARY DEBUG: First few columns: ['WardName', 'X.1', 'X', 'StateCode', 'WardCode', 'LGACode', 'Urban', 'Source', 'Timestamp', 'GlobalID']
🔍 SUMMARY DEBUG: ✅ Found 'composite_score' column
🔍 SUMMARY DEBUG: ✅ Found 'pca_score' column
🔍 SUMMARY DEBUG: ✅ Found 'WardName' column
🔍 SUMMARY DEBUG: ✅ Found 'WardCode' column
[2025-07-20 20:46:43,681] INFO in complete_analysis_tools: 🔍 UNIFIED DATASET DEBUG: Available columns: ['WardName', 'X.1', 'X', 'StateCode', 'WardCode', 'LGACode', 'Urban', 'Source', 'Timestamp', 'GlobalID', 'AMAPCODE', 'mean_EVI', 'mean_NDVI', 'mean_rainfall', 'distance_to_water', 'RH_mean', 'temp_mean', 'housing_quality', 'pfpr', 'avgRAD', 'flood', 'NDWI', 'NDMI', 'elevation', 'mean_soil_wetness', 'settlement_type', 'u5_tpr_rdt', 'totalArea', 'urbanArea', 'urbanPercentage', 'building_height', 'detected_zone', 'zone_detection_method', 'zone_climate', 'zone_priority_focus', 'zone_states', 'composite_score', 'composite_rank', 'composite_category', 'overall_rank', 'vulnerability_category', 'pca_score', 'pca_rank', 'pca_category', 'pca_coverage', 'model_1', 'model_2', 'model_3', 'model_4', 'model_5', 'model_6', 'model_7', 'model_8', 'model_9', 'model_10', 'model_11', 'model_12', 'model_13', 'model_14', 'model_15', 'model_16', 'model_mean_score', 'model_std_score', 'model_agreement', 'model_consensus', 'area_km2', 'centroid_lat', 'centroid_lon', 'perimeter_km', 'rank_difference', 'rank_difference_abs', 'method_agreement', 'combined_priority', 'method_consensus_score', 'better_ranking_method', 'consensus_risk_level', 'data_completeness', 'last_updated', 'dataset_version']
[2025-07-20 20:46:43,681] INFO in complete_analysis_tools: 🔍 UNIFIED DATASET DEBUG: Dataset shape: (484, 79)
[2025-07-20 20:46:43,681] INFO in complete_analysis_tools: 🔍 COLUMN DETECTION: Composite=composite_score, PCA=pca_score, Ward=WardName
[2025-07-20 20:46:43,715] INFO in complete_analysis_tools: 🔍 VARIABLE DETECTION: Composite vars: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_evi', 'distance_to_water', 'mean_soil_wetness']
[2025-07-20 20:46:43,716] INFO in complete_analysis_tools: 🔍 VARIABLE DETECTION: PCA vars: ['pfpr', 'u5_tpr_rdt', 'housing_quality', 'elevation', 'mean_EVI', 'distance_to_water']
[2025-07-20 20:46:43,716] INFO in complete_analysis_tools: 🔍 VARIABLE DETECTION: Composite data keys: ['variables_used', 'variable_selection_method', 'wards_analyzed', 'results']
[2025-07-20 20:46:43,716] INFO in complete_analysis_tools: 🔍 VARIABLE DETECTION: PCA data keys: ['method', 'pca_rankings', 'explained_variance', 'variable_importance', 'n_components', 'variables_used', 'ward_count', 'summary', 'variable_selection_method']
[2025-07-20 20:46:43,739] INFO in events: Logged tool_execution_complete event for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00, success: True
[2025-07-20 20:46:43,752] INFO in analysis_state_handler: Analysis complete for session 6e90b139-5d30-40fd-91ad-4af66fec5f00, updating state...
[2025-07-20 20:46:43,752] INFO in unified_data_state: Analysis complete for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:44,224] INFO in unified_data_state: Loaded unified dataset from geoparquet: (484, 80)
[2025-07-20 20:46:44,224] INFO in unified_data_state: Successfully loaded unified dataset after analysis: (484, 80)
[2025-07-20 20:46:44,225] INFO in analysis_state_handler: Analysis completion hook triggered for 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:44,226] INFO in analysis_state_handler: Data info: {'session_id': '6e90b139-5d30-40fd-91ad-4af66fec5f00', 'data_loaded': False, 'analysis_complete': True, 'stage': 'no_data', 'shape': (484, 80), 'columns': ['WardName', 'X.1', 'X', 'StateCode', 'WardCode', 'LGACode', 'Urban', 'Source', 'Timestamp', 'GlobalID', 'AMAPCODE', 'mean_EVI', 'mean_NDVI', 'mean_rainfall', 'distance_to_water', 'RH_mean', 'temp_mean', 'housing_quality', 'pfpr', 'avgRAD', 'flood', 'NDWI', 'NDMI', 'elevation', 'mean_soil_wetness', 'settlement_type', 'u5_tpr_rdt', 'totalArea', 'urbanArea', 'urbanPercentage', 'building_height', 'geometry', 'detected_zone', 'zone_detection_method', 'zone_climate', 'zone_priority_focus', 'zone_states', 'composite_score', 'composite_rank', 'composite_category', 'overall_rank', 'vulnerability_category', 'pca_score', 'pca_rank', 'pca_category', 'pca_coverage', 'model_1', 'model_2', 'model_3', 'model_4', 'model_5', 'model_6', 'model_7', 'model_8', 'model_9', 'model_10', 'model_11', 'model_12', 'model_13', 'model_14', 'model_15', 'model_16', 'model_mean_score', 'model_std_score', 'model_agreement', 'model_consensus', 'area_km2', 'centroid_lat', 'centroid_lon', 'perimeter_km', 'rank_difference', 'rank_difference_abs', 'method_agreement', 'combined_priority', 'method_consensus_score', 'better_ranking_method', 'consensus_risk_level', 'data_completeness', 'last_updated', 'dataset_version'], 'dtypes': {'WardName': dtype('O'), 'X.1': dtype('int64'), 'X': dtype('int64'), 'StateCode': dtype('O'), 'WardCode': dtype('O'), 'LGACode': dtype('int64'), 'Urban': dtype('O'), 'Source': dtype('O'), 'Timestamp': dtype('O'), 'GlobalID': dtype('O'), 'AMAPCODE': dtype('O'), 'mean_EVI': dtype('float64'), 'mean_NDVI': dtype('float64'), 'mean_rainfall': dtype('float64'), 'distance_to_water': dtype('float64'), 'RH_mean': dtype('float64'), 'temp_mean': dtype('float64'), 'housing_quality': dtype('float64'), 'pfpr': dtype('float64'), 'avgRAD': dtype('float64'), 'flood': dtype('float64'), 'NDWI': dtype('float64'), 'NDMI': dtype('float64'), 'elevation': dtype('float64'), 'mean_soil_wetness': dtype('float64'), 'settlement_type': dtype('float64'), 'u5_tpr_rdt': dtype('float64'), 'totalArea': dtype('float64'), 'urbanArea': dtype('float64'), 'urbanPercentage': dtype('float64'), 'building_height': dtype('float64'), 'geometry': <geopandas.array.GeometryDtype object at 0x7f8c6daf00d0>, 'detected_zone': dtype('O'), 'zone_detection_method': dtype('O'), 'zone_climate': dtype('O'), 'zone_priority_focus': CategoricalDtype(categories=['population and settlement factors'], ordered=False, categories_dtype=object), 'zone_states': dtype('O'), 'composite_score': dtype('float64'), 'composite_rank': dtype('int64'), 'composite_category': CategoricalDtype(categories=['High Risk', 'Low Risk', 'Medium Risk'], ordered=False, categories_dtype=object), 'overall_rank': dtype('int64'), 'vulnerability_category': CategoricalDtype(categories=['High Risk', 'Low Risk', 'Medium Risk'], ordered=False, categories_dtype=object), 'pca_score': dtype('float64'), 'pca_rank': dtype('int64'), 'pca_category': CategoricalDtype(categories=['High Risk', 'Low Risk', 'Medium Risk'], ordered=False, categories_dtype=object), 'pca_coverage': dtype('float64'), 'model_1': dtype('float64'), 'model_2': dtype('float64'), 'model_3': dtype('float64'), 'model_4': dtype('float64'), 'model_5': dtype('float64'), 'model_6': dtype('float64'), 'model_7': dtype('float64'), 'model_8': dtype('float64'), 'model_9': dtype('float64'), 'model_10': dtype('float64'), 'model_11': dtype('float64'), 'model_12': dtype('float64'), 'model_13': dtype('float64'), 'model_14': dtype('float64'), 'model_15': dtype('float64'), 'model_16': dtype('float64'), 'model_mean_score': dtype('float64'), 'model_std_score': dtype('float64'), 'model_agreement': dtype('float64'), 'model_consensus': dtype('bool'), 'area_km2': dtype('float64'), 'centroid_lat': dtype('float64'), 'centroid_lon': dtype('float64'), 'perimeter_km': dtype('float64'), 'rank_difference': dtype('int64'), 'rank_difference_abs': dtype('int64'), 'method_agreement': CategoricalDtype(categories=['High Agreement', 'Low Agreement', 'Moderate Agreement'], ordered=False, categories_dtype=object), 'combined_priority': CategoricalDtype(categories=['High Priority', 'Low Priority', 'Medium Priority'], ordered=False, categories_dtype=object), 'method_consensus_score': dtype('float64'), 'better_ranking_method': dtype('O'), 'consensus_risk_level': dtype('O'), 'data_completeness': dtype('float64'), 'last_updated': dtype('O'), 'dataset_version': dtype('O')}, 'analysis_columns': ['composite_score', 'composite_rank', 'pca_score', 'pca_rank']}
[2025-07-20 20:46:44,227] INFO in analysis_state_handler: State transition complete. Unified dataset ready: (484, 80)
[2025-07-20 20:46:44,227] INFO in complete_analysis_tools: State handler notified: {'status': 'success', 'message': 'Analysis complete and data ready for exploration', 'unified_shape': (484, 80), 'available_tools': ['execute_sql_query', 'execute_python_code', 'create_vulnerability_map', 'create_box_plot', 'create_decision_tree', 'create_urban_extent_map', 'generate_report']}
[2025-07-20 20:46:44,228] DEBUG in request_interpreter: Tool run_complete_analysis completed
[2025-07-20 20:46:44,228] DEBUG in analysis_routes: Sending streaming chunk: {"content": "Analysis complete! I've ranked all 484 wards by malaria risk.\n\n**Here's what I did:**\n1. **Cleaned your data** - Fixed ward name mismatches and filled missing values using neighboring areas\n2. **Selected 7 risk factors** - Based on North West's malaria patterns\n3. **Normalized everything** - Put all variables on the same 0-1 scale for fair comparison\n4. **Calculated risk scores using two methods:**\n   \u2022 **Composite Score**: Simple average of all risk factors (transparent and easy to understand)\n   \u2022 **PCA Score**: Statistical method that finds hidden patterns in your data\n5. **Ranked all wards** - From highest to lowest risk for intervention planning\n\nWhat would you like to do next?\n\u2022 **Plan ITN/bed net distribution** - Allocate nets optimally based on these rankings\n\u2022 View highest risk wards that need urgent intervention\n\u2022 View lowest risk wards  \n\u2022 Create risk maps (vulnerability maps for either composite or PCA method)\n\u2022 Compare methods (composite vs PCA)\n\u2022 Export results\n\n**To start ITN planning**, just say \"I want to plan bed net distribution\" or \"Help me distribute ITNs\".", "status": "success", "visualizations": [], "tools_used": ["run_complete_analysis"], "done": false}
127.0.0.1 - - [20/Jul/2025 20:46:44] "POST /send_message_streaming HTTP/1.1" 200 -
[2025-07-20 20:46:48,292] INFO in events: Logged LLM interaction: standard in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:48,293] DEBUG in analysis_routes: Sending streaming chunk: {"content": "The analysis ranked 484 wards by malaria risk using both composite and PCA scores. The composite score, a straightforward average of seven key risk factors, provides a transparent view of overall risk, while the PCA score identifies wards that align with dominant risk patterns. This dual approach ensures a comprehensive assessment.\n\nKey findings indicate that wards with high scores in both methods face severe malaria threats due to factors like high prevalence, poor housing, and conducive environmental conditions. Comparing these scores within the dataset helps identify wards that consistently rank high, signaling urgent need for intervention.\n\nFor immediate action, prioritize ITN distribution in the top-ranked wards, focusing on those with high composite and PCA scores. This targeted approach will address multiple risk factors simultaneously, reducing transmission effectively. Would you like to proceed with ITN distribution planning or explore other options?", "status": "success", "done": true}
[2025-07-20 20:46:48,319] INFO in core: Logged assistant message for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:50,923] DEBUG in development: Request: POST http://localhost:5015/send_message_streaming
[2025-07-20 20:46:50,924] INFO in decorators: send_message_streaming executed in 0.00 seconds
[2025-07-20 20:46:50,947] INFO in analysis_routes: Processing streaming message: 'plot me the vulnerability map for the composite score method...'
[2025-07-20 20:46:50,947] INFO in analysis_routes: Using real streaming system with proper line break preservation
[2025-07-20 20:46:50,948] INFO in request_interpreter: 🎯 Permission flag found! User message: 'plot me the vulnerability map for the composite score method'
[2025-07-20 20:46:52,082] INFO in events: Logged LLM interaction: streaming_function_calling in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:52,082] DEBUG in request_interpreter: Tool call detected: create_vulnerability_map with args: {"session_id":"current","method":"composite"}
[2025-07-20 20:46:52,082] DEBUG in request_interpreter: Executing tool: create_vulnerability_map with args: {'session_id': '6e90b139-5d30-40fd-91ad-4af66fec5f00', 'method': 'composite'}
[2025-07-20 20:46:52,082] INFO in __init__: Attempting to load unified dataset for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:52,102] INFO in unified_dataset_builder: ✅ Loaded CSV (no geometry needed): (484, 79) - 580.3KB
[2025-07-20 20:46:52,102] INFO in __init__: ✅ Successfully loaded unified dataset: 484 rows, 79 columns
[2025-07-20 20:46:52,203] INFO in composite_visualizations: 🗺️ Creating agent vulnerability map...
[2025-07-20 20:46:52,203] INFO in core_utils: 📊 Preparing unified dataset: (484, 79)
[2025-07-20 20:46:52,204] ERROR in core_utils: Error ensuring WGS84 CRS: The CRS attribute of a GeoDataFrame without an active geometry column is not defined. Use GeoDataFrame.set_geometry to set the active geometry column.
[2025-07-20 20:46:52,205] ERROR in core_utils: Error preparing unified dataset: You are calling a geospatial method on the GeoDataFrame, but the active geometry column to use has not been set. 
There are no existing columns with geometry data type. You can add a geometry column as the active geometry column with df.set_geometry. 
[2025-07-20 20:46:52,205] DEBUG in request_interpreter: Tool create_vulnerability_map completed
[2025-07-20 20:46:52,205] DEBUG in analysis_routes: Sending streaming chunk: {"content": "Error creating vulnerability map: Dataset preparation failed: You are calling a geospatial method on the GeoDataFrame, but the active geometry column to use has not been set. \nThere are no existing columns with geometry data type. You can add a geometry column as the active geometry column with df.set_geometry. ", "status": "success", "tools_used": ["create_vulnerability_map"], "done": false}
127.0.0.1 - - [20/Jul/2025 20:46:52] "POST /send_message_streaming HTTP/1.1" 200 -
[2025-07-20 20:46:56,132] INFO in events: Logged LLM interaction: standard in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:46:56,132] DEBUG in analysis_routes: Sending streaming chunk: {"content": "The error indicates that the dataset lacks a properly defined geometry column, which is essential for creating a geospatial vulnerability map. This means we cannot visualize the spatial distribution of malaria risk across wards using the composite score method at this moment.\n\nIn the context of malaria, the composite score method identifies areas with multiple overlapping risk factors. High composite scores suggest wards with significant malaria transmission potential due to factors like high prevalence, poor housing, and environmental conditions.\n\nTo address this, we should ensure the dataset includes accurate geographic information, such as ward boundaries, to enable mapping. As an immediate action, prioritize data verification and enhancement to include geospatial data, enabling effective visualization and targeted intervention planning. This will help in identifying high-risk areas for focused malaria control efforts, such as ITN distribution and environmental management.", "status": "success", "done": true}
[2025-07-20 20:46:56,154] INFO in core: Logged assistant message for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:47:36,978] DEBUG in development: Request: POST http://localhost:5015/send_message_streaming
[2025-07-20 20:47:36,979] INFO in decorators: send_message_streaming executed in 0.00 seconds
[2025-07-20 20:47:36,998] INFO in analysis_routes: Processing streaming message: 'I want to plan bed net distribution...'
[2025-07-20 20:47:36,998] INFO in analysis_routes: Using real streaming system with proper line break preservation
[2025-07-20 20:47:36,998] INFO in request_interpreter: 🎯 Permission flag found! User message: 'I want to plan bed net distribution'
[2025-07-20 20:47:38,620] DEBUG in analysis_routes: Sending streaming chunk: {"content": "To assist with planning the distribution of bed nets (ITNs), I need to know the total number of nets available and the average household size in the area. Additionally", "status": "success", "done": false}
127.0.0.1 - - [20/Jul/2025 20:47:38] "POST /send_message_streaming HTTP/1.1" 200 -
[2025-07-20 20:47:38,893] DEBUG in analysis_routes: Sending streaming chunk: {"content": ", if you have any specific urban-rural prioritization preferences, please let me know.\n\n", "status": "success", "done": false}
[2025-07-20 20:47:38,972] DEBUG in analysis_routes: Sending streaming chunk: {"content": "Can you provide these details?", "status": "success", "done": false}
[2025-07-20 20:47:38,993] INFO in events: Logged LLM interaction: streaming_conversational in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:47:38,994] DEBUG in analysis_routes: Sending streaming chunk: {"content": "", "status": "success", "done": true}
[2025-07-20 20:47:39,020] INFO in core: Logged assistant message for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:48:02,939] DEBUG in development: Request: POST http://localhost:5015/send_message_streaming
[2025-07-20 20:48:02,939] INFO in decorators: send_message_streaming executed in 0.00 seconds
[2025-07-20 20:48:02,961] INFO in analysis_routes: Processing streaming message: 'I have 90000 nets, and average household size is 4...'
[2025-07-20 20:48:02,961] INFO in analysis_routes: Using real streaming system with proper line break preservation
[2025-07-20 20:48:02,961] INFO in request_interpreter: 🎯 Permission flag found! User message: 'I have 90000 nets, and average household size is 4'
[2025-07-20 20:48:04,108] INFO in events: Logged LLM interaction: streaming_function_calling in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:48:04,108] DEBUG in request_interpreter: Tool call detected: run_itn_planning with args: {"session_id":"session_id","total_nets":90000,"avg_household_size":4}
[2025-07-20 20:48:04,109] DEBUG in request_interpreter: Executing tool: run_itn_planning with args: {'session_id': '6e90b139-5d30-40fd-91ad-4af66fec5f00', 'total_nets': 90000, 'avg_household_size': 4}
[2025-07-20 20:48:04,109] INFO in request_interpreter: Overrode analysis_complete to True based on unified dataset rankings for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:48:04,861] INFO in itn_pipeline: Found 38 duplicate ward entries across LGAs in population data
[2025-07-20 20:48:04,862] INFO in itn_pipeline: Duplicate ward names: ['Dawaki', 'Falgore', 'Goron Dutse', 'Gurjiya', 'Gwarmai', 'Kadawa', 'Kanwa', 'Karfi', 'Maraku', 'Sabon Gari']
[2025-07-20 20:48:04,862] INFO in itn_pipeline: Loaded population data for 484 ward-LGA combinations in Kano
[2025-07-20 20:48:04,862] INFO in itn_pipeline:   Unique wards: 446, Duplicate entries: 38
[2025-07-20 20:48:04,866] INFO in itn_pipeline: Using unified dataset for ITN planning
[2025-07-20 20:48:04,878] INFO in itn_pipeline: Ward names needing coordinate matching: 17
[2025-07-20 20:48:04,892] INFO in itn_pipeline: Matching strategy: 446 unique wards (simple match), 38 duplicate wards (coordinate match)
[2025-07-20 20:48:04,901] INFO in itn_pipeline: Fuzzy matched: 'Jauben Kudu' -> 'jaube'
[2025-07-20 20:48:04,901] INFO in itn_pipeline: Fuzzy matched: 'Rigar Duka' -> 'rugar duka'
[2025-07-20 20:48:04,902] INFO in itn_pipeline: Simple matching: 446/446 unique wards matched
[2025-07-20 20:48:04,970] INFO in itn_pipeline: Coordinate matching: 38/38 duplicate wards matched
[2025-07-20 20:48:04,972] INFO in itn_pipeline:   Dawaki (KN0903) -> Dawaki (Dawakin Kudu) (0.45 km)
[2025-07-20 20:48:04,972] INFO in itn_pipeline:   Dawaki (KN3201) -> Dawaki (Rano) (0.40 km)
[2025-07-20 20:48:04,973] INFO in itn_pipeline:   Falgore (KN1104) -> Falgore (Doguwa) (12.12 km)
[2025-07-20 20:48:04,978] INFO in itn_pipeline: Total matched: 484/484 (100.0%)
[2025-07-20 20:48:04,981] INFO in itn_pipeline: Matched population data for 484 out of 484 wards
[2025-07-20 20:48:05,058] INFO in itn_pipeline: Creating ITN map with 484 wards
[2025-07-20 20:48:05,059] INFO in itn_pipeline: Nets allocated range: 0.0 to 20628.0
[2025-07-20 20:48:05,059] INFO in itn_pipeline: Map center: lat=11.573981234000058, lon=8.517741215500026
[2025-07-20 20:48:05,062] INFO in itn_pipeline: Converting datetime column 'Timestamp' to string for JSON serialization
[2025-07-20 20:48:05,884] INFO in itn_pipeline: Saved ITN distribution results to instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/itn_distribution_results.json
[2025-07-20 20:48:05,885] DEBUG in request_interpreter: Tool run_itn_planning completed
[2025-07-20 20:48:05,886] DEBUG in analysis_routes: Sending streaming chunk: {"content": "ITN Distribution Plan:\nTotal Nets: 90000\nAllocated: 90000\nCoverage: 0.9%\nPrioritized Wards: 409\n\n<iframe src='/itn_embed/6e90b139-5d30-40fd-91ad-4af66fec5f00' width='100%' height='600' frameborder='0'></iframe>", "status": "success", "visualizations": [{"type": "itn_map", "path": "/static/visualizations/itn_map_6e90b139-5d30-40fd-91ad-4af66fec5f00.html", "url": "/itn_embed/6e90b139-5d30-40fd-91ad-4af66fec5f00"}], "tools_used": ["run_itn_planning"], "done": false}
127.0.0.1 - - [20/Jul/2025 20:48:05] "POST /send_message_streaming HTTP/1.1" 200 -
[2025-07-20 20:48:10,438] INFO in events: Logged LLM interaction: standard in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:48:10,438] DEBUG in analysis_routes: Sending streaming chunk: {"content": "The ITN distribution plan indicates that with 90,000 nets available, the coverage across the target area is only 0.9%, which is significantly low given the need for comprehensive malaria prevention. This low coverage suggests that the available nets are insufficient to meet the demand, as 409 wards have been prioritized for distribution. In the context of malaria control, achieving higher coverage is crucial to interrupt transmission cycles, especially in high-risk areas.\n\nGiven the limited coverage, it is essential to focus on the highest-risk wards identified by the composite and PCA scores. An immediate action would be to secure additional resources or nets to increase coverage, ensuring that the most vulnerable populations, particularly in wards with high malaria prevalence and poor housing conditions, receive adequate protection. Additionally, targeted community education on proper net usage can enhance the effectiveness of the distributed ITNs.", "status": "success", "done": true}
[2025-07-20 20:48:10,471] INFO in core: Logged assistant message for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:48:30,763] DEBUG in development: Request: GET http://localhost:5015/itn_embed/6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:48:30,765] INFO in itn_routes: Serving ITN map from: /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/static/visualizations/itn_map_6e90b139-5d30-40fd-91ad-4af66fec5f00.html
127.0.0.1 - - [20/Jul/2025 20:48:30] "GET /itn_embed/6e90b139-5d30-40fd-91ad-4af66fec5f00 HTTP/1.1" 200 -
[2025-07-20 20:49:09,288] DEBUG in development: Request: POST http://localhost:5015/send_message_streaming
[2025-07-20 20:49:09,289] INFO in decorators: send_message_streaming executed in 0.00 seconds
[2025-07-20 20:49:09,314] INFO in analysis_routes: Processing streaming message: 'Export ITN distribution results...'
[2025-07-20 20:49:09,314] INFO in analysis_routes: Using real streaming system with proper line break preservation
[2025-07-20 20:49:09,315] INFO in request_interpreter: 🎯 Permission flag found! User message: 'Export ITN distribution results'
[2025-07-20 20:49:10,286] DEBUG in analysis_routes: Sending streaming chunk: {"content": "To provide you with the ITN (Insecticide-Treated Net) distribution results, I'll first need to check if the ITN planning has been conducted based on the completed analysis. Let", "status": "success", "done": false}
127.0.0.1 - - [20/Jul/2025 20:49:10] "POST /send_message_streaming HTTP/1.1" 200 -
[2025-07-20 20:49:10,830] DEBUG in analysis_routes: Sending streaming chunk: {"content": " me retrieve and prepare the ITN distribution data for export.", "status": "success", "done": false}
[2025-07-20 20:49:10,863] INFO in events: Logged LLM interaction: streaming_function_calling in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:49:10,863] DEBUG in request_interpreter: Tool call detected: run_itn_planning with args: {"session_id":"current"}
[2025-07-20 20:49:10,863] DEBUG in request_interpreter: Executing tool: run_itn_planning with args: {'session_id': '6e90b139-5d30-40fd-91ad-4af66fec5f00'}
[2025-07-20 20:49:10,863] INFO in request_interpreter: Overrode analysis_complete to True based on unified dataset rankings for session 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:49:10,863] DEBUG in request_interpreter: Tool run_itn_planning completed
[2025-07-20 20:49:10,864] DEBUG in analysis_routes: Sending streaming chunk: {"content": "I'm ready to help you plan ITN distribution! To create an optimal allocation plan, I need to know:\n\n1. **How many bed nets do you have available?** (e.g., 50000, 100000)\n2. **What's the average household size in your area?** (default is 5 people)\n\nFor example, you can say: 'I have 100000 nets and average household size is 6'", "status": "info", "visualizations": [], "tools_used": ["run_itn_planning"], "done": false}
[2025-07-20 20:49:13,146] INFO in events: Logged LLM interaction: standard in session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
[2025-07-20 20:49:13,146] DEBUG in analysis_routes: Sending streaming chunk: {"content": "To effectively plan ITN distribution, we need to know the total number of bed nets available and the average household size in your area. This information allows us to allocate nets based on the specific needs of high-risk wards identified in the dataset.\n\nIn the context of malaria control, ensuring adequate ITN coverage is crucial, especially in wards with high malaria prevalence and poor housing conditions. For instance, if you have 100,000 nets and an average household size of 6, we can prioritize distribution to wards with the highest composite scores, indicating multiple risk factors like high malaria prevalence and poor housing.\n\nAction: Prioritize ITN distribution to wards with high composite scores, focusing on those with the highest malaria prevalence and poorest housing conditions to maximize impact and reduce transmission.", "status": "success", "done": true}
[2025-07-20 20:49:13,174] INFO in core: Logged assistant message for session: 6e90b139-5d30-40fd-91ad-4af66fec5f00
