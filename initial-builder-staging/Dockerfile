# syntax=docker/dockerfile:1.7
ARG EMSDK_IMAGE=emscripten/emsdk:5.0.3@sha256:7b5d14203bb4ef20da6f5b71b90c8f37ec09c2776d342efff3bc989ebf1aa873
FROM ${EMSDK_IMAGE} AS source
ARG PYTHON_VERSION=3.15.0rc2
ARG PYTHON_SERIES=3.15
ARG PYTHON_URL=https://www.python.org/ftp/python/3.15.0/Python-3.15.0rc2.tar.xz
ARG PYTHON_SHA256=8d93af5eaaaea5adfd41bd786a7ba3f03f2ad1ab57c6a65e0b963deab91d5ad7
ARG JOBS=4
ENV SOURCE_DATE_EPOCH=1789430400 TZ=UTC LC_ALL=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl xz-utils make gcc g++ pkg-config libz-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN curl --fail --location --retry 3 "${PYTHON_URL}" -o python.tar.xz \
    && echo "${PYTHON_SHA256}  python.tar.xz" | sha256sum -c - \
    && mkdir cpython && tar -xf python.tar.xz --strip-components=1 -C cpython
FROM source AS native
WORKDIR /src/native
RUN ../cpython/configure --without-ensurepip --disable-test-modules \
    && make -j${JOBS} > /src/native-build.log 2>&1 \
    || { tail -80 /src/native-build.log; exit 1; }
FROM native AS configured
COPY scripts/stdlib.py /builder/stdlib.py
RUN python3 /builder/stdlib.py /src/cpython/Lib /bundle/lib "${PYTHON_SERIES}"
WORKDIR /src/wasm
COPY scripts/build-modern.sh /builder/build-modern.sh
RUN /builder/build-modern.sh
FROM configured AS compiled
RUN make -j${JOBS} "libpython${PYTHON_SERIES}.a" Programs/python.o > /src/wasm-build.log 2>&1 \
    || { tail -100 /src/wasm-build.log; exit 1; }
FROM compiled AS wasm
COPY scripts/link-modern.sh /builder/link-modern.sh
RUN bash /builder/link-modern.sh
COPY scripts/smoke.mjs scripts/manifest.py /builder/
RUN mkdir -p /out && cp python.mjs python.wasm python.data /out/ \
    && cp /src/cpython/LICENSE /out/CPYTHON-LICENSE.txt \
    && cp /builder/smoke.mjs /out/smoke.mjs \
    && cd /out && node smoke.mjs "${PYTHON_VERSION}" > smoke.json \
    && python3 /builder/manifest.py /out "${PYTHON_VERSION}" "${PYTHON_URL}" "${PYTHON_SHA256}"
FROM scratch AS artifacts
COPY --from=wasm /out/ /
