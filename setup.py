from setuptools import setup
from setuptools import find_packages

setup(name='cjtool',
    version='0.14',
    description='Provide some tools in C++ development',
    url='http://github.com/Junch/cjtool',
    author='Jun Chen',
    author_email='junc76@gmail.com',
    license='MIT',
    install_requires=[
        'colorama',
        'pyperclip'
    ],
    packages=find_packages(exclude=['test']),
    entry_points={
        'console_scripts': [
            'stringrep = cjtool.stringtool:main'
        ],
    },
    zip_safe=False)