# Component Search

## Overview

PartsHub provides powerful search capabilities for finding electronic components in your inventory. The system supports both traditional parameter-based search and natural language queries, making it easy to find parts using plain English.

## Search Methods

### Standard Search

Traditional search with explicit filter parameters:
- Search by part number, manufacturer, or description
- Filter by category, storage location, component type
- Filter by stock status (low, out, available)
- Sort and paginate results

### Natural Language Search

New in the latest version, PartsHub understands natural language queries, allowing you to search using conversational phrases like:
- "find resistors with low stock"
- "show me capacitors in location A1"
- "10k SMD resistors under $5"
- "out of stock transistors"

The system automatically extracts search parameters from your query and applies appropriate filters.

---

## Natural Language Search

### Getting Started

Natural Language (NL) Search allows you to find components using everyday language instead of filling out multiple filter fields. Simply toggle to "Natural Language" mode and type your query in plain English.

#### Quick Example

Instead of selecting filters:
- Component Type: "resistor"
- Stock Status: "low"
- Storage Location: "A1"

You can simply type: **"resistors with low stock in A1"**

### How It Works

The Natural Language Search system uses pattern-based parsing to understand your query:

1. **Intent Classification**: Determines what you're trying to do (search by type, filter by stock, etc.)
2. **Entity Extraction**: Identifies specific values like component types, locations, prices, and stock levels
3. **Confidence Scoring**: Calculates how well the system understood your query
4. **Smart Fallback**: If confidence is low, automatically falls back to full-text search

#### Confidence Levels

The system displays a confidence score showing how well it understood your query:

- **High Confidence (80-100%)**: Query well understood with clear intent and entities
  - Visual indicator: Green badge and progress bar
  - Example: "find resistors with low stock in A1"

- **Medium Confidence (50-79%)**: Query partially understood, may have some ambiguity
  - Visual indicator: Orange badge and progress bar
  - Example: "capacitors maybe in the drawer somewhere"

- **Low Confidence (<50%)**: Query ambiguous, using full-text search fallback
  - Visual indicator: Red badge and progress bar
  - Falls back to FTS5 full-text search for better results
  - Example: "show me stuff" or "what do you have"

### Supported Query Patterns

#### 1. Search by Component Type

Find components by their type or category.

**Supported Component Types:**
- Resistors (resistor, res, r)
- Capacitors (capacitor, cap, c)
- Inductors (inductor, ind, l)
- Integrated Circuits (ic, chip)
- Microcontrollers (microcontroller, mcu)
- Diodes (diode, d)
- Transistors (transistor, trans, q)
- LEDs (led)
- Connectors (connector, conn)
- Crystals (crystal, xtal, oscillator)
- Switches (switch, sw)
- Relays (relay)
- Fuses (fuse)
- Sensors (sensor)
- Displays (display, lcd, oled)
- Modules (module, board)
- Batteries (battery)
- Voltage Regulators (regulator, vreg)
- Op-Amps (opamp, op-amp)

**Example Queries:**
```
find resistors
show me all capacitors
list transistors
get ICs
search for LEDs
display connectors
```

#### 2. Filter by Stock Status

Find components based on their inventory levels.

**Stock Status Keywords:**
- **Low stock**: "low stock", "running low", "almost out", "few left"
- **Out of stock**: "out of stock", "no stock", "empty", "depleted"
- **Available**: "available", "in stock", "have", "stocked"
- **Unused**: "unused", "never used", "brand new"
- **Need reorder**: "need reorder", "should order"

**Example Queries:**
```
components with low stock
out of stock parts
available resistors
unused capacitors
parts running low
items that need reorder
```

#### 3. Filter by Storage Location

Find components in specific storage locations.

**Location Formats:**
- Simple codes: A1, B2, C3
- Named locations: Bin-23, Shelf-A, Drawer-3
- With prepositions: "in A1", "at Shelf-2", "from Cabinet-1"

**Example Queries:**
```
components in A1
parts stored in Bin-23
what's in Shelf-A
items at Cabinet-1
resistors from Drawer-2
capacitors in location B5
```

#### 4. Filter by Component Values

Search for components with specific electrical values or specifications.

**Supported Values:**
- **Resistance**: 10kΩ, 100Ω, 4.7k, 1M
- **Capacitance**: 100μF, 10nF, 1pF, 100uF
- **Voltage**: 5V, 3.3V, 12V
- **Inductance**: 10μH, 100nH, 1mH
- **Current**: 1A, 500mA, 100μA
- **Frequency**: 16MHz, 32kHz, 1GHz

