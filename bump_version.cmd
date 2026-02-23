@echo off

call activate

set PYTHONPATH=.;..\runtime;%PYTHONPATH%

echo.
echo Update package version
@python -m tools.cl.runtime.bump_module_version --module cl.runtime --module stubs.cl.runtime
