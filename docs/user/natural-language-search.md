# Natural Language Search

PartsHub's natural language (NL) search feature allows you to search for components using everyday language instead of complex filters and query syntax. Simply describe what you're looking for, and the system will understand your intent and find matching components.

## Overview

Natural language search uses pattern-based parsing to understand your queries and convert them into structured search parameters. You can search using phrases like "find resistors with low stock" or "capacitors in location A1" without needing to learn specific syntax or navigate through filter menus.

### Key Benefits

- **Intuitive**: Use natural phrases instead of learning complex query syntax
- **Fast**: Get results quickly without clicking through multiple filter options
- **Flexible**: Combine multiple search criteria in a single query
- **Transparent**: See how your query was understood with confidence scoring
- **History**: Access your recent searches for quick re-use

## Getting Started

### Accessing Natural Language Search

1. Navigate to the **Components** page
2. Click the **Natural Language** button in the search mode toggle
3. Type your query in the search box
4. Press Enter or click the search button

### Your First Search

Try these simple examples to get started:

| Query | What it finds |
|-------|---------------|
| `resistors` | All resistor components |
| `low stock capacitors` | Capacitors with low inventory levels |
| `components in A1` | All parts stored in location A1 |
| `10k resistors` | Resistors with 10kΩ resistance value |
| `cheap LEDs` | LEDs under $5 |

## Query Patterns

The natural language parser recognizes several types of queries. You can use one or combine multiple patterns in a single search.

### 1. Component Type Queries

Search for specific types of electronic components.

**Supported component types:**

| Component | Recognized terms |
|-----------|-----------------|
| Resistors | `resistors`, `resistor`, `res`, `r` |
| Capacitors | `capacitors`, `capacitor`, `caps`, `cap`, `c` |
| Inductors | `inductors`, `inductor`, `ind`, `l` |
| ICs/Chips | `ics`, `ic`, `integrated circuits`, `chips` |
| Microcontrollers | `microcontrollers`, `mcu`, `mcus`, `micros` |
| Diodes | `diodes`, `diode`, `d` |
| Transistors | `transistors`, `transistor`, `trans`, `q` |
| LEDs | `leds`, `led`, `light emitting diodes` |
| Connectors | `connectors`, `connector`, `conn` |
| Crystals | `crystals`, `crystal`, `xtals`, `oscillators` |
| Switches | `switches`, `switch`, `sw` |
| Sensors | `sensors`, `sensor` |
| Voltage Regulators | `voltage regulators`, `regulators`, `vreg` |

**Examples:**
```
resistors
find capacitors
show me all transistors
list microcontrollers
```

### 2. Stock Status Filters

Filter components based on inventory levels.

**Supported stock statuses:**

| Status | Recognized phrases |
|--------|-------------------|
| Low stock | `low stock`, `running low`, `almost out`, `nearly out`, `few left` |
| Out of stock | `out of stock`, `no stock`, `empty`, `none`, `depleted` |
| Available | `available`, `in stock`, `have`, `got`, `stocked` |
| Unused | `unused`, `never used`, `brand new`, `new` |
| Needs reorder | `need reorder`, `need to order`, `should order`, `reorder` |

**Examples:**
```
low stock components
out of stock resistors
available capacitors
unused transistors
parts that need reorder
```

### 3. Location Filters

Search for components in specific storage locations.

**Supported location formats:**

| Format | Example | Description |
|--------|---------|-------------|
| Simple code | `A1`, `B5`, `C12` | Single letter + number |
| Named location | `Bin-23`, `Shelf-A` | Category + identifier |
| With preposition | `in A1`, `at Bin-23` | Natural phrase format |

**Examples:**
```
components in A1
parts at Bin-23
capacitors stored in Shelf-A
location B5
from Drawer-2
```

### 4. Value Filters

Search by component specifications like resistance, capacitance, voltage, etc.

#### Resistance Values

**Formats:** `10k`, `10kΩ`, `100R`, `100 ohm`, `4.7k`, `1M`

**Examples:**
```
10k resistors
100 ohm resistors
4.7kΩ components
1M resistors
```

