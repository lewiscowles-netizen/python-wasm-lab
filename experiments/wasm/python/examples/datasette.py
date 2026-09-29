# Select Pyodide and enable micropip; leave the packages box empty.
import json
import sqlite3
import micropip
from pyodide.http import pyfetch

response = await pyfetch("./examples/datasette-requirements.txt")
requirements = [
    line.strip()
    for line in (await response.string()).splitlines()
    if line.strip() and not line.startswith("#")
]
await micropip.install(requirements)

from datasette.app import Datasette

connection = sqlite3.connect("/tmp/lab.db")
connection.execute("CREATE TABLE releases (name TEXT, year INTEGER)")
connection.executemany(
    "INSERT INTO releases VALUES (?, ?)",
    [("Python 2.7", 2010), ("Python 3.0", 2008)],
)
connection.commit()
connection.close()

# Use in-process application requests with SQL threads disabled.
ds = Datasette(["/tmp/lab.db"], settings={"num_sql_threads": 0})
await ds.invoke_startup()

response = await ds.client.get("/lab/releases.json?_shape=array")
print("JSON status:", response.status_code)
print("JSON content type:", response.headers["content-type"])
print("Rows:", json.dumps(response.json(), sort_keys=True))

html = await ds.client.get("/lab/releases")
print("HTML status:", html.status_code)
print("HTML content type:", html.headers["content-type"])
print("HTML contains our row:", "Python 2.7" in html.text)

missing = await ds.client.get("/not-a-database.json")
print("Missing page status:", missing.status_code)
