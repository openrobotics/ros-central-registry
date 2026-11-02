# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Bazel equivalent of cmake/rmf_api_generate_schema_headers.cmake."""

_TEMPLATE = Label("//:cmake/schemas_template.hpp.in")

def rmf_api_generate_schema_headers(name, package, schemas, out_dir = "_gen/include", **kwargs):
    """Render one <package>/schemas/<schema>.hpp per JSON schema.

    Mirrors the upstream CMake function: for every schemas/*.json it runs
    configure_file(@ONLY) on cmake/schemas_template.hpp.in, embedding the
    schema text in a raw string literal.

    Args:
      name: name of the filegroup collecting all generated headers.
      package: C++ namespace / include directory (upstream's PACKAGE arg).
      schemas: list of *.json schema files.
      out_dir: directory (relative to the calling package) for the headers.
      **kwargs: forwarded to the filegroup.
    """
    upper_package = package.upper()
    outs = []
    for schema in schemas:
        schema_name = schema.split("/")[-1].rsplit(".", 1)[0]
        out = "%s/%s/schemas/%s.hpp" % (out_dir, package, schema_name)
        outs.append(out)
        native.genrule(
            name = "%s_%s" % (name, schema_name),
            srcs = [schema],
            outs = [out],
            tools = [_TEMPLATE],
            # @_PACKAGE@ is never set by the upstream function, so CMake
            # renders it as an empty string; keep that.
            cmd = " | ".join([
                "sed -e 's/@_PACKAGE@//' " +
                "-e 's/@upper_package_name@/%s/g' " % upper_package +
                "-e 's/@upper_schema_name@/%s/g' " % schema_name.upper() +
                "-e 's/@_ARG_PACKAGE@/%s/g' " % package +
                "-e 's/@schema_name@/%s/g' " % schema_name +
                "$(execpath %s)" % _TEMPLATE,
                "awk -v f=$(execpath %s) '" % schema +
                "{ i = index($$0, \"@schema_text@\"); " +
                "if (i) { printf \"%s\", substr($$0, 1, i - 1); " +
                "while ((getline l < f) > 0) print l; " +
                "print substr($$0, i + 13) } else print }'",
            ]) + " > $@",
        )
    native.filegroup(
        name = name,
        srcs = outs,
        **kwargs
    )
