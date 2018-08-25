from distutils.core import setup
import py2exe

setup(console=['Pysetup.py'],
        options={
    'py2exe':{'packages':['random', 'pygame', 'functools', 'math', 'pickle', 'statistics', 'copy']}
})