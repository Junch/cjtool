from setuptools import setup
from setuptools import find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(name='cjtool',
      version='0.18',
      description='Provide some tools in C++ development',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://github.com/Junch/cjtool',
      author='Jun Chen',
      author_email='junc76@gmail.com',
      license='MIT',
      install_requires=['colorama', 'pyperclip', 'pexpect'],
      packages=find_packages(exclude=['test']),
      entry_points={
          'console_scripts':
          ['stringrep = cjtool.stringtool:main', 'ct = cjtool.debugtool:main'],
      },
      zip_safe=False)