#### Capacitance Values

**Formats:** `100μF`, `100uF`, `10nF`, `1pF`, `47 microfarad`

**Examples:**
```
100μF capacitors
10nF caps
capacitors under 1uF
47pF capacitors
```

#### Voltage Values

**Formats:** `5V`, `3.3V`, `12V`, `5 volt`

**Examples:**
```
5V regulators
3.3V components
12 volt parts
```

#### Other Values

- **Inductance:** `10μH`, `100nH`, `1mH`
- **Current:** `1A`, `500mA`, `100μA`
- **Frequency:** `16MHz`, `32kHz`, `1GHz`

### 5. Package/Footprint Filters

Search for components with specific packages or footprints.

**Supported package types:**

| Category | Examples |
|----------|----------|
| SMD Imperial | `0201`, `0402`, `0603`, `0805`, `1206`, `1210`, `1812`, `2010`, `2512` |
| SMD Metric | `0603M`, `1005M` |
| DIP Packages | `DIP8`, `DIP-14`, `DIP16` |
| Surface Mount | `SOT-23`, `SOT-223`, `SOIC8`, `SSOP16`, `TQFP32`, `QFN48` |
| Through-hole | `TO-220`, `TO-92`, `TO-3` |
| Generic | `SMD`, `SMT`, `through-hole`, `THT` |

**Examples:**
```
0805 resistors
1206 capacitors
DIP8 ICs
SOT-23 transistors
SMD components
through-hole parts
```

### 6. Manufacturer Filters

Search for components from specific manufacturers.

**Supported manufacturers:**

- **Texas Instruments** - `TI`, `Texas Instruments`
- **Infineon** - `Infineon`
- **NXP** - `NXP`
- **STMicroelectronics** - `ST`, `STMicroelectronics`
- **Analog Devices** - `ADI`, `Analog Devices`
- **Microchip** - `Microchip`
- **Vishay** - `Vishay`
- **Murata** - `Murata`
- **TDK** - `TDK`
- **KEMET** - `KEMET`
- **Samsung** - `Samsung`
- **Panasonic** - `Panasonic`

And many more...

**Examples:**
```
TI microcontrollers
Texas Instruments ICs
Infineon transistors
Murata capacitors
```

### 7. Price Filters

Search for components within specific price ranges.

**Supported price patterns:**

| Pattern | Example | Description |
|---------|---------|-------------|
| Under/below | `under $5`, `below $10`, `less than $20` | Maximum price |
| Over/above | `over $5`, `above $10`, `more than $20` | Minimum price |
| Cheap keywords | `cheap`, `inexpensive`, `affordable`, `budget` | Under $5 (default) |
| Exact | `$5`, `exactly $10` | Specific price |
| Range | `$1 to $5`, `between $1 and $5` | Price range |

**Examples:**
```
cheap resistors
components under $1
parts less than $5
ICs over $10
capacitors between $0.50 and $2
affordable microcontrollers
```

### 8. Multi-Entity Queries

Combine multiple search criteria in a single query for precise results.

**Examples:**
```
10k SMD resistors with low stock
0805 capacitors in location A1
TI microcontrollers under $10
available 5V regulators
unused 100μF capacitors in Bin-23
cheap 0603 resistors
Texas Instruments ICs under $5
low stock 1206 components
SMD resistors in storage A1 under $1
available DIP8 ICs from Texas Instruments
out of stock 0805 capacitors
10k resistors in A1 under $0.50
```

## Understanding Results

### Confidence Scoring

Every natural language search includes a confidence score that shows how well the system understood your query.

| Confidence Level | Score | Meaning |
|-----------------|-------|---------|
| High | 80-100% | Query well understood, accurate filtering applied |
| Medium | 50-79% | Query partially understood, may need refinement |
| Low | <50% | Using fallback full-text search, try rephrasing |

**What the scores mean:**

- **High confidence (80-100%)**: The parser recognized your intent and extracted specific search criteria. Results should be very accurate.

- **Medium confidence (50-79%)**: Some parts of your query were understood, but others may be ambiguous. Results are relevant but you might want to refine your query.

