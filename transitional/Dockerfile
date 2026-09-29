# syntax=docker/dockerfile:1.7
FROM emscripten/emsdk:5.0.3@sha256:7b5d14203bb4ef20da6f5b71b90c8f37ec09c2776d342efff3bc989ebf1aa873 AS configured
ARG PYTHON_VERSION=3.10.21
ENV PYTHON_VERSION=${PYTHON_VERSION} SOURCE_DATE_EPOCH=1789430400 TZ=UTC LC_ALL=C.UTF-8
WORKDIR /build
COPY sources.json fetch.py /recipe/
RUN python3 /recipe/fetch.py
COPY port.py configure.sh sdk-config.site /recipe/
RUN bash /recipe/configure.sh
FROM configured AS compiled
COPY compile.sh /recipe/
RUN bash /recipe/compile.sh
FROM compiled AS linked
COPY stdlib.py link.sh /recipe/
RUN bash /recipe/link.sh
COPY smoke.mjs manifest.py notices.py /recipe/
RUN cp /recipe/smoke.mjs /out/ && cp /build/source/LICENSE /out/CPYTHON-LICENSE.txt \
    && python3 /recipe/notices.py /build/source /out/THIRD-PARTY-NOTICES.txt \
    && cd /out && node smoke.mjs "${PYTHON_VERSION}" > smoke.json \
    && python3 -c 'import os,json,subprocess; v=os.environ["PYTHON_VERSION"]; p=json.load(open("/recipe/sources.json"))[v]; subprocess.run(["python3","/recipe/manifest.py","/out",v,p["url"],p["sha256"]],check=True)'
FROM scratch AS configuration-evidence
COPY --from=configured /build/wasm/config.log /build/wasm/pyconfig.h /build/wasm/Makefile /
FROM scratch AS artifacts
COPY --from=linked /out/ /
