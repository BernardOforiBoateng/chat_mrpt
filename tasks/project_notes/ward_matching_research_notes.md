# Ward Name Matching Research and Solution Notes

## Date: 2025-08-04

### Problem Discovery Journey

Started with user reporting that PCA test results weren't showing in the analysis summary. Initial investigation revealed the summary was falling back to a simpler version due to NaN values in the unified dataset.

**Key Discovery**: 46 wards in Adamawa state were losing their WardCodes during TPR processing, causing merge failures and NaN values.

### Investigation Process

1. **Initial Confusion**: Thought WardCodes were duplicated (ADSDSA01 appearing 47 times seemed impossible)
2. **Clarification**: Realized 46 wards had NULL WardCodes, which pandas was treating as equal during merges
3. **Root Cause Found**: TPR data and Nigerian shapefile use different naming conventions for the same wards

### Research Findings

#### Industry Best Practices (2024)
- **Splink**: Python package for probabilistic record linkage, can link 1M records in ~1 minute
- **recordlinkage**: Comprehensive toolkit with Jaro-Winkler, Levenshtein, token matching
- **Blocking Strategy**: Segment data by geographic units (state/LGA) for efficiency
- **Multi-stage Pipelines**: Exact → Normalized → Phonetic → Fuzzy → ML-based

#### Nigerian Administrative Data Specifics
- 768 LGAs + 6 Area Councils = 774 total
- 36 states + 1 FCT
- Each LGA has 10-20 wards
- Data sources: OSGOF, Ehealth Africa, UNCS
- Ward boundaries verified with local leaders and INEC

#### LLM Applications (2024)
- GPT-4 and Claude leading in entity resolution tasks
- Zero-shot NER capabilities without fine-tuning
- Semantic understanding helps with unstructured/varied data
- AWS Bedrock showing 50% context reduction still works

### Pattern Analysis of Problem Wards

#### Categories of Mismatches:
1. **Slashes** (8 wards): `Futudou/Futuless` → `Futuless`
2. **Hyphens vs Spaces** (10+ wards): `Mayo-Ine` → `Mayo Inne`
3. **Roman vs Arabic** (2 wards): `Girei I` → `Girei 1`
4. **Apostrophes** (1 ward): `Ga'anda` → `Gaanda`
5. **Spelling Variations** (2 wards): `Gabun` → `Gabon`
6. **Duplicate Names** (4 wards): Same name in multiple LGAs

### Current Implementation Analysis

**Strengths**:
- Has basic fuzzy matching with difflib
- Attempts normalization (uppercase, remove common words)
- Recognizes the problem exists

**Weaknesses**:
- No LGA context during matching
- Threshold too high (70-80%)
- No handling of Nigerian-specific patterns
- Simple normalization insufficient
- No learning from successful matches

### Solution Design Decisions

#### Why Multi-Tiered Approach?
- Different name variations require different matching strategies
- Allows fast exact matches before expensive fuzzy matching
- Provides fallback options for difficult cases

#### Why Include LLMs?
- Can understand context humans would ("Futudou/Futuless" likely means "Futuless")
- Handles cases rules can't anticipate
- Only for <5% most difficult cases (cost control)

#### Why Knowledge Base?
- Nigerian ward names don't change often
- Can learn from successful matches
- Speeds up future processing
- Builds institutional knowledge

### Technical Insights

#### Blocking Strategy Importance:
- Without blocking: 226² = 51,076 comparisons
- With LGA blocking: ~226 * 10 = 2,260 comparisons (95% reduction)

#### Algorithm Selection:
- **Jaro-Winkler**: Best for typos, good for Nigerian names
- **Token Sort**: Best for multi-word ward names
- **Soundex/Metaphone**: Catches phonetic similarities
- **Levenshtein**: Good for edit distances but expensive

#### Performance Considerations:
- Jaro-Winkler is 10x faster than Damerau-Levenshtein
- Caching normalized names saves 30-40% processing time
- Parallel processing by LGA gives near-linear speedup

### Implementation Strategy Notes

#### Phase 1 (Immediate):
Focus on fixing the 46 known problem wards with rule-based transformations. This alone would solve the current user's issue.

#### Phase 2 (Enhancement):
Add recordlinkage library for more sophisticated matching. Build the knowledge base system.

#### Phase 3 (Advanced):
ML training on Nigerian data, LLM integration for edge cases.

### Lessons Learned

1. **Always consider data source differences** - TPR and shapefile come from different systems
2. **Context matters** - Ward names need LGA context for disambiguation
3. **Domain knowledge crucial** - Nigerian naming patterns are specific
4. **Start simple, enhance gradually** - Rule-based fixes can solve 80% of problems
5. **Build for learning** - System should improve over time

### Open Questions

1. Should we modify TPR data source or shapefile to be consistent?
2. How often do ward names/boundaries change in Nigeria?
3. What's the authoritative source - INEC, OSGOF, or Ehealth?
4. Should we implement fuzzy matching at data ingestion or analysis time?

### Next Steps

1. Implement Phase 1 solution (rule-based fixes)
2. Test on full Adamawa dataset
3. Validate no regressions on other states
4. Deploy to staging for user testing
5. Monitor match rates and gather feedback

### Risk Considerations

- **Over-matching**: Could incorrectly match different wards
- **Under-matching**: Could miss valid matches
- **Performance**: More sophisticated matching = slower processing
- **Maintenance**: Knowledge base needs updates as ward names change

### Success Criteria

- All 46 problem wards correctly matched
- No false positives introduced
- Processing time < 5 seconds
- User sees PCA test results as requested
- System learns from corrections