**Package/Footprint:**
- SMD imperial: 0603, 0805, 1206
- DIP packages: DIP8, DIP-14
- Surface mount: SOT-23, SOIC8, TQFP32
- Through-hole: TO-220, TO-92
- Generic: SMD, THT

**Example Queries:**
```
10k resistors
100μF capacitors
5V voltage regulators
16MHz crystals
0805 resistors
DIP8 ICs
SOT-23 transistors
SMD components
3.3V parts
```

#### 5. Filter by Price

Find components within your budget.

**Price Patterns:**
- **Under/Below**: "under $5", "less than $10", "below $20"
- **Over/Above**: "over $5", "more than $10", "above $20"
- **Exact**: "$5", "exactly $10"
- **Range**: "$1 to $5", "between $2 and $10"
- **Cheap keywords**: "cheap", "inexpensive", "affordable", "budget"

**Example Queries:**
```
components under $1
cheap capacitors
parts less than $5
inexpensive resistors
affordable ICs
budget components
parts over $10
between $1 and $5
```

#### 6. Filter by Time (Recently Added)

Find components added within a specific timeframe.

**Time Keywords:**
- "recently added"
- "added this week"
- "added last month"
- "new components"

**Example Queries:**
```
recently added components
parts added this week
items from last month
new resistors
```

### Multi-Entity Queries

Combine multiple filters in a single natural language query for powerful searches.

**Example Queries:**
```
10k SMD resistors with low stock
0805 capacitors in location A1 under $1
Texas Instruments ICs under $5
available 5V regulators
unused 100μF capacitors in Bin-23
cheap 0603 resistors with low stock
SMD resistors in storage A1
low stock 1206 components
DIP8 ICs from Texas Instruments
resistors between $0.10 and $1.00 in A1
```

**How Multi-Entity Queries Work:**
- The system extracts multiple entities from your query
- Each entity adds to the confidence score
- All extracted filters are combined with AND logic
- Visual feedback shows which filters were extracted

### Interactive Features

#### Example Query Chips

Click on pre-made example queries to try common search patterns:
- "resistors with low stock"
- "capacitors in location A1"
- "10k SMD resistors"
- "out of stock transistors"
- "capacitors under 1uF"

#### Parsed Filter Chips

After searching, you'll see color-coded chips showing extracted filters:
- **Purple**: Component type
- **Orange**: Stock status
- **Blue**: Storage location
- **Teal**: Category
- **Indigo**: Search term
- **Deep Purple**: Component value
- **Cyan**: Package/footprint

**Removing Filters:**
Click the × on any filter chip to remove it and automatically re-run the search with the remaining filters.

#### Search History

The system automatically saves your recent natural language queries:
- Access history via the "History" dropdown button
- Click any previous query to re-run it
- Last 10 queries are saved locally
- Clear history with "Clear History" option

### Best Practices

#### Writing Effective Queries

**DO:**
- Use specific component types: "resistors", "capacitors", "ICs"
- Include clear values: "10k", "100uF", "5V"
- Specify locations clearly: "in A1", "at Bin-23"
- Combine relevant filters: "10k resistors with low stock"

**DON'T:**
- Be too vague: "show me stuff", "things"
- Use complex sentences: "I'm looking for maybe some resistors if you have them"
- Mix unrelated concepts: "resistors and also what's the weather"

#### Query Examples by Use Case

**Inventory Management:**
```
low stock items
out of stock parts
components that need reorder
unused items
```

**Location Organization:**
```
what's in Bin-A1
all parts in Cabinet-2
components stored in Drawer-5
```

**Value-Based Searches:**
```
10k resistors
5V regulators
100μF capacitors
16MHz crystals
0805 SMD components
```

**Budget Planning:**
```
cheap resistors
components under $1
inexpensive capacitors
parts between $0.50 and $2
```

**Component Sourcing:**
```
Texas Instruments ICs
Murata capacitors
Vishay resistors
```

### Limitations and Edge Cases

#### Known Limitations

1. **Ambiguous Queries**: Very vague queries like "show me all the things" will have low confidence and fall back to text search

2. **Complex Logic**: The system doesn't support complex boolean logic like "resistors OR capacitors" - use separate queries instead

