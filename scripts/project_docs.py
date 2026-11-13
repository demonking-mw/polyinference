"""Check repository documentation coverage and render the offline feature tree.

Run from any directory: python /path/to/scripts/project_docs.py [--check].
Uses only Python's standard library and Git; no runtime/provider services.
"""

from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import subprocess
from collections import deque
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TREE = "docs/file-tree.json"
OUTPUT = "docs/file-tree.html"
ENTRYPOINT = "README.md"
EXTERNAL = (
    "references/claude-code",
    "references/deepagents",
    "references/mini-swe-agent",
)
CODE = {
    ".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".css",
    ".sh", ".ps1", ".c", ".h", ".cpp", ".rs", ".go",
}


class DocumentationError(ValueError):
    """An actionable navigation, inventory or document-contract failure."""


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.anchors.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.anchors.add(attrs["name"])
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.links.append(attrs[attr])


def without_code(source, *, keep_inline=False):
    """Omit fenced/inline examples, retaining headings and prose links."""
    lines, fence = [], None
    for line in source.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            value = marker[1]
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line if keep_inline else re.sub(r"(`+).*?\1", "", line))
    return "\n".join(lines)


def markdown_links(source):
    source = without_code(source)
    # Balance parentheses so links to names such as graph(1).html work too.
    links = []
    for match in re.finditer(r"(?<!\\)\[(?:[^\[\]\n]|\n(?![ \t]*\n))*\]\(", source):
        start = match.end()
        depth = 1
        end = start
        while end < len(source) and depth:
            char = source[end]
            if char == "\\":
                end += 2
                continue
            depth += (char == "(") - (char == ")")
            end += 1
        if depth == 0:
            target = source[start:end - 1].strip()
            if target.startswith("<"):
                target = target[1:target.index(">")]
            else:
                target = re.split(r'\s+[\'\"]', target, maxsplit=1)[0]
            links.append(target)
    definitions = dict(re.findall(r"^\s*\[([^\]]+)\]:\s*<?([^\s>]+)>?", source, re.M))
    for match in re.finditer(r"\[([^\]]+)\]\[([^\]]*)\]", source):
        label = (match[2] or match[1]).casefold()
        links.extend(value for key, value in definitions.items() if key.casefold() == label)
    parser = HTMLLinks()
    parser.feed(source)
    return links + parser.links


def anchors(source):
    source = without_code(source, keep_inline=True)
    parser = HTMLLinks()
    parser.feed(source)
    found = set(parser.anchors)
    counts = {}
    for heading in re.findall(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?$", source, re.M):
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        heading = re.sub(r"<[^>]*>", "", html.unescape(heading)).replace("`", "")
        found.add(heading)  # Obsidian uses the heading text rather than a GitHub slug.
        slug = re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug + (f"-{count}" if count else ""))
    return found


def external(path):
    return any(path == prefix or path.startswith(prefix + "/") for prefix in EXTERNAL)


def repository_files(root):
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, check=True, stdout=subprocess.PIPE,
    )
    files = set(result.stdout.decode("utf-8").split("\0")) - {""}
    return {
        path for path in files
        if not external(path) and not path.endswith(":Zone.Identifier")
        and (root / path).is_file()
    }


