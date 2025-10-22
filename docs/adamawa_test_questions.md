# Test Questions for Adamawa TPR Data
## For Manual Testing of Data Analysis V3 Agent

Based on the actual Adamawa TPR dataset with 10,452 records from health facilities across multiple LGAs.

---

## 🔍 Basic Data Exploration Questions

1. **"How many health facilities are in the dataset?"**

2. **"What are all the LGAs represented in Adamawa state?"**

3. **"Show me the first 10 facilities in Yola South"**

4. **"What time period does this data cover?"**

5. **"How many unique wards are in the dataset?"**

---

## 📊 Testing Volume Analysis

6. **"What's the total number of people tested by RDT across all facilities?"**

7. **"Show me the top 10 facilities by total testing volume"**

8. **"Which LGA has the highest number of tests performed?"**

9. **"Compare RDT vs Microscopy testing volumes across the state"**

10. **"What's the average number of tests per facility per month?"**

---

## 🎯 Positivity Rate Questions (Tests Encoding!)

11. **"Calculate the overall test positivity rate for children under 5 years"**
    - Tests access to "<5yrs" columns

12. **"What's the positivity rate for adults aged 5 years and above?"**
    - Tests access to "≥5yrs" columns with special character

13. **"Show me facilities with test positivity rate above 50% for pregnant women"**

14. **"Which ward has the highest malaria positivity rate?"**

15. **"Compare positivity rates between different age groups"**

---

## 📈 Temporal/Trend Analysis

16. **"Show me the monthly trend of malaria cases from January to June 2024"**

17. **"Which month had the highest number of positive cases?"**

18. **"Is there a seasonal pattern in malaria testing?"**

19. **"Calculate the month-over-month change in test volumes"**

20. **"Show me the trend of RDT positivity rates over time"**

---

## 🏥 Facility-Level Analysis

21. **"Compare testing patterns between Primary and Secondary facilities"**

22. **"Which primary health facilities have zero microscopy testing?"**

23. **"Show me facilities that only use RDT for testing"**

24. **"Identify facilities with incomplete data reporting"**

25. **"Rank facilities by their testing capacity"**

---

## 👥 Demographic Analysis (Heavy Encoding Test!)

26. **"What's the total number of pregnant women tested positive by RDT?"**

27. **"Compare malaria burden between children <5 years and adults ≥5 years"**
    - Critical test of encoding handling

28. **"What percentage of total tests are for pregnant women?"**

29. **"Show the age distribution of positive cases"**

30. **"Which demographic group has the highest positivity rate?"**

---

## 🗺️ Geographic Analysis

31. **"Which LGA has the highest malaria burden?"**

32. **"Compare malaria rates between Yola North and Yola South"**

33. **"Show me the top 5 wards with highest positive cases"**

34. **"Create a summary of testing by LGA"**

35. **"Which geographic areas have gaps in testing coverage?"**

---

## 🛡️ LLIN Distribution Questions

36. **"How many pregnant women received LLIN?"**

37. **"What's the total LLIN distributed to children under 5?"**

38. **"Which facilities have the highest LLIN distribution?"**

39. **"Calculate LLIN coverage rate for pregnant women who tested positive"**

40. **"Compare LLIN distribution between different LGAs"**

---

## 📊 Statistical Analysis

41. **"Calculate the mean, median, and standard deviation of monthly test volumes"**

42. **"What's the correlation between testing volume and positivity rate?"**

43. **"Identify outlier facilities with unusual testing patterns"**

44. **"Show me the distribution of test positivity rates across facilities"**

45. **"What's the 90th percentile for testing volume?"**

---

## 🎯 Complex Analytical Questions

46. **"Which facilities are high-volume but low-positivity?"**

47. **"Identify facilities that might be under-testing based on their catchment population"**

48. **"What factors correlate with high malaria positivity?"**

49. **"Create a risk score for each ward based on positivity and volume"**

50. **"Which areas should be prioritized for intervention based on the data?"**

---

## 🔴 Critical Encoding Test Questions
These specifically test the handling of special characters (≥, <):

51. **"Sum all tests for people ≥5 years across all facilities"**

52. **"Show me data for 'Persons presenting with fever & tested by RDT ≥5yrs (excl PW)'"**

53. **"Calculate total positive cases for children <5 years by microscopy"**

54. **"Compare RDT results between <5 years and ≥5 years age groups"**

55. **"What's the ratio of <5 years to ≥5 years in testing volumes?"**

---

## 📝 Reporting Questions

56. **"Generate a summary report of key malaria indicators for Adamawa"**

57. **"Create an executive summary of the malaria situation"**

58. **"What are the top 3 insights from this data?"**

59. **"Provide recommendations for malaria control based on the data"**

60. **"Summarize the data quality issues found in the dataset"**

---

## ⚠️ Expected Behavior When Testing

### ✅ GOOD Signs (Encoding Fix Working):
- Agent correctly accesses columns with ≥ and < symbols
- Returns actual facility names from the data (e.g., "Wuro-Hausa Primary Health Clinic")
- Provides specific numbers that can be verified
- No errors when accessing age-specific columns

### ❌ BAD Signs (Encoding Issues):
- Agent says "can't find column" or "column doesn't exist"
- Returns fake facility names like "Facility A, B, C"
- Provides made-up percentages like "82.3%" consistently
- Error messages mentioning "â‰¥" instead of "≥"
- Agent says it will "create example data" or use "hypothetical" values

---

## 💡 Testing Tips

1. **Start with simple questions** (1-5) to verify data is loaded
2. **Move to encoding test questions** (11-12, 26-28, 51-55) to check the fix
3. **Try complex queries** (46-50) to test full capability
4. **Watch for hallucinations** - the agent should use real data, not make up examples
5. **Check specific numbers** - you can verify responses against the actual CSV

---

## Sample Testing Session Flow

```
1. Upload adamawa_tpr_cleaned.csv
2. Wait for "Data successfully loaded" message
3. Start with: "How many health facilities are in the dataset?"
4. Then try: "Show me the top 10 facilities by total testing volume"
5. Test encoding: "Calculate positivity rate for adults ≥5 years"
6. If working well, try complex: "Compare malaria burden between age groups"
```