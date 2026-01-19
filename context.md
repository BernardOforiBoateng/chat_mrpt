
prompt theme 	prompt
Burden Stratification & Prioritization	Which wards in [Ward] have the highest malaria burden?
Burden Stratification & Prioritization	Rank all wards in [Wards] based on composite risk score.
Burden Stratification & Prioritization	What is the burden classification for [Ward Name]?
Burden Stratification & Prioritization	Which wards fall in the top decile of risk?
Burden Stratification & Prioritization	Are there any wards in [State] with that hint that the burden of Malaria is spatialy dependent ?
Burden Stratification & Prioritization	Which wards are high risk but not currently prioritized for ITN campaigns?
Burden Stratification & Prioritization	Show me high-burden wards that have low intervention coverage.
Urban Morphology & Settlement Type	What settlement types dominate [Ward]?
Urban Morphology & Settlement Type	Classify the wards in [City] by dominant settlement type.
Urban Morphology & Settlement Type	Which wards in [State] are predominantly informal?
Urban Morphology & Settlement Type	List all wards with high compactness and low nearest neighbor index.
Urban Morphology & Settlement Type	What is the morphology profile of [Ward]?

Urban Morphology & Settlement Type	Are industrial or non-residential zones contributing to high composite scores?
Urban Morphology & Settlement Type	Which wards are likely uninhabited based on morphology and building density?
specific information on variables 	What is the TPR among under-fives in [Ward Name]?
specific information on variables 	Map the TPR for all wards in [State].
specific information on variables 	Are there any wards with high TPR and high environmental risk?
specific information on variables 	What’s the relationship between TPR and composite risk in [ward]?
specific information on variables 	What is the mean TPR across wards classified as informal settlements?
specific information on variables 	Which wards had missing TPR values and were imputed using spatial mean?
Environmental & Spatial Drivers	Which wards in [State] are flood-prone?
Environmental & Spatial Drivers	Does proximity to water bodies correlate with higher malaria burden in [City]?
Environmental & Spatial Drivers	What is the elevation profile of [Ward]?
Environmental & Spatial Drivers	List wards with high vegetation density and compact buildings.
Environmental & Spatial Drivers	Are low-lying wards in [City] at higher malaria risk?
Environmental & Spatial Drivers	Which spatial factors contributed most to the composite score in [Ward]?
Spatial Intelligence & Mapping	Show me the reprioritization map for [State].
Spatial Intelligence & Mapping	Generate a morphology risk map for [Ward].
Spatial Intelligence & Mapping	Which wards near [Ward Name] share similar risk profiles?
Spatial Intelligence & Mapping	Display wards grouped by morphology class across [City].
Spatial Intelligence & Mapping	Can you overlay ITN coverage and composite score for [LGA]?
Spatial Intelligence & Mapping	Provide a ward-level malaria burden heatmap for [State].
Intervention Targeting	Which wards are most in need of ITNs in [City]?
Intervention Targeting	Identify wards eligible for IRS based on burden and settlement type.
Intervention Targeting	List wards where current intervention coverage is not proportional to risk.
Intervention Targeting	Which wards should be added to the next SMC round?
Intervention Targeting	Is [Ward] deprioritized? Should it be reconsidered based on current risk?
Intervention Targeting	Where can additional CHWs be deployed based on ward-level needs?
Model Inputs, Data Sources & Reliability	What data sources were used to compute the composite score?
Model Inputs, Data Sources & Reliability	How is the composite score calculated?
Model Inputs, Data Sources & Reliability	Was the TPR in [Ward] imputed or observed?
Model Inputs, Data Sources & Reliability	What covariates contributed most to the model in [City]?
Model Inputs, Data Sources & Reliability	Can you show the missingness pattern for TPR across [State]?
Scenario Simulation & What-If Analysis	If ITN coverage in [Ward] increases by 30%, how does the reprioritization change?
Scenario Simulation & What-If Analysis	What happens if we exclude elevation as a covariate?
Scenario Simulation & What-If Analysis	How would the risk classification change if TPR is assumed to be 20% in [Ward]?
Scenario Simulation & What-If Analysis	Simulate reprioritization with all wards above 50% compactness flagged as high-risk.
Scenario Simulation & What-If Analysis	What if informal settlements in [City] were classified separately in the model?
Strategy Development & Decision Support	Based on current risk, which wards should be targeted first in [State]?
Strategy Development & Decision Support	Which LGAs in [State] have the most high-risk wards?
Strategy Development & Decision Support	Propose a reprioritization strategy for [City] using model outputs.
Strategy Development & Decision Support	Which wards should receive additional monitoring or data collection?
Strategy Development & Decision Support	Highlight low-risk wards that might be safely deprioritized.