def safe_path(value):
    if not isinstance(value, str) or not value:
        raise DocumentationError("Expected a nonempty repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value or str(path) != value:
        raise DocumentationError(f"Unsafe/noncanonical path: {value}")
    return value


def validate_tree(data, root, inventory):
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise DocumentationError("Unsupported file-tree schema_version")
    if data.get("entrypoint") != ENTRYPOINT:
        raise DocumentationError(f"file-tree entrypoint must be {ENTRYPOINT}")
    if data.get("external_sources") != list(EXTERNAL):
        raise DocumentationError("External boundaries must match the documented reference checkouts")
    ids, owners, children_by_doc = set(), {}, {}

    def visit(node, *, is_root=False):
        if not isinstance(node, dict):
            raise DocumentationError("Every tree node must be an object")
        identity = node.get("id")
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z0-9-]+", identity) or identity in ids:
            raise DocumentationError(f"Missing/invalid/duplicate node id: {identity}")
        ids.add(identity)
        if not isinstance(node.get("title"), str) or not node["title"].strip():
            raise DocumentationError(f"Missing title: {identity}")
        required = {"id", "title", "doc", "files"}
        if not required <= node.keys() or node.keys() - required - {"children"}:
            raise DocumentationError(f"Every node needs exactly one doc and a files list: {identity}")
        doc = safe_path(node["doc"])
        if is_root and doc != ENTRYPOINT:
            raise DocumentationError(f"Tree root doc must be {ENTRYPOINT}")
        if not doc.endswith(".md") or not (root / doc).is_file():
            raise DocumentationError(f"Primary doc must be an existing Markdown file: {doc}")
        if not isinstance(node["files"], list):
            raise DocumentationError(f"files must be a list: {identity}")
        doc_links = {
            resolve_link(doc, target)[0]
            for target in markdown_links((root / doc).read_text(encoding="utf-8"))
        }
        for path in [doc, *node["files"]]:
            path = safe_path(path)
            if path.endswith(".md") and path != doc:
                raise DocumentationError(f"Additional docs need their own primary-doc node: {path}")
            if path in owners:
                raise DocumentationError(f"Duplicate ownership: {path} ({owners[path]}, {identity})")
            if external(path) or (path != OUTPUT and not (root / path).is_file()):
                raise DocumentationError(f"Missing/non-project file: {path}")
            owners[path] = identity
            if Path(path).suffix in CODE and path not in doc_links:
                raise DocumentationError(f"Primary doc {doc} must link and explain code module {path}")
        children = node.get("children", [])
        if not isinstance(children, list) or ("children" in node and not children):
            raise DocumentationError(f"Branch needs a nonempty children list: {identity}")
        children_by_doc[doc] = {visit(child) for child in children}
        return doc

    visit(data.get("root"), is_root=True)
    missing = sorted(inventory - owners.keys())
    extra = sorted(owners.keys() - inventory)
    if missing or extra:
        raise DocumentationError(f"Inventory mismatch; uncovered={missing}; outside inventory={extra}")
    return children_by_doc


def resolve_link(origin, target):
    parsed = urlsplit(html.unescape(target))
    if parsed.scheme or parsed.netloc:
        return None, ""
    path = unquote(parsed.path)
    if not path:
        return origin, unquote(parsed.fragment)
    if path.startswith("/"):
        raise DocumentationError(f"Use repository-relative links in {origin}: {target}")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(origin), path))
    if resolved == ".." or resolved.startswith("../"):
        raise DocumentationError(f"Link leaves repository in {origin}: {target}")
    return resolved, unquote(parsed.fragment)


def validate_links(root, inventory, generated, children_by_doc):
    sources = {path: (root / path).read_text(encoding="utf-8") for path in inventory if path.endswith(".md")}
    # UI routes and the unrendered template have different URL bases. Only maintained
    # documentation HTML is interpreted as repository-relative output here.
    sources.update({path: (root / path).read_text(encoding="utf-8") for path in inventory
                    if path.endswith(".html") and path.startswith(("docs/", "design-docs/", "development-docs/"))
                    and path != "docs/tree-template.html" and path not in generated})
    sources.update(generated)
    document_anchors = {path: anchors(source) for path, source in sources.items() if path.endswith(".md")}
    for path, source in sources.items():
        if path.endswith(".html"):
            parser = HTMLLinks()
            parser.feed(source)
            document_anchors[path] = parser.anchors
    graph = {}
    errors = []
    for origin, source in sources.items():
        if origin.endswith(".md"):
            if re.search(r"(?<!\\)\[\[[^\]\n]+\]\]", without_code(source)):
                errors.append(f"{origin}: use relative Markdown note links instead of wikilinks")
            links = markdown_links(source)
        else:
            parser = HTMLLinks()
            parser.feed(source)
            links = parser.links
        graph[origin] = set()
        for target in links:
            try:
                path, fragment = resolve_link(origin, target)
                if path is None:
                    continue
                if not (root / path).exists() and path not in generated and not external(path):
                    errors.append(f"{origin}: missing {target}")
                    continue
                if origin.endswith(".md") and path.endswith(".md") and path not in children_by_doc:
                    errors.append(f"{origin}: note link is outside the maintained tree: {target}")
                graph[origin].add(path)
                if fragment and path in document_anchors and fragment not in document_anchors[path]:
                    errors.append(f"{origin}: missing anchor {target}")
            except (DocumentationError, ValueError) as error:
                errors.append(f"{origin}: {error}")
    notes = children_by_doc.keys()
    for note, expected in children_by_doc.items():
        actual = (graph[note] & notes) - {note}
        if actual != expected:
            errors.append(
                f"{note}: note links must match file-tree children; "
                f"missing={sorted(expected - actual)}; extra={sorted(actual - expected)}"
            )
    reached, queue = set(), deque([ENTRYPOINT])
    while queue:
        path = queue.popleft()
        if path not in reached:
            reached.add(path)
            queue.extend(graph.get(path, ()))
    unreachable = sorted(inventory - reached)
    if unreachable:
        errors.append(f"Files unreachable from README.md: {unreachable}")
    if errors:
        raise DocumentationError("\n".join(errors))


