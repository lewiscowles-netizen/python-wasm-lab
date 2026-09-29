# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 emscripten/emsdk:2.0.2@sha256:d2daf8d497c38f69e854239b06679184dcb676580fcb56146a3ad6f559b47aa6 AS sources
ARG PYTHON_VERSION=3.0.1
ENV PYTHON_VERSION=${PYTHON_VERSION}
WORKDIR /build
COPY sources.json fetch.py /recipe/
RUN python3 /recipe/fetch.py
FROM sources AS configured
COPY port.py configure.sh emscripten-2.0.2.config.site /recipe/
RUN bash /recipe/configure.sh
FROM configured AS build
COPY compile.sh /recipe/
RUN bash /recipe/compile.sh
COPY link.sh smoke.mjs python.mjs entropy.js manifest.py notices.py /recipe/
RUN bash /recipe/link.sh
FROM scratch AS artifacts
COPY --from=build /out/ /
