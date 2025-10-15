---
description: Smart semantic search with natural language
argument-hint: <search_query>
model: claude-sonnet-4-20250514
---

## Search Query Analysis

**User's Original Query**: "$ARGUMENTS"

### Query Optimization

Claude, analyze the query above and improve it for code search:

1. **If vague** (e.g., "that parsing thing") → Make it specific (e.g., "language parser implementation")
2. **If a question** (e.g., "how does parsing work?") → Extract keywords (e.g., "parsing implementation process")
3. **If conversational** (e.g., "the stuff that handles languages") → Use technical terms (e.g., "language handler processor")
4. **If too broad** (e.g., "errors") → Add context (e.g., "error handling exception management")

**YourOptimizedQuery**: _{Claude: Write your improved query here, then use it below}_

---

### Semantic Search with Context

Execute this command with your optimized query:

```bash
codanna mcp semantic_search_with_context query:"{YourOptimizedQuery}" limit:5
```

### Alternative: Full-Text Search

If semantic search needs different keywords, try this (use your optimized query):

```bash
codanna retrieve search "{YourOptimizedQuery}" --limit 10
```

**Instructions for Claude**: 
1. First, write an optimized version of the user's query
2. Replace `{YourOptimizedQuery}` in both commands with your optimized query
3. Execute the semantic search command
4. If results are poor, try adjusting the query and searching again
5. **For follow-up questions**: If the user asks related questions or wants to explore further, repeat this entire workflow:
   - Analyze their new query using the same optimization process
   - Execute new searches with the optimized query
   - Use the search results to answer their question
   - Continue this cycle for as many iterations as needed
6. **For saving findings**: When the user says something like "save what we learned", "save report", "create a summary", or similar requests:
   - **IMMEDIATELY use the Write tool** to save to: `reports/find/find-{short-semantic-slug}.md`
   - Create a well-formatted markdown report using the template structure below
   - Include: Original query, key findings, relevant code locations, insights discovered  
   - Use clear headings, code snippets, and file references with line numbers
   - Make it a comprehensive reference document for future use
   - **DO NOT just display the report - actually save it to the file**

**Date**: 
!`date '+%B %d, %Y at %I:%M %p'`

---

## Report Template

**IMPORTANT**:Use this structure for all find command reports:

```markdown
# Find Report: {Descriptive Title}

**Generated**: {Date}  
**Original Query**: "{User's original search query}"  
**Optimized Query**: "{Your optimized query}"

## Summary

Brief overview of what was discovered and the main purpose of the search.

## Key Findings

### Primary Discoveries
- **Finding 1**: Description with file reference (`src/file.rs:123`)
- **Finding 2**: Description with file reference (`src/other.rs:456`)
- **Finding 3**: etc.

### Code Locations
| Component | File | Line | Purpose |
|-----------|------|------|---------|
| ComponentName | `src/path/file.rs` | 123 | Brief description |
| AnotherComponent | `src/other/file.rs` | 456 | Brief description |

## Notable Findings

### Interesting Patterns
- Pattern or architecture insight discovered
- Unexpected implementation detail
- Connection between different parts of the codebase

### Code Quality Observations  
- Well-designed aspects noticed
- Areas that could benefit from attention
- Performance considerations observed

## Claude's Assessment

### Honest Feedback
- How well does this code accomplish its purpose?
- What are the strengths of the current implementation?
- Any potential concerns or areas for improvement?

### Recommendations
- **For developers**: Actionable suggestions for working with this code
- **For architecture**: Higher-level structural recommendations  
- **For maintenance**: Things to keep in mind for future changes

## Search Journey

### Query Evolution
1. Original: "{original query}"
2. Optimized: "{optimized query}"
3. Follow-ups: (if any additional searches were performed)

### Search Results Quality
- Semantic search effectiveness: {High/Medium/Low}
- Full-text search needed: {Yes/No}
- Total relevant results found: {Number}

## Related Areas

### Connected Components
- List of related files/modules that weren't directly searched but are connected
- Suggestions for future exploration

### Follow-up Questions
- What questions remain unanswered?
- What would be good next steps for deeper understanding?

---

*This report was generated using the `/find` command workflow.*
*Claude version: [your model version]*
```

**IMPORTANT**:
Save report to: `@reports/find/find-{short-semantic-slug}.md`
