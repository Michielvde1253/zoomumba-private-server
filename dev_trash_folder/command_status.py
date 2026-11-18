"""
Regenerate the command list in README.md from the handlers the server has.

    python tools/command_status.py path/to/scripts/com/bigpoint/zoomumba/constants/NET.as

NET.as is the client's list of every call (from the decompiled SWF). The
README section between the "List of game commands" heading and the end of
the file is replaced.
"""
import re, sys, os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
sys.path[:0] = [".", "commands", "commands/field_actions"]
os.environ.setdefault("LOCAL_DEV_MODE", "1"); os.environ.setdefault("MONGO_URI", "mongodb://x")
import mongomock, pymongo; pymongo.MongoClient = mongomock.MongoClient
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import app
from stubs import READ, NOOP, EVENT, TODO
from field_fia import available_field_actions
from inventory_iva import HANDLERS as IVA
net = open(sys.argv[1]).read()
rows = []
for const, body in re.findall(r'const (\w+):String = "(.*?)";', net):
    body = body.replace('\\"', '"')
    m = re.search(r'\{\s*"([\w.]+)"\s*:', body)
    if not m: continue
    cmd = m.group(1)
    fia = re.search(r'"fia"\s*:\s*"(\w+)"', body); iva = re.search(r'"iva"\s*:\s*"(\w+)"', body)
    if cmd in app.available_commands:
        status = "x"
        if cmd == "field.fia":
            status = "x" if fia and fia.group(1) in available_field_actions else " "
        if cmd == "inventory.iva" and iva and iva.group(1) != "gui":
            status = "x" if any(k[0] == iva.group(1) for k in IVA) else " "
        note = ""
    elif cmd in READ: status, note = "~", "stub: returns saved data"
    elif cmd in NOOP: status, note = "~", "stub: accepted, ignored"
    elif cmd in EVENT: status, note = " ", "event not running"
    else: status, note = " ", "not implemented"
    rows.append((cmd, const, status, note, fia.group(1) if fia else None))
rows.sort(key=lambda r: (r[0], r[1]))
impl = [r for r in rows if r[2] == "x"]
stub = [r for r in rows if r[2] == "~"]
event = [r for r in rows if r[3] == "event not running"]
todo = [r for r in rows if r[3] == "not implemented"]


def fmt(r):
    cmd, const, status, note, fia = r
    extra = f" (`{fia}`)" if fia else ""
    mark = "x" if status == "x" else " "
    return f"- [{mark}] {cmd}{extra} - {const}" + (f" — {note}" if note else "")


section = f"""## List of game commands

Every command in the client's `NET.as`: {len(impl)} implemented, {len(stub)} stubbed, {len(event)} seasonal event commands (answer "event not running"), {len(todo)} not implemented yet. Regenerate with `python tools/command_status.py <NET.as>`.

### Implemented

""" + "\n".join(map(fmt, impl)) + """

### Stubbed (the client gets an answer, nothing is changed)

""" + "\n".join(map(fmt, stub)) + """

### Not implemented yet

""" + "\n".join(map(fmt, todo)) + """

### Seasonal events (answer "event not running")

""" + "\n".join(map(fmt, event)) + "\n"
readme = open("README.md").read()
readme = readme[:readme.index("## List of game commands")] + section
open("README.md", "w").write(readme)
print(f"{len(impl)} implemented, {len(stub)} stubs, {len(event)} event, {len(todo)} not implemented")
