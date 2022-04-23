from setuptools import setup
from setuptools import find_packages

setup(name='cjtool',
    version='0.01',
    description='Provide some tools in C++ development',
    url='http://github.com/storborg/funniest',
    author='Jun Chen',
    author_email='junc76@gmail.com',
    license='MIT',
    install_requires=[
        'colorama'
    ],
    packages=find_packages(exclude=['test']),
    entry_points={
        'console_scripts': [
            'stringrep = cjtool.stringtool:main'
        ],
    },
    zip_safe=False)