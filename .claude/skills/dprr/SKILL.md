---
name: dprr
description: Query the Digital Prosopography of the Roman Republic (DPRR) database using natural language. Generates SPARQL queries, validates them, executes against the local RDF store, and synthesizes results into academic prose.
argument-hint: <question about Roman Republic>
---

# DPRR Query Skill

Answer the user's question about the Roman Republic by generating and executing SPARQL queries against the DPRR database.

## Workflow

Follow these steps in order:

1. **Load schema**: Call the `get_schema` MCP tool to retrieve the DPRR ontology (prefixes, ShEx schema, example queries). Study the schema and examples carefully before writing any SPARQL.

2. **Analyze the question**: Identify the intent (data query vs. general info), relevant ontology classes (Person, PostAssertion, Office, etc.), named entities, and decompose complex questions into sub-queries.

3. **Generate SPARQL**: Write a SPARQL SELECT query using ONLY classes and predicates from the schema. Follow the critical rules below.

4. **Validate**: Call the `validate_sparql` MCP tool with your query. If errors are returned, fix the query based on the error messages and re-validate. Retry up to 2 times.

5. **Execute**: Call the `execute_sparql` MCP tool to run the validated query.

6. **Synthesize**: Present the results as described in the synthesis rules below.

## Critical DPRR Rules

- **Namespace**: Always use `PREFIX vocab: <http://romanrepublic.ac.uk/rdf/entity/vocab/>` for DPRR properties.
- **Entity URIs**: Follow the pattern `<http://romanrepublic.ac.uk/rdf/entity/{Type}/{ID}>`. Known entities: `<.../Sex/Male>`, `<.../Sex/Female>`.
- **Assertion-based model**: Office-holding is on PostAssertion, NOT Person. To find who held an office, query PostAssertion with `vocab:isAboutPerson` and `vocab:hasOffice`. Same pattern for RelationshipAssertion, StatusAssertion, DateInformation, TribeAssertion.
- **Dates are integers**: Negative values = BC (e.g., -200 = 200 BC). Use integer comparison in FILTERs.
- **Always use DISTINCT** in SELECT queries.
- **Always use LIMIT 100** unless the user requests all results.
- **Include uncertainty**: When relevant, include `vocab:isUncertain` to flag uncertain assertions.

## Synthesis Rules

When presenting results:

1. **Cite sources**: Reference secondary sources when available (Broughton's MRR, Rupke's Fasti Sacerdotum, Zmeskal's Adfinitas).
2. **Flag uncertainty**: If any results have `isUncertain = true`, note this explicitly.
3. **Data completeness**: Note that DPRR covers 509-31 BC and draws from specific secondary sources. Not all known Romans are included.
4. **Roman naming conventions**: Use standard prosopographic notation (e.g., "L. Cornelius Scipio Africanus" not just "Scipio").
5. **Date formatting**: Present dates as "200 BC" not "-200".
6. **Results table**: Include a formatted table of key results before the prose summary.
7. **Keep it concise**: 2-4 paragraphs of prose after the table. Focus on what the data shows.

## Question: $ARGUMENTS
