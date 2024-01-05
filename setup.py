from setuptools import setup
from setuptools import find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(name='cjtool',
      version='0.29.1',
      description='Provide some tools in C++ development',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://github.com/Junch/cjtool',
      author='Jun Chen',
      author_email='junc76@gmail.com',
      license='MIT',
      install_requires=['colorama', 'pyperclip', 'pexpect', 'pykd', 'PyYAML',
                        'sourceline', 'PyQt5','qscintilla'],
      packages=find_packages(exclude=['test', 'test_projects']),
      include_package_data=True,
      package_data = {'': ['image/*.png', 'font/*.ttf']},
      entry_points={
          'console_scripts':
          ['stringrep = cjtool.stringtool:main',
           'ct = cjtool.cdbtool:main',
           'cm = cjtool.monitor:main',
           'ci = cjtool.indent:main',
           'cs = cjtool.search:main'
           ],
          'gui_scripts':
          ['codebook = cjtool.codebook:main']
      },
      zip_safe=False)