3. **Negation**: Queries like "not resistors" or "exclude capacitors" are not supported - use standard filters instead

4. **Ranges in Natural Language**: Saying "between 10k and 100k ohms" requires specific formatting - use "10k to 100k resistors" or standard filters

5. **Manufacturer Abbreviations**: Some manufacturer abbreviations may not be recognized - try the full name or use standard filters

#### Common Mistakes and Fixes

**Mistake:** "show me all resistors maybe in A1 or B2 I think"
**Fix:** "resistors in A1" (be specific, avoid uncertainty)

**Mistake:** "what components do we have"
**Fix:** Use the standard search or be more specific: "list all resistors"

**Mistake:** "10kohm resistors"
**Fix:** "10k resistors" or "10kΩ resistors" (use standard units)

**Mistake:** "cheap cheap cheap parts"
**Fix:** "cheap parts" or "components under $1" (avoid repetition)

### FTS5 Fallback Behavior

When the natural language parser has low confidence (<50%), the system automatically falls back to SQLite FTS5 (Full-Text Search):

**What Happens:**
- Your query is treated as a text search across all fields
- Searches component names, part numbers, manufacturers, descriptions
- No structured filtering is applied
- Results ranked by text relevance
- Orange warning banner appears: "Query couldn't be fully understood. Using text search fallback."

**When Fallback Occurs:**
- Very vague queries
- Complex or grammatically unusual queries
- Queries with no recognized entities
- Generic phrases like "show me" or "what do you have"

**Making Fallback Work:**
- Your query is still useful as a text search
- Try rephrasing with more specific terms
- Use component types, locations, or values
- Consider switching to standard search mode

### Unsupported Query Patterns

The following patterns are **not supported** and will likely result in low confidence or unexpected results:

**Boolean Operators:**
```
resistors OR capacitors
NOT transistors
resistors AND NOT used
```

**Comparisons:**
```
more than 100 units
greater than 10k ohm
less than minimum stock
```

**Relative Queries:**
```
recently used components
most expensive parts
highest quantity items
```

**Action Queries:**
```
order more resistors
delete old parts
move components to A1
```

**Conditional Queries:**
```
if stock is low then show
resistors when available
parts unless they're used
```

For these advanced queries, use the standard search filters or the API directly.

---

## API Reference

### Natural Language Query Parameter

The component list endpoint supports an optional `nl_query` parameter for natural language search.

#### Endpoint

```
GET /api/v1/components?nl_query={query}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nl_query` | string | No | Natural language query string |
| `limit` | integer | No | Number of results (1-100, default: 50) |
| `offset` | integer | No | Pagination offset (default: 0) |
| `sort_by` | string | No | Sort field (default: "updated_at") |
| `sort_order` | string | No | Sort order "asc" or "desc" (default: "desc") |

**Note:** Manual filter parameters (category, stock_status, etc.) can be combined with `nl_query`. Manual parameters always take priority over parsed parameters.

#### Response Structure

```json
{
  "components": [...],
  "total": 42,
  "page": 1,
  "total_pages": 3,
  "limit": 20,
  "nl_metadata": {
    "query": "resistors with low stock",
    "confidence": 0.85,
    "parsed_entities": {
      "component_type": "resistor",
      "stock_status": "low"
    },
    "fallback_to_fts5": false,
    "intent": "search_by_type"
  }
}
```

#### NL Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Original natural language query |
| `confidence` | float | Parsing confidence (0.0-1.0) |
| `parsed_entities` | object | Extracted filter parameters |
| `fallback_to_fts5` | boolean | Whether FTS5 fallback was used |
| `intent` | string | Classified query intent |
| `error` | string | Error message if parsing failed (optional) |

#### Parsed Entity Fields

The `parsed_entities` object can contain:

| Field | Type | Example Values |
|-------|------|----------------|
| `component_type` | string | "resistor", "capacitor", "ic" |
| `stock_status` | string | "low", "out", "available" |
| `location` | string | "A1", "Bin-23", "Shelf-A" |
| `package` | string | "0805", "DIP8", "SOT-23" |
| `manufacturer` | string | "Texas Instruments", "Murata" |
| `min_price` | float | 0.5, 1.0, 5.0 |
| `max_price` | float | 1.0, 5.0, 10.0 |
| `exact_price` | float | 0.99, 2.50 |
| `resistance` | string | "10kΩ", "100Ω" |
| `capacitance` | string | "100μF", "10nF" |
| `voltage` | string | "5V", "3.3V" |
| `search` | string | Free-text search term |

