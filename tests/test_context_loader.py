from dprr_tool.context import load_prefixes, load_schemas, load_examples, render_schemas_as_shex, render_examples


def test_load_prefixes():
    prefixes = load_prefixes()
    assert isinstance(prefixes, dict)
    assert prefixes["vocab"] == "http://romanrepublic.ac.uk/rdf/entity/vocab/"
    assert "rdfs" in prefixes


def test_load_schemas():
    schemas = load_schemas()
    assert "Person" in schemas
    assert "PostAssertion" in schemas
    assert "uri" in schemas["Person"]
    assert len(schemas["Person"]["properties"]) > 5


def test_load_examples():
    examples = load_examples()
    assert isinstance(examples, list)
    assert len(examples) >= 15
    assert "question" in examples[0]
    assert "sparql" in examples[0]


def test_render_schemas_as_shex():
    schemas = load_schemas()
    text = render_schemas_as_shex(schemas)
    assert "vocab:Person" in text
    assert "vocab:hasDprrID" in text
    assert "vocab:PostAssertion" in text
    assert "vocab:hasOffice" in text
    assert "{" in text
    assert "}" in text


def test_render_examples():
    examples = load_examples()
    text = render_examples(examples)
    assert "PREFIX" in text
    assert "SELECT" in text
    assert examples[0]["question"] in text