def render_tree(node):
    title = html.escape(node["title"])
    doc = node["doc"]
    def href(path):
        return quote(posixpath.relpath(path, "docs"), safe="/")
    files = "".join(f'<li><a href="{href(path)}">{html.escape(path)}</a></li>' for path in node["files"])
    attached = f'<details class="files"><summary>{len(node["files"])} related files</summary><ul>{files}</ul></details>' if files else ""
    search = html.escape(" ".join([node["title"], doc, *node["files"]]), quote=True)
    feature = (
        f'<li class="feature" id="{node["id"]}" data-search="{search}"><article>'
        f'<a class="primary-doc" href="{href(doc)}">{title}</a><p class="path">{html.escape(doc)}</p>'
        f'{attached}</article></li>'
    )
    if "children" not in node:
        return feature
    children = "\n".join(render_tree(child) for child in node["children"])
    opened = " open" if doc == ENTRYPOINT else ""
    return f'<li class="branch"><details{opened}><summary>{title}</summary><ul>{feature}{children}</ul></details></li>'


def render(root, data, raw, note_count, file_count):
    template = (root / "docs/tree-template.html").read_text(encoding="utf-8")
    replacements = {
        "{{TREE}}": render_tree(data["root"]),
        "{{DATA}}": raw.replace("<", "\\u003c"),
        "{{FEATURE_COUNT}}": str(note_count),
        "{{FILE_COUNT}}": str(file_count),
    }
    for token, value in replacements.items():
        if token not in template:
            raise DocumentationError(f"Template is missing {token}")
        template = template.replace(token, value)
    return template


def run(root=ROOT, check=False):
    raw = (root / TREE).read_text(encoding="utf-8")
    data = json.loads(raw)
    inventory = repository_files(root)
    # The generated file is part of the inventory even on the first build.
    inventory.add(OUTPUT)
    children_by_doc = validate_tree(data, root, inventory)
    output = render(root, data, raw, len(children_by_doc), len(inventory))
    validate_links(root, inventory, {OUTPUT: output}, children_by_doc)
    target = root / OUTPUT
    if check:
        if not target.exists() or target.read_text(encoding="utf-8") != output:
            raise DocumentationError("Stale docs/file-tree.html; run python scripts/project_docs.py")
    else:
        target.write_text(output, encoding="utf-8", newline="\n")
    message = (
        f"Documentation OK: {len(inventory)} files, {len(children_by_doc)} notes; "
        f"{len(children_by_doc) - 1} Obsidian tree links and README reachability verified."
    )
    long_guides = sorted(p for p in inventory if p.endswith(".md")
                         and p.startswith(("docs/modules/", "docs/guides/"))
                         and len((root / p).read_text(encoding="utf-8").splitlines()) > 80)
    if long_guides:
        message += "\nGuide length advisory (>80 lines): " + ", ".join(long_guides)
    return message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without writing; fail on stale HTML")
    args = parser.parse_args()
    try:
        print(run(check=args.check))
    except (DocumentationError, OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Documentation check failed:\n{error}\n")


if __name__ == "__main__":
    main()