#### Example API Calls

**Simple Query:**
```bash
curl -X GET "http://localhost:8000/api/v1/components?nl_query=find%20resistors" \
  -H "accept: application/json"
```

**Multi-Entity Query:**
```bash
curl -X GET "http://localhost:8000/api/v1/components?nl_query=10k%20SMD%20resistors%20with%20low%20stock" \
  -H "accept: application/json"
```

**Query with Pagination:**
```bash
curl -X GET "http://localhost:8000/api/v1/components?nl_query=capacitors%20in%20A1&limit=20&offset=0" \
  -H "accept: application/json"
```

**Combining NL Query with Manual Filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/components?nl_query=low%20stock%20parts&category=passive&limit=50" \
  -H "accept: application/json"
```

#### Intent Types

The system classifies queries into these intent categories:

| Intent | Description | Example Queries |
|--------|-------------|-----------------|
| `search_by_type` | Finding components by type | "find resistors", "show capacitors" |
| `filter_by_stock` | Filtering by stock status | "low stock items", "out of stock" |
| `filter_by_location` | Filtering by location | "in A1", "at Shelf-2" |
| `filter_by_value` | Filtering by specifications | "10k resistors", "5V regulators" |
| `filter_by_price` | Filtering by price | "under $5", "cheap parts" |

#### Error Handling

**Invalid Query (Empty):**
```json
{
  "components": [],
  "total": 0,
  "nl_metadata": {
    "query": "",
    "confidence": 0.0,
    "fallback_to_fts5": true,
    "parsed_entities": {}
  }
}
```

**Low Confidence Query:**
```json
{
  "components": [...],
  "total": 15,
  "nl_metadata": {
    "query": "show me stuff",
    "confidence": 0.25,
    "fallback_to_fts5": true,
    "parsed_entities": {},
    "intent": "search_by_type"
  }
}
```

---

## Troubleshooting

### No Results Found

**Symptom:** Query returns zero results with high confidence

**Possible Causes:**
1. No components match the extracted filters
2. Typo in component type or location name
3. Overly restrictive multi-entity query

**Solutions:**
- Check parsed filter chips to see what was extracted
- Remove specific filters by clicking the × on chips
- Try a broader query (fewer filters)
- Verify location names and component types in your inventory

### Low Confidence Warning

**Symptom:** Orange "Using fallback text search" banner appears

**Possible Causes:**
1. Query is too vague or generic
2. Unrecognized entity names
3. Complex grammatical structure
4. No clear intent

**Solutions:**
- Be more specific with component types and values
- Use recognized keywords from the supported patterns
- Simplify your query structure
- Try example queries as templates
- Consider using standard search mode instead

### Unexpected Filters Extracted

**Symptom:** Parsed filter chips show filters you didn't intend

**Possible Causes:**
1. Ambiguous keywords (e.g., "C" could be capacitor or a location)
2. Multiple interpretations of values
3. Unintended abbreviations matched

**Solutions:**
- Review and remove incorrect filter chips
- Rephrase query with more specific terms
- Use longer, unambiguous component names
- Separate multi-word locations with hyphens

### Search History Not Saving

**Symptom:** History dropdown is empty or doesn't update

**Possible Causes:**
1. Browser localStorage disabled
2. Private/incognito browsing mode
3. Browser storage quota exceeded

**Solutions:**
- Check browser settings for localStorage
- Use normal browsing mode (not private)
- Clear browser storage and try again
- History is per-browser, not synced across devices

### Performance Issues

**Symptom:** Slow search results with natural language queries

**Possible Causes:**
1. Very large result set
2. Complex multi-entity query
3. Database performance

**Solutions:**
- Use pagination (limit parameter)
- Add more specific filters to narrow results
- Consider using standard search for broad queries
- Check database indexes and optimization

---

## Performance Characteristics

### Parsing Speed

- **Target:** <50ms for query parsing
- **Typical:** 10-30ms for simple queries
- **Maximum:** ~100ms for complex multi-entity queries

Parsing is done entirely in Python using regex patterns, with no external API calls or NLP libraries required.

### Search Speed

Natural language search performance is comparable to standard search:
- **Simple queries (1-2 entities):** 50-200ms
- **Complex queries (3+ entities):** 100-500ms
- **Large result sets (100+ matches):** May take longer due to database query time

Results are integrated with existing search infrastructure, including FTS5 full-text search for fallback scenarios.

### Scalability

The NL search system is designed to scale with your inventory:
- Pattern matching is O(n) where n = query length (very fast)
- Database queries use proper indexes
- Confidence scoring is lightweight
- No external API dependencies or rate limits

---

## Privacy and Security

### Data Handling

- **Query Privacy:** Natural language queries are processed entirely server-side
- **No External Calls:** No queries are sent to external NLP services or APIs
- **Logging:** Queries may be logged for debugging (check your backend logs)
- **History Storage:** Search history is stored locally in browser localStorage only

### Authentication

Natural language search respects the same authentication and authorization rules as standard search:
- Anonymous users can search (read-only access)
- Authenticated users can search with full access
- Admin-only operations remain restricted

### Rate Limiting

Natural language queries are subject to the same rate limiting as standard API calls. No special rate limits apply.

---

## Technical Architecture

For developers and advanced users, here's how the Natural Language Search system works under the hood:

### Components

1. **NLQueryParser** (`backend/src/services/nl_patterns.py`)
   - Pattern-based regex parsing
   - Entity extraction using 7 specialized extractors
   - Intent classification using 5 intent categories

2. **NaturalLanguageSearchService** (`backend/src/services/natural_language_search_service.py`)
   - Main service layer for NL queries
   - Confidence calculation and threshold management
   - Parameter mapping to ComponentService API
   - FTS5 fallback logic

3. **ComponentService** (`backend/src/services/component_service.py`)
   - Integration point in `list_components()` method
   - Merges NL-parsed parameters with manual filters
   - Returns results + metadata tuple

4. **API Endpoint** (`backend/src/api/components.py`)
   - Exposes `nl_query` query parameter
   - Returns `nl_metadata` in response
   - Manual parameters override parsed parameters

5. **Frontend Component** (`frontend/src/components/ComponentSearch.vue`)
   - Search mode toggle (Standard/NL)
   - Example query chips
   - Confidence visualization (badges, progress bars)
   - Parsed filter chips with removal
   - Search history management

### Pattern Grammar

The system uses comprehensive regex patterns for entity extraction:

- **Component Types:** 19 component categories with abbreviations
- **Stock Status:** 5 status types with natural variations
- **Locations:** 3 pattern types (codes, named, with prepositions)
- **Values:** 7 value types (R, C, L, V, I, F) with unit normalization
- **Packages:** 5 package categories (SMD, DIP, SMT, TO, etc.)
- **Manufacturers:** 20+ common manufacturers with abbreviations
- **Prices:** 4 price pattern types (under, over, exact, range)

### Confidence Calculation

Confidence score is calculated using:

1. **Base confidence** from intent classifier (0.0-1.0)
2. **Entity confidence** averaged across all extracted entities
3. **Multi-entity boost** (+0.1 per additional entity beyond first)
4. **Ambiguity penalty** (-0.15 for vague queries)
5. **Final clamping** to [0.0, 1.0] range

**Threshold:** 0.5 (50%) - Below this triggers FTS5 fallback

### Test Coverage

The Natural Language Search feature has extensive test coverage:

- **Pattern Grammar:** 69+ test cases covering all entity extractors
- **Parsing Service:** 23+ unit tests for confidence and fallback logic
- **Integration Tests:** API endpoint testing with real queries
- **Performance Tests:** Parsing speed and database query benchmarks

---

## Future Enhancements

Planned improvements for Natural Language Search:

- **Machine Learning:** Train custom models for better intent recognition
- **Query Suggestions:** Real-time autocomplete for NL queries
- **Voice Search:** Speech-to-text integration for hands-free searching
- **Query Analytics:** Track popular queries and improve patterns
- **Multilingual Support:** Support for languages beyond English
- **Advanced Logic:** Support for OR, NOT, and complex boolean queries
- **Fuzzy Matching:** Tolerant of typos and spelling variations
- **Context Awareness:** Remember user preferences and recent searches

---

## Related Documentation

- [Component Management Guide](../user/components.md)
- [Storage Location Guide](../user/storage-locations.md)
- [API Documentation](../api.md)
- [Bulk Operations](../user/bulk-operations.md)
- [Saved Searches](../user/saved-searches.md)

---

**Note:** Natural Language Search is an evolving feature. Query patterns and confidence algorithms may be refined in future releases based on user feedback and usage analytics.
