FROM python:3.12-slim-bookworm

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR
ARG POETRY_VERSION=2.1.3
ARG KOTLIN_VERSION=2.3.20

RUN apt-get update && \
    apt-get -y install nano curl unzip && \
    pip install --upgrade pip && \
    pip install --upgrade pip "poetry==${POETRY_VERSION}"

RUN apt-get -y install openjdk-17-jdk-headless

RUN curl -sLO "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip" && \
    unzip "kotlin-compiler-${KOTLIN_VERSION}.zip" -d /opt && \
    ln -s /opt/kotlinc/bin/kotlinc /usr/local/bin/kotlinc && \
    ln -s /opt/kotlinc/bin/kotlin /usr/local/bin/kotlin && \
    rm "kotlin-compiler-${KOTLIN_VERSION}.zip"

RUN adduser \
    --system \
    --gecos \
    --disabled-login \
    --disabled-password \
    --home ${SANDBOX_DIR} \
    --uid ${SANDBOX_USER_UID} \
    sandbox && \
    chown root:root ${SANDBOX_DIR}

COPY ./src/pyproject.toml ./src/poetry.lock /tmp/
RUN cd /tmp && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-ansi

WORKDIR ${SANDBOX_DIR}
