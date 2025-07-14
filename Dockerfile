FROM python:3.12-slim
WORKDIR /usr/src/app

ARG MAESTRO_VERSION="0.3.0"

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install pip and dependencies
RUN pip install --upgrade pip

# Install dependencies
COPY dist/maestro-${MAESTRO_VERSION}-py3-none-any.whl maestro-${MAESTRO_VERSION}-py3-none-any.whl
RUN pip install maestro-${MAESTRO_VERSION}-py3-none-any.whl
RUN rm maestro-${MAESTRO_VERSION}-py3-none-any.whl

RUN chown -R 1000:100 /usr/src/app &&\
    mkdir -p /usr/src/app/src/media && chown 1000:100 /usr/src/app/src/media

EXPOSE 5000
USER 1000:100

