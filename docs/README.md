# Paasify Documentation

Documentation source lives in [src](src/) directory. The documentation build process
involves `mkdocs` and some other parts of the project, such as APIdoc, Jupyter notebooks
and other files of the git repository.

There is two ways to build/test the documentation:

* with Python environment
* with Docker

## Python environment

To ensure the documenation is correctly build, just run:

```
mkdocs build
```

This will create a [build](build/) directory where will live html files. The build process
involve the `gen_apidoc.py` file that prepare the other required elements to build the
documenation.

To test locally the documenation

```
mkdocs serve
```

Documentation is now available on [http://127.0.0.1:8000/](http://127.0.0.1:8000/). To start
Jupyter:

```
jupyter-notebook --notebook-dir src/jupyter/
```

Jupyter is now available on [http://127.0.0.1:8888/](http://127.0.0.1:8888/).

## Docker

There is also a provided [docker-compose.yml](docker-compose.yml) file that exposes the following
services:

```
docker-compose up
```

Documentation is now available on [http://127.0.0.1:8042/](http://127.0.0.1:8042/), while Jupyter
will be available on [http://127.0.0.1:8043/](http://127.0.0.1:8043/)

