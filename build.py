import multiprocessing
from pathlib import Path
from typing import List

from setuptools import Extension, Distribution

# so that copy_extensions_to_source is in cython_build_ext (complicated import process)
import setuptools.command.build_ext
# it doesn't even works :(
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py

from Cython.Build import cythonize
from Cython.Distutils.build_ext import new_build_ext as cython_build_ext

SOURCE_DIR = Path("poetry_compile_test")  # replace SRC with the root of your source
BUILD_DIR = Path("cython_build")

def get_extension_modules() -> List[Extension]:
    """Collect all .py files and construct Setuptools Extensions"""
    extension_modules: List[Extension] = []

    for py_file in SOURCE_DIR.rglob("*.py"):

        # Get path (not just name) without .py extension
        module_path = py_file.with_suffix("")

        # Convert path to module name
        module_path = str(module_path).replace("/", ".").replace("\\", ".")

        extension_module = Extension(
            name=module_path,
            sources=[str(py_file)]
        )

        extension_modules.append(extension_module)

    return extension_modules

def cythonize_helper(extension_modules: List[Extension]) -> List[Extension]:
    """Cythonize all Python extensions"""

    return cythonize(
        module_list=extension_modules,

        # Don't build in source tree (this leaves behind .c files)
        build_dir=BUILD_DIR,

        # Don't generate an .html output file. Would contain source.
        annotate=False,

        # Parallelize our build
        # nthreads=multiprocessing.cpu_count() * 2,

        # Tell Cython we're using Python 3. Becomes default in Cython 3
        compiler_directives={"language_level": "3"},

        # (Optional) Always rebuild, even if files untouched
        force=True,
    )

# Collect and cythonize all files
extension_modules = cythonize_helper(get_extension_modules())

class BuildExt(build_ext):
    def finalize_options(self):
        super().finalize_options()
        self.build_lib = f"{self.build_lib}.blah"

    def run(self):
        ...


# Use Setuptools to collect files
distribution = Distribution({
    "ext_modules": extension_modules,
    "cmdclass": {
        "build_ext": build_ext,
    },
})

# Grab the build_ext command and copy all files back to source dir.
# Done so Poetry grabs the files during the next step in its build.
distribution.run_command("build_ext")
build_ext_cmd = distribution.get_command_obj("build_ext")
build_ext_cmd.copy_extensions_to_source()
