# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from packaging.specifiers import SpecifierSet
from packaging.version import Version
import pandas

assert Version(pandas.__version__) in SpecifierSet(">=2.2.3,<3")