- **Low confidence (<50%)**: The query couldn't be parsed into specific filters. The system falls back to full-text search across all component fields.

### Parsed Filters Display

When you perform a natural language search, the system shows you exactly how it interpreted your query:

- **Confidence badge**: Shows the overall confidence level with color coding (green = high, yellow = medium, red = low)
- **Parsed filters**: Displays each recognized search criterion as a removable chip
- **Fallback warning**: Alerts you if the system switched to text search fallback

You can click the "×" on any parsed filter chip to remove that criterion (you'll need to search again after removing).

### Search History

Your recent natural language searches are automatically saved for quick re-use:

1. Click the **History** button next to the search box
2. Select a previous query to re-run it
3. Click **Clear History** to remove all saved searches

History is stored locally in your browser and limited to the last 10 queries.

## Search Tips and Best Practices

### Writing Effective Queries

**DO:**
- Use natural phrases: `resistors with low stock`
- Combine specific details: `10k SMD 0805 resistors`
- Be specific about what you want: `available 5V regulators in A1`
- Use abbreviations when known: `TI MCUs`, `0805 caps`
- Include units: `100uF`, `5V`, `16MHz`

**DON'T:**
- Use complex grammar: `Could you please find...` (just start with `find` or the component type)
- Ask questions: `What resistors do you have?` (use `resistors` or `show resistors`)
- Use very long sentences: Keep it concise
- Mix different component types: Search for one type at a time

### Getting Better Results

1. **Start broad, then narrow**: Begin with a simple query like `resistors`, then add filters: `10k resistors`, then `10k SMD resistors with low stock`

2. **Check the confidence score**: If confidence is low, try rephrasing your query with more specific terms

3. **Use recognized abbreviations**: The parser knows common abbreviations like `res` for resistors, `caps` for capacitors, `MCU` for microcontrollers

4. **Include units**: Always include units for values (`10k` not just `10`, `5V` not just `5`)

5. **Review parsed filters**: Check what filters were extracted to understand how your query was interpreted

6. **Try example queries**: Click on the example query chips to see how different patterns work

### Common Query Patterns

| What you want to find | Try this query |
|----------------------|----------------|
| Components running low | `low stock components` |
| Parts in a specific location | `components in A1` |
| Specific resistor value | `10k resistors` |
| SMD components by size | `0805 components` |
| Budget-friendly parts | `cheap resistors` or `under $1` |
| Manufacturer-specific | `TI microcontrollers` |
| Complex combination | `10k SMD 0805 resistors in A1 under $0.50` |
| Out of stock items | `out of stock capacitors` |
| New/unused parts | `unused components` |

## Troubleshooting

### No Results Found

If your search returns no results:

1. **Check your spelling**: Make sure component types and manufacturers are spelled correctly
2. **Simplify your query**: Remove some filters and try again
3. **Verify data exists**: Make sure you have components that match your criteria
4. **Try broader terms**: Use `resistors` instead of specific values first

### Low Confidence Score

If you're getting low confidence scores:

1. **Use recognized terms**: Stick to the component types and patterns listed in this guide
2. **Be more specific**: Instead of `parts`, use `resistors`, `capacitors`, etc.
3. **Include units**: Always add units for values (`10k` not `10`, `100uF` not `100`)
4. **Check examples**: Use the example query chips as templates

### Unexpected Results

If results don't match your expectations:

1. **Review parsed filters**: Check which filters were extracted from your query
2. **Rephrase your query**: Try alternative wording for ambiguous terms
3. **Use standard search**: Switch to standard search mode for more control
4. **Check confidence**: Low confidence may indicate misunderstanding

## Feature Limitations

Natural language search uses pattern-based parsing, which has some limitations:

### What Works Well

- Searching for specific component types
- Filtering by stock status, location, value, package, manufacturer, and price
- Combining 2-4 search criteria in one query
- Common abbreviations and units

### What Doesn't Work

- **Complex questions**: "What resistors do I have that would work for a 5V circuit?"
- **Calculations**: "Resistors that give me 2.5V from 5V"
- **Comparisons**: "Better than" or "equivalent to"
- **Vague terms**: "Good capacitors" or "high quality"
- **Multiple component types**: "Resistors and capacitors" (search separately)
- **Negations**: "Not in A1" (use standard filters instead)

### When to Use Standard Search

Consider switching to standard search mode when you need:

- More precise control over filter values
- Multiple component type selection
- Complex boolean logic (AND/OR/NOT)
- Exact parameter matching
- Provider SKU searches

## Frequently Asked Questions

### Q: How is this different from standard search?

A: Standard search requires you to type exact part numbers or use dropdown filters. Natural language search lets you describe what you want in plain English. Both search modes work well - use whichever feels more natural for your workflow.

### Q: Can I save natural language searches?

A: Yes! After running a search, click the **Save Search** button to save it with a custom name. Saved searches can be accessed from the **Saved Searches** dropdown.

### Q: Does it use AI or machine learning?

A: No, it uses pattern-based parsing with regular expressions. This means it's fast, predictable, and works offline without requiring external API calls. However, it only understands the specific patterns documented in this guide.

### Q: What happens if it doesn't understand my query?

A: If confidence is very low (<30%), the system automatically falls back to full-text search, which searches across all component fields for your query terms. You'll see a warning banner when this happens.

### Q: Can I search for multiple component types at once?

A: Not in a single natural language query. Each query should focus on one component type. For multiple types, use standard search or run separate queries.

### Q: Why do I see "Medium confidence"?

A: Medium confidence (50-79%) means the parser recognized some parts of your query but others may be ambiguous. Results should still be relevant, but you might want to make your query more specific for better accuracy.

### Q: Can I use wildcards or regex?

A: No, natural language search doesn't support wildcards or regular expressions. It focuses on natural phrases. For advanced pattern matching, use standard search mode.

### Q: Is my search history shared with other users?

A: No, search history is stored locally in your browser using localStorage. It's private to your browser session and not shared with other users or saved on the server.

## Examples Gallery

Here are 25+ real-world examples to inspire your searches:

### Basic Searches
```
resistors
capacitors
microcontrollers
transistors
LEDs
```

### Stock Management
```
low stock components
out of stock resistors
components running low
parts that need reorder
available capacitors
unused transistors
```

### Location-Based
```
components in A1
parts at Bin-23
capacitors stored in Shelf-A
transistors from Drawer-2
location B5 components
```

### Value-Based
```
10k resistors
100uF capacitors
5V regulators
3.3V components
16MHz crystals
4.7k resistors
47pF capacitors
```

### Package-Based
```
0805 resistors
1206 capacitors
DIP8 ICs
SOT-23 transistors
SMD components
through-hole resistors
```

### Manufacturer-Based
```
TI microcontrollers
Texas Instruments ICs
Infineon transistors
Murata capacitors
ST microcontrollers
```

### Price-Based
```
cheap resistors
components under $1
parts less than $5
affordable ICs
budget components
capacitors under $0.50
```

### Complex Combinations
```
10k SMD resistors with low stock
0805 capacitors in location A1
TI microcontrollers under $10
available 5V regulators
unused 100μF capacitors in Bin-23
cheap 0603 resistors
low stock 1206 components
SMD resistors in A1 under $1
out of stock 0805 capacitors
available DIP8 ICs from TI
16MHz crystals with low stock
affordable 3.3V regulators in stock
```

## Next Steps

- **Try it yourself**: Go to the Components page and toggle to Natural Language search
- **Explore examples**: Click the example query chips to see how different patterns work
- **Save favorites**: Save your most-used queries for quick access
- **Combine with filters**: Use manual filters alongside natural language for even more control

For more search options, see:
- [Saved Searches Guide](saved-searches.md) - Save and reuse frequent searches
- [Component Management](features.md#1-component-management) - Full feature overview
- [Getting Started Guide](getting-started.md) - Setup and basic usage

---

**Have feedback on natural language search?** We're always improving! Let us know what queries you wish worked or what features would be helpful.
