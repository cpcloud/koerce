from __future__ import annotations

import os
import shutil
from pathlib import Path

import Cython.Compiler.Options
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools import Distribution

Cython.Compiler.Options.cimport_from_pyx = True

SOURCE_DIR = Path("koerce")
BUILD_DIR = Path("cython_build")


cythonized_modules = cythonize(
    [
        "koerce/patterns.py",
        "koerce/builders.py",
    ],
    build_dir=BUILD_DIR,
    # generate anannotated .html output files.
    annotate=True,
    # nthreads=multiprocessing.cpu_count() * 2,
    compiler_directives={"language_level": "3"},
    # always rebuild, even if files untouched
    force=False,
)

dist = Distribution({"ext_modules": cythonized_modules})
cmd = build_ext(dist)
cmd.ensure_finalized()
cmd.run()

for output in cmd.get_outputs():
    relative_extension = os.path.relpath(output, cmd.build_lib)
    shutil.copyfile(output, relative_extension)
