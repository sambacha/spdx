#!/usr/bin/python3
# SPDX-License-Identifier: Apache-2.0

import extensions
import json
import os
import sys

# Given a root directory and a set of file extensions, this function finds all
# files under the root directory with an extension in the list of extensions.
def yield_files(root_dir, types):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            name, extension = os.path.splitext(file)
            extension = extension.replace(".", "")
            if extension in types:
                yield (os.path.join(root, file), extension)


# Given a line from a file, check if it's a valid shebang.
def check_shebang(line):
    if len(line) >= 2 and line[:2] == "#!":
        return True
    return False


# Determine whether a given line in a file is a valid SPDX header, given
# acceptable licenses.
#
# Inputs:
# line: a line from a file
# licenses: a list of acceptable licenses
# comments: a list of acceptable comment starters
# filename: the file being checked
def check_license(line, licenses, comments, filename):
    tokens = line.split(" ")
    tokens = [t.strip() for t in tokens]
    if len(tokens) != 3:
        print(
            f"""
File {filename} has an incorrectly formatted SPDX header.
Ensure the SPDX header matches the format:
SPDX-License-Identifier: <license-id>
        """
        )
        return 1
    if tokens[0] not in comments:
        print(
            f"""
File {filename} does not use an allowed comment format.
Allowed formats are:
{comments}
        """
        )
        return 1
    if tokens[1] != "SPDX-License-Identifier:":
        print(
            f"""
File {filename} does not specify 'SPDX-License-Identifier' correctly.
Ensure the SPDX header matches the format:
SPDX-License-Identifier: <license-id>
        """
        )
        return 1
    if tokens[2] not in licenses:
        print(
            f"""
File {filename} does not use an allowed license.
Allowed licenses are:
{licenses}
        """
        )
        return 1

    # If none of the above failures happen, this line is a valid header.
    return 0


# Get the input file types to check.
print(sys.argv[1])
licenses = json.loads(sys.argv[1])

# Get the calling workflow's workspace.
workspace = os.environ.get("GITHUB_WORKSPACE", None)
# Grab all file paths to check.
files_to_check = yield_files(workspace, licenses.keys())

# Default exit code to 0 (success).
code = 0

# Check each file for its SPDX header.
for file in files_to_check:
    extension_rules = extensions.rules.get(file[1])
    if extension_rules is None:
        print(
            f"""
File type {file[1]} does not have SPDX header rules defined. Please consider
contributing a ruleset.
        """
        )
        continue

    try:
        f = open(file[0], "r")
    except:
        print(f"File {file[0]} cannot be opened.")
        code = 1
        continue

    line = f.readline()

    if not line:
        print(f"File {file[0]} is empty.")
        code = 1
        f.close()
        continue

    # If a shebang is allowed for this file type and the first line is a valid
    # shebang, skip to the next line.
    if extension_rules["shebang"] and check_shebang(line):
        line = f.readline()
        if not line:
            print(f"File {file[0]} does not include a valid SPDX header.")
            code = 1
            f.close()
            continue
    f.close()

    # Check for a valid SPDX header.
    code = check_license(line, licenses[file[1]], extension_rules["comment"], file[0])

# Exit with the appropriate code.
exit(code)
