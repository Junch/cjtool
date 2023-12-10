@echo off 
set config=Release
set folder=_build-x64

@mkdir %folder% >nul
pushd %folder% >nul

@echo on

cmake -A x64 ..
cmake --build . --config %config%

@echo off
popd >nul

pause
