"""Navigation regressions: preserve findability as source/docs evolve."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/project_docs.py"
spec = importlib.util.spec_from_file_location("project_docs", SCRIPT)
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


@pytest.fixture
def checkout(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "docs").mkdir()
    files = {
        "README.md": "# Project\n[Browse](docs/file-tree.html)\n",
        "docs/module.md": "# Module\n[module.py](../module.py) · [tree.js](tree.js)\n"
        "[Styles](tree.css) · [Template](tree-template.html) · [Tree](file-tree.html)\n",
        "module.py": "VALUE = 1\n",
        "docs/tree.css": "body {}\n",
        "docs/tree.js": "// enhancement\n",
        "docs/tree-template.html": '<!doctype html><html><head><title>Tree</title></head><body>'
        '{{FEATURE_COUNT}} / {{FILE_COUNT}}<ul>{{TREE}}</ul>'
        '<script id="project-tree-data" type="application/json">{{DATA}}</script></body></html>\n',
    }
    for path, text in files.items():
        (tmp_path / path).write_text(text, encoding="utf-8")
    data = {
        "schema_version": 1,
        "external_sources": list(docs.EXTERNAL),
        "root": {"id": "project", "title": "Project", "children": [
            {"id": "intro", "title": "Introduction", "doc": "README.md", "files": []},
            {"id": "module", "title": "Module", "doc": "docs/module.md", "files": [
                "module.py", "docs/tree.css", "docs/tree.js", "docs/tree-template.html",
                "docs/file-tree.json", "docs/file-tree.html",
            ]},
        ]},
    }
    (tmp_path / docs.TREE).write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def change_tree(root, update):
    path = root / docs.TREE
    data = json.loads(path.read_text())
    update(data)
    path.write_text(json.dumps(data))


def test_first_build_is_offline_findable_and_check_detects_staleness(checkout):
    docs.run(checkout)
    output = (checkout / docs.OUTPUT).read_text()
    assert 'href="module.md"' in output
    assert 'href="../module.py"' in output
    assert "fetch(" not in output
    assert docs.run(checkout, check=True).startswith("Documentation OK")
    (checkout / "docs/tree-template.html").write_text(
        (checkout / "docs/tree-template.html").read_text() + "<!-- edit -->\n"
    )
    with pytest.raises(docs.DocumentationError, match="Stale"):
        docs.run(checkout, check=True)
    assert (checkout / docs.OUTPUT).read_text() == output
    docs.run(checkout)
    docs.run(checkout, check=True)


def test_new_source_file_cannot_silently_escape_documentation(checkout):
    (checkout / "new_feature.py").write_text("VALUE = 2\n")
    with pytest.raises(docs.DocumentationError, match="uncovered=.*new_feature.py"):
        docs.run(checkout)


@pytest.mark.parametrize("data", [None, [], 1])
def test_non_object_tree_is_an_actionable_validation_error(checkout, data):
    (checkout / docs.TREE).write_text(json.dumps(data))
    with pytest.raises(docs.DocumentationError, match="schema_version"):
        docs.run(checkout)


@pytest.mark.parametrize("update,message", [
    (lambda d: d["root"]["children"][0]["files"].append("module.py"), "must link and explain"),
    (lambda d: d["root"]["children"][1]["files"].append("module.py"), "Duplicate ownership"),
    (lambda d: d["root"]["children"][1].update(doc=["docs/module.md"]), "path"),
    (lambda d: d["root"]["children"][1]["files"].append("README.md"), "Additional docs"),
    (lambda d: d["root"].update(doc="README.md"), "Branch needs"),
    (lambda d: d["root"]["children"][1].update(id="intro"), "duplicate node id"),
    (lambda d: d["root"]["children"][1]["files"].append("../secret.py"), "Unsafe"),
])
def test_ambiguous_or_unsafe_feature_ownership_fails(checkout, update, message):
    change_tree(checkout, update)
    with pytest.raises(docs.DocumentationError, match=message):
        docs.run(checkout)


def test_code_needs_an_explicit_link_in_its_primary_guide(checkout):
    (checkout / "docs/module.md").write_text("# Module\nDescribes something.\n")
    with pytest.raises(docs.DocumentationError, match="must link and explain code module"):
        docs.run(checkout)


@pytest.mark.parametrize("link,message", [
    ("[missing](missing.md)", "missing missing.md"),
    ("[anchor](module.md#no-such-heading)", "missing anchor"),
    ("[escape](../../outside.md)", "leaves repository"),
])
def test_broken_links_and_anchors_fail(checkout, link, message):
    with (checkout / "docs/module.md").open("a") as output:
        output.write("\n" + link + "\n")
    with pytest.raises(docs.DocumentationError, match=message):
        docs.run(checkout)


def test_disconnected_document_cycle_is_not_findable(checkout):
    (checkout / "README.md").write_text("# Project\n")
    with pytest.raises(docs.DocumentationError, match="unreachable from README"):
        docs.run(checkout)


def test_markdown_links_support_parentheses_references_and_ignore_examples():
    text = '''# A heading
[export](graph(1).html) [ref][guide]
[guide]: module.md
`[example](not-real.md)`
```markdown
[example](not-real-either.md)
```
<a href="module.md#anchor">anchor</a>
'''
    assert docs.markdown_links(text) == ["graph(1).html", "module.md", "module.md#anchor"]
    assert {"use-runtimeports", "use-runtimeports-1", "explicit"} <= docs.anchors(
        '## Use `RuntimePorts`\n## Use `RuntimePorts`\n<a id="explicit"></a>\n'
    )


def test_ignored_runtime_state_and_external_code_are_outside_inventory(checkout):
    (checkout / ".gitignore").write_text(".runtime/\n")
    (checkout / ".runtime").mkdir()
    (checkout / ".runtime/secret.txt").write_text("not source")
    upstream = checkout / docs.EXTERNAL[0]
    upstream.mkdir(parents=True)
    (upstream / "upstream.py").write_text("third party")
    inventory = docs.repository_files(checkout)
    assert ".gitignore" in inventory
    assert ".runtime/secret.txt" not in inventory
    assert str(upstream.relative_to(checkout) / "upstream.py") not in inventory


def test_embedded_tree_data_cannot_break_out_of_json_script(checkout):
    change_tree(checkout, lambda d: d["root"]["children"][1].update(title="</script><script>bad()</script>"))
    docs.run(checkout)
    output = (checkout / docs.OUTPUT).read_text()
    assert "<script>bad()" not in output
    embedded = output.split('type="application/json">')[1].split("</script>")[0]
    assert json.loads(embedded)["root"]["children"][1]["title"] == "</script><script>bad()</script>"