10th JuneSNQuestion1What is reprioritization 2distingusih between prioritization, deprioritization and reprioritization3what types of variables are available for use in the model4what is the relevance of the variables, what do they mean?5can you show me an example of how to approach reprioritization using example data6how is spatial mean calculated7In my city I have various settlements, does this model help in telling where to depriotitize?8explain how to use the vulnerability map? where do i start?9what would you recommend for high risk or low risk areas identified10can you show me how i can use this tool for microplanning11i have two cities that i want to reprioritize for, how can you help me figure out an approach12what relationships do you assume between the variables and the tpr13how is composite scoring different from pca, which one should i use14what if i want to weight one variable higher than the other, would you be able to help with that15why do we need to reprioritize16why should we care about reprioritization17does prior admistration of smc affect the output of the malaria risk scores in the wards24th June1Would this tool also help in identifying boundaries of wards earmarked for reprioritization2Can you do a quality check of the results 3Can you also compare the settlement classification with what I would see if I used the google earth engine application4When is it the best season  to deprioritize5Can you list the source of the variables being used in the composite scoring6Which variables are the most important to use in this State7How did you determine the variables to be used in State X8I want to select my own variables to be used in the composite scoring, how can I do that?9Concerning the box and whisker plots produced, how do I interpret it10Can you produce maps of where the reprioritized wards are?11Can you explain what the percentage thresholds in the different scenarios mean?12Can you explain what the urban coverage percentages are and why we are using them?13What should I do with these results?14Can I redo the reprioritization with different variables?15Would like to visualize only the wards with scores greater than 0.516Was housing quality  considered in the risk scores17Which variable are you pulling between EVI and NDVI18Can I use this tool to also prioritize larviciding activites for urban areas19How can I add more variables for consideration in the composite score analysis20What Machine learning approach is analogous to the the objective of this tool 21What variables were available to be used in the risk score that you did not end up using?22Can I include other variables not in the default list of variables based on my data needs 23I have a dataset with other variables apart from the sample csv, will the composite score still be computed24How does this tool compare to other malaria risk scoring tools?25Do I need internet connectivity to make my predictions26How do you define urban extent and urban percentage? 27Which is more appropriate to use for deprioritization between urban extent and urban percentage28how do you handle variables that have a nonlinear relationship with Test positivity rate 29What test positivity rate data are you using and what is the population covered?30What is the maximum number of variables that can  be used in the composite score 31How do you handle multicollinearity when using the composite score32What is the exact measure is the flood variable using 33For which months/year/days are the variables being extracted for 34Which variables require rasters or use of google earth engine35Do we need to download any software to use this tool?36What if  ITN coversge increases by [x] % in the top 5 wards?37Which ranking method works best for this data?38I have [X] amount of ITNs for [Y] state. Help me distribute them39is this tool available offline 40how was the settlement classification derived41are there any external tools that I can use to cross validate the the settlement type classification beside ground truth 42Could this tool be used to decide how to distribute other interventions, like if a malaria vaccine became widely available?43Was the data for each variable all collected during the same time period?44What other interventions campaigns is this work applicable to45Can we assume that values are missing completely at random in some variables and how does this tool handle it46How does this tool account for missing values, does it use computational measures? 47Can we also compute amount to be spent on ITN distribution in different reprioritization scenarios48Is this tool solely for use by malaria control programs49I would like to make a comparison between two wards based on the composite scores and which variables ranked higher in their computation50Does this tool consider missing values especially in the malaria positivity data?How does each variable influence malaria risk?What wards should be deprioritised based on their malaria risks?What are the steps to clean and summarise these datasets?Which variables matter most in this ward, that is not applicable to other wards?Why should this ward be prioritised over others?Can show me how to interprete each variable going into the risk scoring?How does the formula used for the risk scoring work?