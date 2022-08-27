FROM ubuntu:22.04

##################################################################################
# Install pyenv (https://github.com/pyenv/pyenv/wiki#suggested-build-environment)
##################################################################################

RUN echo "installing pyenv"
RUN apt-get update
# install tzdata to remove "Please select the geographic area in which you live" when installing pyenv dependencies
RUN apt-get install -y tzdata && \
    apt-get install -y make build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

RUN apt-get install -y git apt-utils

# install pyenv
RUN curl https://pyenv.run | bash

# add pyenv to path
RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile && \
    echo 'eval "$(pyenv init -)"' >> ~/.profile

ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:${PATH}"
RUN echo $PATH

##################################################################################
# Install python
##################################################################################

RUN pyenv install 3.9.9 && \
    pyenv global 3.9.9

##################################################################################
# Install EG prerequisites
##################################################################################

RUN apt-get install -y libgmp-dev libmpfr-dev libmpc-dev
RUN pip install 'poetry==1.1.13'

##################################################################################
# Poetry Install
##################################################################################

RUN mkdir /app
WORKDIR /app
# --no-root allows us to copy the minimum to just get dependencies to give
#       Docker very few reasons to invalidate the poetry install layer
COPY pyproject.toml README.md ./
RUN poetry config virtualenvs.in-project true && \
	poetry install --no-root

##################################################################################
# Get Source
##################################################################################

# cleanup first, the next layer will get invalidated easiliy
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ./src ./src
RUN rm src/electionguard_gui/__init__.py

##################################################################################
# Run EGUI
##################################################################################

# the final poetry install runs fast, it activates the virtualenv and initializes the modules
RUN poetry install

ENTRYPOINT ["poetry", "run", "egui"]
# alternately, for testing:
# ENTRYPOINT ["tail", "-f", "/dev/null"]
