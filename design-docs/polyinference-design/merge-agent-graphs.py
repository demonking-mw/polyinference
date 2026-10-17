"""Merge the two supplied exports without changing the user's memory model.

Usage: python merge-agent-graphs.py USER.html AI.html
Outputs are written beside this script; neither input is overwritten.
"""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path


SEED = re.compile(r'(<script\b[^>]*id="graph-seed"[^>]*>)([\s\S]*?)(</script>)')


def read(path):
    source = Path(path).read_text(encoding="utf-8-sig")
    match = SEED.search(source)
    assert match, "Missing graph seed"
    return source, json.loads(match[2]), match[2]


def memory_json(seed):
    start = re.search(r'"memoryGraph"\s*:\s*', seed).end()
    _, end = json.JSONDecoder().raw_decode(seed[start:])
    return seed[start:start + end]


def main(user_path, ai_path):
    source, user, user_seed = read(user_path)
    _, ai, _ = read(ai_path)
    merged = copy.deepcopy(user)
    original = {n["id"]: n for n in user["nodes"]}
    memory_nodes = {n["id"]: n for n in user["memoryGraph"]["nodes"]}
    ai_nodes = {n["id"]: n for n in ai["nodes"]}
    canonical = {**{k: n["title"] for k, n in memory_nodes.items()},
                 **{k: n["title"] for k, n in original.items()}}
    aliases = {n["title"]: canonical[n["id"]] for n in ai["nodes"]
               if n["id"] in canonical and n["title"] != canonical[n["id"]]}
    aliases.update({"Local result processor": "Result Processor (OS / LOCAL PIPE)",
                    "Cloud result processor": "Result Processor (CLOUD PIPE)"})
    alias_pattern = re.compile("|".join(re.escape(x) for x in sorted(aliases, key=len, reverse=True)))

    def references(value):
        if isinstance(value, str):
            return alias_pattern.sub(lambda m: aliases[m[0]], value)
        if isinstance(value, list):
            return [references(x) for x in value]
        if isinstance(value, dict):
            return {k: references(v) for k, v in value.items()}
        return value

    # The 15 user architecture nodes retain identity, names, subtitles, kinds,
    # order, and coordinates. AI supplies the updated behavioral contracts.
    merged["nodes"] = []
    for node in user["nodes"]:
        update = references(copy.deepcopy(ai_nodes.get(node["id"], node)))
        for key in ("id", "title", "subtitle", "kind", "x", "y", "custom"):
            update[key] = node[key]
        merged["nodes"].append(update)

    # Insert new concepts in the gaps around the existing two-pipe design.
    # Names already present in the user's memory view take precedence too.
    additions = {
        "state_xsyangll": (-835, 207),
        "state_rqc9j1bh": (-525, -390),
        "state_hxca0deg": (-835, -12),
        "integration_gate": (-21, 520),
        "private_code_copy": (810, -108),
        "shell_mutex": (1036, 280),
        "verification_gate": (377, 520),
        "reconciliation_dev": (679, 650),
    }
    for node in ai["nodes"]:
        if node["id"] in original:
            continue
        update = references(copy.deepcopy(node))
        update["title"] = canonical.get(node["id"], node["title"])
        update["x"], update["y"] = additions[node["id"]]
        merged["nodes"].append(update)

    nodes = {n["id"]: n for n in merged["nodes"]}
    # Retain the original independent evidence gate as well as the AI's final
    # local assessment; a prose/model verdict never establishes host success.
    nodes["verdict"]["body"] += (
        " The host independently validates the required check records against the exact assessed tree. "
        "Unavailable, stale or missing required evidence cannot yield successful. Blocked, "
        "budget-exhausted and interrupted attempts retain their explicit stopping state; "
        "they are not silently converted into an assessed normal completion.")
    nodes["verdict"]["facts"] = [
        "Record command, availability/status, exit code, output artifact, and tested tree/revision for each check.",
        "The assigned model performs the final examination; the host enforces the acceptance criteria and evidence contract.",
        "A repair retains the assigned role and verification ownership, and requires final assessment again.",
    ]
    nodes["final"]["body"] += (
        " Run the independent integration/regression checks required by the project through Tools & observations. "
        "Complete only when both the senior decision and current host evidence support it. "
        "Failed checks return concrete evidence to ORCHESTRATOR / LOOP HANDLER for another review. "
        "Persist truthful blocked, budget_stopped, failed or cancelled outcomes with partial work and continuation references.")
    nodes["final"]["facts"] = copy.deepcopy(original["final"]["facts"])
    nodes["execute"]["facts"] = copy.deepcopy(original["execute"]["facts"])
    nodes["report"]["facts"] = [
        "Record task/attempt identity, original base B, captured predecessor H, tested tree, actual checkpoint SHA, evidence, usage and unresolved issues.",
        "A no-diff normal completion may use an empty metadata commit; never fabricate a SHA when Git fails or its outcome is uncertain.",
        "Tests remain bound to their exact tree. Changed content requires new checks, even if a model claims success.",
        "All normal assessed outcomes publish provisionally and remain unresolved until senior review.",
        "Crash, incomplete assessment or uncertain publication requires reconciliation before closure or ownership release.",
    ]
    nodes["state_xxdtqfse"]["body"] += (
        " The initial objective enters ORCHESTRATOR / LOOP HANDLER. Later steering is recorded in Immediate Memory "
        "and applied by the sprint planner after the captured running local tasks finish.")
    nodes["state_xxdtqfse"]["contract"] = {
        "input": "initial objective, acceptance criteria and run limits; subsequent ordered steering",
        "output": "initial run request; durable pending-steering event",
    }

    # Every original transition ID is present in the AI export. The AI corrects
    # reversed/missing flows and removes the old result-to-report bypass.
    assert {e["id"] for e in user["edges"]} <= {e["id"] for e in ai["edges"]}
    merged["edges"] = references(copy.deepcopy(ai["edges"]))
    merged["documentId"] = "polyinference-merged-user-layout-20261017"
    merged["title"] = "Polyinference · merged agent architecture"
    merged["description"] = (
        "Original node names and spatial layout, expanded architecture contracts and connections, "
        "and the original unmodified data and memory model.")

    # Keep the user's focus-view layouts, placing additions deliberately.
    merged["layouts"] = copy.deepcopy(user["layouts"])
    merged["layouts"]["cloud"].update({
        "state_xsyangll": {"x": 48, "y": 612},
        "integration_gate": {"x": 338, "y": 786},
        "state_rqc9j1bh": {"x": 918, "y": 264},
    })
    merged["layouts"]["local"].update({
        "private_code_copy": {"x": 628, "y": 90},
        "shell_mutex": {"x": 918, "y": 438},
        "verification_gate": {"x": 48, "y": 612},
        "reconciliation_dev": {"x": 48, "y": 786},
    })
    merged["layouts"]["delivery"].update({
        "integration_gate": {"x": 628, "y": 612},
        "verification_gate": {"x": 48, "y": 612},
        "reconciliation_dev": {"x": 338, "y": 612},
        "shell_mutex": {"x": 918, "y": 612},
        "state_hxca0deg": {"x": 918, "y": 264},
    })

    # Only the architecture labels are adjusted; memory labels are untouched.
    merged["labelPositions"] = {"cloud": {"x": -353, "y": 155},
                                "local": {"x": 531, "y": 168}}
    scopes = {
        "all": None,
        "cloud": ["state_xxdtqfse", "state_rahx5xff", "senior_review", "state_4qybbs1y",
                  "state_53hlm9fa", "state_xsyangll", "state_45l9fwoc", "state_5qvpqrzx",
                  "report", "state_4yxicmqq", "integration_gate", "state_rqc9j1bh", "final"],
        "local": ["state_rahx5xff", "state_5qvpqrzx", "private_code_copy", "local_infer",
                  "state_f3e0h1d3", "state_b93kssuk", "execute", "shell_mutex",
                  "verification_gate", "reconciliation_dev", "verdict", "report"],
        "delivery": ["state_rahx5xff", "state_45l9fwoc", "state_5qvpqrzx", "local_infer",
                     "state_b93kssuk", "verdict", "report", "state_4yxicmqq", "final",
                     "integration_gate", "verification_gate", "reconciliation_dev",
                     "shell_mutex", "state_hxca0deg"],
        "memory": None,
    }

    # Preserve the actual memory JSON text, not merely an equivalent rewrite.
    preserved_memory = memory_json(user_seed)
    merged["memoryGraph"] = "__MEMORY_GRAPH_PRESERVED_VERBATIM__"
    seed_text = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
    seed_text = seed_text.replace('"__MEMORY_GRAPH_PRESERVED_VERBATIM__"', preserved_memory)
    merged["memoryGraph"] = copy.deepcopy(user["memoryGraph"])
    source = SEED.sub(lambda m: m[1] + seed_text + m[3], source)
    source = re.sub(r"const scopes=.*?;\n", "const scopes=" + json.dumps(scopes) + ";\n", source, count=1)
    source = source.replace("<title>Polyinference — agent design v1</title>",
                            "<title>Polyinference — merged agent architecture</title>")
    source = source.replace("V1 PROPOSAL", "MERGED DESIGN")
    source = source.replace("19 states / 21 arrows", f'{len(merged["nodes"])} states / {len(merged["edges"])} arrows')

    # The memory view continues to use the original renderer. Other views show
    # complete canonical names on two lines rather than truncating references.
    old = "const title=node.title.length>25?node.title.slice(0,24)+'…':node.title;g.append(svg('text',{x:14,y:48,class:'node-title'},title),svg('text',{x:14,y:72,class:'node-sub'},(kindNames[node.kind]||'State')+'   ·   inspect →'));"
    new = """if(view==='memory'){const title=node.title.length>25?node.title.slice(0,24)+'…':node.title;g.append(svg('text',{x:14,y:48,class:'node-title'},title),svg('text',{x:14,y:72,class:'node-sub'},(kindNames[node.kind]||'State')+'   ·   inspect →'));}else{const label=svg('text',{x:14,y:44,class:'architecture-title'});let line='',lines=[];for(const word of node.title.split(' ')){if((line+' '+word).trim().length>24&&line){lines.push(line);line=word;}else line=(line+' '+word).trim();}if(line)lines.push(line);lines.forEach((text,i)=>label.append(svg('tspan',{x:14,dy:i?17:0},text)));g.append(label,svg('title',{},node.title),svg('text',{x:14,y:82,class:'node-sub'},(kindNames[node.kind]||'State')+'   ·   inspect →'));}"""
    assert old in source
    source = source.replace(old, new)
    source = source.replace("</style>", ".architecture-title{font-size:14px;font-weight:650;fill:#263244;letter-spacing:-.15px}\n</style>", 1)
    source = source.replace("download('polyinference-agent-design.html'", "download('polyinference-agent-design-merged.html'")
    source = source.replace("download('polyinference-agent-design.svg'", "download('polyinference-agent-design-merged.svg'")
    source = source.replace("download('polyinference-agent-structure.json'", "download('polyinference-agent-design-merged.json'")

    notes = """<dialog id="notes"><div class="dialog-top"><h2>Merged architecture</h2><button data-close="notes" aria-label="Close design notes">×</button></div><div class="dialog-body">
<h3>Read the original two-pipe layout</h3><p>Your original 15 architecture nodes retain their exact names, IDs and coordinates. The cloud strategy path remains on the left, local execution on the right, and orchestration above. The two Result Processor nodes remain distinct by their subtitles and stable IDs. Added workspace and synchronization nodes sit beside the local loop; shared memory and recovery services sit at the perimeter.</p>
<h3>Cloud strategy and execution</h3><p>USER PROMPT enters ORCHESTRATOR / LOOP HANDLER. Cloud Model · senior engineer selects the prompt mode; Cloud Query Processor packages it; Cloud process entry admits it; Cloud conductor / loop executes it. The cloud Result Processor validates the returned plan, review, specialist action or completion proposal. Prompt selection and packaging do not incur separate model calls.</p>
<h3>Private development, serialized final phase</h3><p>Task Queue starts a private code copy at base B. Local coding agent loop calls Local inference; its Result Processor routes proposals and observations through Tools &amp; observations. Private reasoning and non-shell edits can overlap. Every managed shell command takes Shell mutex · one command. A final candidate enters Verification critical section, captures current head H, merges and re-examines incoming changes in Merge head / reconciliation dev, then completes Task verification. When both are needed, acquire verification before shell.</p>
<h3>Commit, publish, then review</h3><p>Commit &amp; task report publishes the attributable provisional commit P and immutable unresolved report before verification ownership is released. All normally assessed verdicts—fail, uncertain and successful—remain unresolved. Senior resolution / commit undo applies keep, revert, retry or defer; undo follows the same ownership rules and examines dependent work. Host check evidence remains tied to the exact tree. Project acceptance requires senior agreement and independent current project checks.</p>
<h3>Steering, context and recovery</h3><p>Immediate Memory records steering immediately. New local starts stop; the captured running locals, including gate waiters, finish their original work before the planner applies steering. Pending unstarted tasks need not finish. Info Documentation batches durable report/disposition events and supplies pinned documentation. Trap frame mechanism retains continuation, ownership, effects and publication references for validated recovery.</p>
<h3>Data &amp; memory model</h3><p>This view is copied verbatim from your design, including every node, description, transition, coordinate and label position. Its original naming and contracts are deliberately preserved independently of the expanded architecture. Key frame remains deferred exactly as in your source.</p>
<h3>Reading and saving</h3><p>Solid arrows carry work and results; dashed arrows show exceptions and control barriers; dotted arrows show service/context dependencies. Select a node to highlight its connections, or select an arrow to read its trigger and payload. Focus views retain the original layouts and include relevant added nodes. Drag to pan, use the wheel to zoom, or press F to fit. JSON and Save HTML exports retain both graph models.</p>
</div></dialog>"""
    source = re.sub(r'<dialog id="notes">[\s\S]*?</dialog>', lambda _: notes, source, count=1)
    source = source.replace("A deliberate division of work.", "Your layout. Restored connections.")
    source = source.replace("The cloud owns direction. The local model owns bounded execution. The host owns evidence, budgets, and the handoff.",
                            "Cloud strategy stays on the left, local execution on the right. Select a state to follow its connections. Your data and memory model is preserved verbatim.")
    source = source.replace("Plan-scoped tools, a few bounded attempts, then host checks and an explicit verdict.",
                            "Private development, serialized reconciliation and final assessment, then an unresolved commit and report.")

    output = Path(__file__).parent
    html_path = output / "polyinference-agent-design-merged.html"
    json_path = output / "polyinference-agent-design-merged.json"
    html_path.write_text(source, encoding="utf-8")
    json_path.write_text(seed_text + "\n", encoding="utf-8")

    # Direct preservation checks, independent of any browser's autosave.
    _, actual, actual_seed = read(html_path)
    assert actual["memoryGraph"] == user["memoryGraph"]
    assert memory_json(actual_seed) == preserved_memory
    for node in user["nodes"]:
        result = next(n for n in actual["nodes"] if n["id"] == node["id"])
        assert all(result[k] == node[k] for k in ("id", "title", "x", "y", "subtitle", "kind"))
    for node in actual["nodes"]:
        if node["id"] in canonical:
            assert node["title"] == canonical[node["id"]]
    for graph in (actual, actual["memoryGraph"]):
        node_ids = {n["id"] for n in graph["nodes"]}
        assert len(node_ids) == len(graph["nodes"])
        assert len({e["id"] for e in graph["edges"]}) == len(graph["edges"])
        assert all(e["from"] in node_ids and e["to"] in node_ids for e in graph["edges"])
    print(json.dumps({"html": str(html_path), "nodes": len(actual["nodes"]),
                      "edges": len(actual["edges"]), "original_positions_preserved": len(original),
                      "memory_nodes": len(actual["memoryGraph"]["nodes"]),
                      "memory_edges": len(actual["memoryGraph"]["edges"]),
                      "memory_sha256": hashlib.sha256(preserved_memory.encode()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:])
