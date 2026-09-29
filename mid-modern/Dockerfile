# syntax=docker/dockerfile:1.7
ARG EMSDK_IMAGE=emscripten/emsdk:5.0.3@sha256:7b5d14203bb4ef20da6f5b71b90c8f37ec09c2776d342efff3bc989ebf1aa873
FROM ${EMSDK_IMAGE} AS source
ARG PYTHON_VERSION=3.13.15
ARG PYTHON_SERIES=3.13
ARG PYTHON_URL=https://www.python.org/ftp/python/3.13.15/Python-3.13.15.tar.xz
ARG PYTHON_SHA256=1e66a7945a48390ee4c2a4268a0e4185884059a13c4aab6d148aa208deea4a76
ARG JOBS=2
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
FROM native AS wasm
COPY scripts /builder
RUN python3 /builder/stdlib.py /src/cpython/Lib /bundle/lib "${PYTHON_SERIES}"
WORKDIR /src/wasm
RUN bash /builder/build.sh
# Preserve the expensive configure/build cache while retaining the empty import directory.
RUN touch /bundle/lib/python${PYTHON_SERIES}/lib-dynload/.empty \
    && rm -f python.mjs python.wasm python.data \
    && make -j${JOBS} LINKFORSHARED='-O2 -g0 --preload-file /bundle@/' python.mjs > /src/wasm-relink.log 2>&1 \
    || { tail -100 /src/wasm-relink.log; exit 1; }
COPY validation /builder
RUN mkdir -p /out && cp python.mjs python.wasm python.data /out/ \
    && cp /src/cpython/LICENSE /out/CPYTHON-LICENSE.txt \
    && python3 /builder/notices.py /src/cpython /out/THIRD-PARTY-NOTICES.txt \
    && cp /builder/smoke.mjs /out/smoke.mjs \
    && cd /out && node smoke.mjs "${PYTHON_VERSION}" > smoke.json \
    && python3 /builder/manifest.py /out "${PYTHON_VERSION}" "${PYTHON_URL}" "${PYTHON_SHA256}"
FROM scratch AS artifacts
COPY --from=wasm /out/ /
