from setuptools import setup

setup(
    name='raven',
    version='0.0.1',
    description='Training CLI Tool',
    packages=['raven'],
    install_requires=[
        'Click',
    ],
    entry_points='''
      [console_scripts]
      raven=raven.cli:cli
    ''',
)
      