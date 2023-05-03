# SPDX-License-Identifier: Apache-2.0
# Copyright © 2022-2023 Intel Corporation

"""Type definitions for cargo manifest files."""

from __future__ import annotations
import typing as T

from typing_extensions import Literal, TypedDict

EDITION = Literal['2015', '2018', '2021']
CRATE_TYPE = Literal['bin', 'lib', 'dylib', 'staticlib', 'cdylib', 'rlib', 'proc-macro']

Package = TypedDict(
    'Package',
    {
        'name': str,
        'version': str,
        'authors': T.List[str],
        'edition': EDITION,
        'rust-version': str,
        'description': str,
        'readme': str,
        'license': str,
        'license-file': str,
        'keywords': T.List[str],
        'categories': T.List[str],
        'workspace': str,
        'build': str,
        'links': str,
        'include': T.List[str],
        'exclude': T.List[str],
        'publish': bool,
        'metadata': T.Dict[str, T.Dict[str, str]],
        'default-run': str,
        'autobins': bool,
        'autoexamples': bool,
        'autotests': bool,
        'autobenches': bool,
    },
    total=False,
)
"""A description of the Package Dictionary."""

FixedPackage = TypedDict(
    'FixedPackage',
    {
        'name': str,
        'version': str,
        'authors': T.List[str],
        'edition': EDITION,
        'rust_version': str,
        'description': str,
        'readme': str,
        'license': str,
        'license_file': str,
        'keywords': T.List[str],
        'categories': T.List[str],
        'workspace': str,
        'build': str,
        'links': str,
        'include': T.List[str],
        'exclude': T.List[str],
        'publish': bool,
        'metadata': T.Dict[str, T.Dict[str, str]],
        'default_run': str,
        'autobins': bool,
        'autoexamples': bool,
        'autotests': bool,
        'autobenches': bool,
    },
    total=False,
)
"""A description of the Package Dictionary, fixed up."""


Badge = TypedDict(
    'Badge',
    {
        'status': Literal['actively-developed', 'passively-developed', 'as-is', 'experimental', 'deprecated', 'none']
    },
    total=False,
)
"""An entry in the badge section."""


Dependency = TypedDict(
    'Dependency',
    {
        'version': str,
        'registry': str,
        'git': str,
        'branch': str,
        'rev': str,
        'path': str,
        'optional': bool,
        'package': str,
        'default-features': bool,
        'features': T.List[str],
    },
    total=False,
)
"""An entry in the *dependencies sections."""


FixedDependency = TypedDict(
    'FixedDependency',
    {
        'version': T.List[str],
        'registry': str,
        'git': str,
        'branch': str,
        'rev': str,
        'path': str,
        'optional': bool,
        'package': str,
        'default_features': bool,
        'features': T.List[str],
    },
    total=False,
)
"""An entry in the *dependencies sections, fixed up."""


DependencyV = T.Union[Dependency, str]
"""A Dependency entry, either a string or a Dependency Dict."""


BuildTarget = TypedDict(
    'BuildTarget',
    {
        'name': str,
        'path': str,
        'test': bool,
        'doctest': bool,
        'bench': bool,
        'doc': bool,
        'plugin': bool,
        'proc-macro': bool,
        'harness': bool,
        'edition': EDITION,
        'crate-type': T.List[CRATE_TYPE],
        'required-features': T.List[str],
    },
    total=False,
)


FixedBuildTarget = TypedDict(
    'FixedBuildTarget',
    {
        'name': str,
        'path': str,
        'test': bool,
        'doctest': bool,
        'bench': bool,
        'doc': bool,
        'plugin': bool,
        'harness': bool,
        'edition': EDITION,
        'crate_type': T.List[CRATE_TYPE],
        'required_features': T.List[str],
    },
    total=False,
)


class FixedLibTarget(FixedBuildTarget, total=False):

    proc_macro: bool


class Target(TypedDict):

    """Target entry in the Manifest File."""

    dependencies: T.Dict[str, DependencyV]


class Workspace(TypedDict):

    """The representation of a workspace.

    In a vritual manifest the :attribute:`members` is always present, but in a
    project manifest, an empty workspace may be provided, in which case the
    workspace is implicitly filled in by values from the path based dependencies.

    the :attribute:`exclude` is always optional
    """

    members: T.List[str]
    exclude: T.List[str]


Manifest = TypedDict(
    'Manifest',
    {
        'package': Package,
        'badges': T.Dict[str, Badge],
        'dependencies': T.Dict[str, DependencyV],
        'dev-dependencies': T.Dict[str, DependencyV],
        'build-dependencies': T.Dict[str, DependencyV],
        'lib': BuildTarget,
        'bin': T.List[BuildTarget],
        'test': T.List[BuildTarget],
        'bench': T.List[BuildTarget],
        'example': T.List[BuildTarget],
        'features': T.Dict[str, T.List[str]],
        'target': T.Dict[str, Target],
        'workspace': Workspace,

        # TODO: patch?
        # TODO: replace?
    },
    total=False,
)
"""The Cargo Manifest format."""


class VirtualManifest(TypedDict):

    """The Representation of a virtual manifest.

    Cargo allows a root manifest that contains only a workspace, this is called
    a virtual manifest. This doesn't really map 1:1 with any meson concept,
    except perhaps the proposed "meta project".
    """

    workspace: Workspace
