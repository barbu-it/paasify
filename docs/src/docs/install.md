# Installation

There are different ways to install paasify. The most recommended way is with pip.

If you want to develop or
patch paasify, you have to [install paasify with git](install) instead.




## Install with Pip

To install pip at home:

```
pip install --user paasify
```

## Install with Docker

!!! warning "About using this method"

    Using docker installation is the fastest way to use and test Paasify. However, this
    method is limited and will not work if you have reference from outside of your
    project directory. This way is the best way for quick try or production
    deployment.


You can also run the docker image by this way:

```
docker run --rm -v $PWD:/work -ti ghcr.io/barbu-it/paasify:latest --help
```

For a more convenient shell wrapper:
```
$ sudo cat <<EOF > /usr/local/bin/paasify
#!/bin/bash

docker run --rm -v $PWD:/work -ti ghcr.io/barbu-it/paasify:latest $@
EOF
$ sudo chmod +x /usr/local/bin/paasify
```
