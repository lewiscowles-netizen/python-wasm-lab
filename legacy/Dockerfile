# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 emscripten/emsdk:2.0.2@sha256:d2daf8d497c38f69e854239b06679184dcb676580fcb56146a3ad6f559b47aa6 AS configured
ARG PYTHON_VERSION=2.7.18
ARG PYTHON_SHA256=b62c0e7937551d0cc02b8fd5cb0f544f9405bafc9a54d3808ed4594812edef43
WORKDIR /build
COPY patches /patches
COPY configure.sh /recipe/
RUN curl -fsSL https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz -o python.tar.xz \
 && echo "${PYTHON_SHA256}  python.tar.xz" | sha256sum -c - \
 && tar -xf python.tar.xz \
 && mv Python-${PYTHON_VERSION} source
RUN bash /recipe/configure.sh
FROM configured AS build
COPY compile.sh /recipe/
RUN bash /recipe/compile.sh
COPY build.sh smoke.mjs python.mjs entropy.js manifest.py notices.py /recipe/
RUN bash /recipe/build.sh
FROM scratch AS artifacts
COPY --from=build /out/ /

FROM scratch AS configuration
COPY --from=configured /build/wasm/config.log /config.log
COPY --from=configured /build/wasm/pyconfig.h /pyconfig.h
COPY --from=configured /build/wasm/Makefile /Makefile

FROM artifacts AS output
