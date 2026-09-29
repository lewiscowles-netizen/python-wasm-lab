# Tutorial: compare two Python interpreters

By the end, you will have run the same source in old and modern Python, inspected a capability difference and stopped a busy interpreter. Use the [run guide](../../../docs/how-to/run-lab.md) first so the local builds appear in the playground. This tutorial requires no AI service.

## 1. Run the same program twice

Choose **CPython 2.7.18** and **Version and arithmetic**, then press **Run Python**. Find the version reported below the editor and the division results in standard output.

Choose a modern stable CPython build and run the unchanged example again. Both calculate the same sum of squares. Slash division changes because you are running different Python language versions, not a source translator.

Choose **Language differences**. Uncomment the f-string example and run it with the modern interpreter, then return to 2.7. The older parser rejects syntax it does not know. Restore the comment before continuing.

## 2. Inspect the environment

Choose **Python info** and run it. Find pointer width, Unicode representation, module probes and target build metadata. Compare old and modern output. A missing optional facility is reported without aborting the whole report.

Choose **Standard library probe** next. Notice that selecting a Python version does not promise every module from a desktop installation. The [runtime matrix](../../../docs/reference/runtimes.md) distinguishes observed availability from modules that were not probed.

## 3. Create and discard a file

Run **Ephemeral files**. It writes and reads a file in the interpreter's virtual filesystem. Replace the editor with:

```python
with open("/tmp/python-wasm-example.txt") as source:
    print(source.read())
```

Run again. The file is missing because this run uses a fresh interpreter. You have observed the lifetime of application state, not a disk-permission failure.

## 4. Try the richer package runtime

Choose **Pyodide** and **Pure Python wheel · Pyodide**. Enable micropip and enter the requirement shown in the example note. Run the example and inspect its output. This step requires internet access.

Uncheck micropip and run again. The missing import shows that the newly started interpreter did not retain the installation. For compiled packages, try **Compiled NumPy package · Pyodide** with automatic import loading enabled. The [package explanation](../../../docs/explanation/packages-and-applications.md) explains why the two loaders differ.

The **Datasette application · Pyodide** example goes further: follow its on-page note and inspect the application responses. Its dependency pins live in [datasette-requirements.txt](examples/datasette-requirements.txt).

## 5. Recover from a busy program

Choose **Stop an infinite loop** and run it, then press **Stop**. Choose **Version and arithmetic** and run again. The page remains usable because execution happens in a disposable worker.

You can now vary source, interpreter and package options independently. The [interface reference](README.md) specifies controls and output; the [architecture explanation](../../../docs/explanation/architecture.md) explains their costs and limits.
