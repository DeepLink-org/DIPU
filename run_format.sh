#!/usr/bin/env bash

# format all C/C++ files in current git repository with clang-format
CLANG_FORMAT_EXCLUDE_REGEX='^.*nlohmann/json\.hpp$'
git ls-files |\
  grep -E '^.+\.(c|h|cpp|cc|cxx|hpp|hh|hxx|cu|cuh)$' |\
  grep -Ev "$CLANG_FORMAT_EXCLUDE_REGEX" |\
  xargs clang-format -i --style=file
