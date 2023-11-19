# README

Provide some tools in C++ development. 

- Extracted raw strings from the C++ code


The source code is [here](https://github.com/Junch/cjtool). The python package is [here](https://pypi.org/project/cjtool).

## 1. How to install

```
pip install cjtool
```

## 2. Command

A new command `stringrep.exe` is added after the installation.

- The command `stringrep` is to replace the raw string to a pointer. For example

```cpp
    auto m = py::module::import("test_cmake_build");
    // convert to the line below
    auto m = py::module::import(pStrTest_cmake_build);

    // the definiation of the string is as below
    constexpr char* pStrTest_cmake_build = "test_cmake_build";
```


- Help message from the command `stringrep` is as below.

```
$ stringrep -h
usage: stringrep [-h] [-i] [-c] [-g] [-p PREFIX] file

positional arguments:
  file                  set the cpp file name

optional arguments:
  -h, --help            show this help message and exit
  -i, --inplace         replace the file in place (default: False)
  -c, --capitalize      capitalize the captured word, for example,
                        "tom" turns to "Tom" (default: False)
  -g, --generate        generate the header lines for the captured
                        strings (default: False)
  -p PREFIX, --prefix PREFIX
                        set the prefix for raw string (default: pStr)
```

## How to build and upload

```bash
python setup.py bdist_wheel --universal
twine upload dist/*
```

## Test on local machine

```bash
python setup.py install
```