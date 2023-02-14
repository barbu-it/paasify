# Update Docs

This page explains how to update documentation.


## Quickstart

When working only on documentation, it's easier to change your working directory in docs, but eventually you can always :
```
cd docs
```

Then start your local server:
```
# If you are in docs/
task doc_serve

# If you are still at the root /
task doc:doc_serve
```

Your own local documentation is now live: [http://127.0.0.1:8000/paasify/](http://127.0.0.1:8000/paasify/)


!!! warning
    Be sure the mkdocs deamon does not run while you build the package, as the build package will
    trigger a documentation release.


To go further, check the available commands and read the following chapters.

```
task --list
```


## Implementation details

There are different cool stuffs in the doc:

### Docker stack: Integrated IDE

You can also use the integrated web IDE (vscode).
```
task doc_serve

# Or from root
task doc:serve_ide
```

Applications:

* Documentation: [http://127.0.0.1:8042](http://127.0.0.1:8042/)
* Jupyter Notebook Editor:  [http://127.0.0.1:8043](http://127.0.0.1:8043/), token is shown in docker logs.
* Code OSS Editor (optional):  [http://127.0.0.1:8044](http://127.0.0.1:8044/), please enable in `docker-compose.yml` file.

From these, you can both edit the code with a visual editor (if you enabled it) and also run jupyter notebooks, and see in live the result in the web page.


### mkdocs

mkdocs is a static website generator. It eat markdown files and generate beautiful html pages.

Build documentation:
```
task doc:build_doc
```


### Generated API/Docs

Documentation need to fetch and copy other files from the project to be able to build completely. This process is scripted in `gen_apidoc.py` script; this script can either be called by hand, or it is automagicaly called when mkdocs build its files. See `mkdocs.toml` to see how it is implemented into mkdocs. For your information, this is the way we run this process manually:

```
./gen_apidoc.py src/
```


From there, you can launch a local instance of the website, you will see in logs messages that the above scripts has been executed. :
```
task -v doc_serve
```


To publish documentation on GH pages:
```
task publish_gh
```


### Jupyter

Jupyter playbooks are meant to be edited into the browser. Start the server this way
```
task jupyter_serve
```
Then got to [http://127.0.0.1:8043](http://127.0.0.1:8043/) to be able to edit notebooks.
