import re
from dataclasses import dataclass

from anthropic import Anthropic

from dprr_tool.context import load_prefixes, load_schemas
from dprr_tool.prompts import (
    EXTRACTION_TOOL_SCHEMA,
    build_extraction_prompt,
    build_generation_prompt,
    build_synthesis_prompt,
)
from dprr_tool.validate import (
    build_schema_dict,
    parse_and_fix_prefixes,
    validate_and_execute,
)


MAX_RETRIES = 3


@dataclass
class StructuredQuestion:
    intent: str
    extracted_classes: list[str]
    extracted_entities: list[str]
    question_steps: list[str]


@dataclass
class PipelineResult:
    question: str
    extraction: StructuredQuestion | None
    sparql: str | None
    rows: list[dict[str, str]]
    synthesis: str | None
    errors: list[str]


def extract_question(question: str, client: Anthropic) -> StructuredQuestion:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1024,
        temperature=0,
        system=build_extraction_prompt(),
        tools=[EXTRACTION_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "extract_question"},
        messages=[{"role": "user", "content": question}],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_question":
            data = block.input
            return StructuredQuestion(
                intent=data["intent"],
                extracted_classes=data["extracted_classes"],
                extracted_entities=data["extracted_entities"],
                question_steps=data["question_steps"],
            )
    raise RuntimeError("Claude did not return a tool_use response for extraction")


def generate_sparql(question: str, extraction: StructuredQuestion, client: Anthropic) -> str:
    prefix_map = load_prefixes()
    system_prompt = build_generation_prompt()
    extraction_context = (
        f"Extracted information:\n"
        f"- Intent: {extraction.intent}\n"
        f"- Classes: {', '.join(extraction.extracted_classes)}\n"
        f"- Entities: {', '.join(extraction.extracted_entities)}\n"
        f"- Steps: {'; '.join(extraction.question_steps)}"
    )
    messages = [{"role": "user", "content": f"{extraction_context}\n\nQuestion: {question}"}]

    last_errors = []
    for attempt in range(MAX_RETRIES):
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=messages,
        )
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        sparql = _extract_sparql_from_markdown(response_text)
        if not sparql:
            last_errors = ["No SPARQL code block found in the response."]
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "Please provide a SPARQL query inside a ```sparql code block."})
            continue

        fixed, errors = parse_and_fix_prefixes(sparql, prefix_map)
        if not errors:
            return fixed

        last_errors = errors
        messages.append({"role": "assistant", "content": response_text})
        messages.append({
            "role": "user",
            "content": "The generated query has errors:\n\n" + "\n".join(f"- {e}" for e in errors) + "\n\nPlease fix the query and try again.",
        })

    raise RuntimeError(f"Failed to generate valid SPARQL after {MAX_RETRIES} attempts. Last errors: {last_errors}")


def synthesize_response(question: str, sparql: str, rows: list[dict[str, str]], client: Anthropic) -> str:
    if rows:
        headers = list(rows[0].keys())
        table_lines = [" | ".join(headers), " | ".join("---" for _ in headers)]
        for row in rows[:50]:
            table_lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        results_table = "\n".join(table_lines)
    else:
        results_table = "(no results)"

    user_content = (
        f"## Original Question\n{question}\n\n"
        f"## SPARQL Query Executed\n```sparql\n{sparql}\n```\n\n"
        f"## Results ({len(rows)} rows)\n{results_table}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=8192,
        temperature=0,
        system=build_synthesis_prompt(),
        messages=[{"role": "user", "content": user_content}],
    )
    for block in response.content:
        if block.type == "text":
            return block.text
    return "(No synthesis generated)"


def run_pipeline(question: str, store, client: Anthropic) -> PipelineResult:
    errors = []

    # Step 1: Extract
    try:
        extraction = extract_question(question, client)
    except Exception as e:
        return PipelineResult(question=question, extraction=None, sparql=None, rows=[], synthesis=None, errors=[f"Extraction failed: {e}"])

    # Step 2: Generate (with syntax retry)
    try:
        sparql = generate_sparql(question, extraction, client)
    except RuntimeError as e:
        return PipelineResult(question=question, extraction=extraction, sparql=None, rows=[], synthesis=None, errors=[str(e)])

    # Step 3: Validate and execute
    prefix_map = load_prefixes()
    schema_dict = build_schema_dict(load_schemas(), prefix_map)
    validation = validate_and_execute(sparql, store, schema_dict, prefix_map)

    if not validation.success:
        sparql, validation = _retry_with_semantic_errors(question, extraction, sparql, validation, store, schema_dict, prefix_map, client)

    if not validation.success:
        return PipelineResult(question=question, extraction=extraction, sparql=validation.sparql, rows=[], synthesis=None, errors=validation.errors)

    # Step 4: Synthesize
    try:
        synthesis = synthesize_response(question, validation.sparql, validation.rows, client)
    except Exception as e:
        synthesis = None
        errors.append(f"Synthesis failed: {e}")

    return PipelineResult(question=question, extraction=extraction, sparql=validation.sparql, rows=validation.rows, synthesis=synthesis, errors=errors)


def _retry_with_semantic_errors(question, extraction, sparql, validation, store, schema_dict, prefix_map, client, max_retries=2):
    system_prompt = build_generation_prompt()
    extraction_context = (
        f"Extracted information:\n"
        f"- Intent: {extraction.intent}\n"
        f"- Classes: {', '.join(extraction.extracted_classes)}\n"
        f"- Entities: {', '.join(extraction.extracted_entities)}\n"
        f"- Steps: {'; '.join(extraction.question_steps)}"
    )
    messages = [
        {"role": "user", "content": f"{extraction_context}\n\nQuestion: {question}"},
        {"role": "assistant", "content": f"```sparql\n{sparql}\n```"},
    ]

    for _ in range(max_retries):
        error_text = "\n".join(f"- {e}" for e in validation.errors)
        messages.append({"role": "user", "content": f"The query has validation errors:\n\n{error_text}\n\nPlease fix the query."})

        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=messages,
        )
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        new_sparql = _extract_sparql_from_markdown(response_text)
        if not new_sparql:
            messages.append({"role": "assistant", "content": response_text})
            continue

        fixed, syntax_errors = parse_and_fix_prefixes(new_sparql, prefix_map)
        if syntax_errors:
            messages.append({"role": "assistant", "content": response_text})
            continue

        validation = validate_and_execute(fixed, store, schema_dict, prefix_map)
        if validation.success:
            return fixed, validation

        sparql = fixed
        messages.append({"role": "assistant", "content": response_text})

    return sparql, validation


def _extract_sparql_from_markdown(text: str) -> str | None:
    match = re.search(r"```sparql\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
