// Keep entropy per instance. Node's wrapper supplies its cryptographic RNG;
// browsers and workers use the Web Crypto API.
var crypto = Module['entropyProvider'] || globalThis.crypto;
