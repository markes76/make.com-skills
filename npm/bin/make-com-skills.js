#!/usr/bin/env node
"use strict";

const { main } = require("../lib/bridge.cjs");

main(process.argv.slice(2)).then(
  (exitCode) => {
    if (typeof exitCode === "number") {
      process.exitCode = exitCode;
    }
  },
  (error) => {
    console.error(`make-com-skills failed: ${error.message}`);
    process.exitCode = 1;
  },
);
