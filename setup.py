from setuptools import setup, find_packages

setup(
    name='midiUtils',
    version='0.1.4',
    author='Daniel Flores Garcia',
    author_email='danialefloresg@gmail.com',
    description='Used for drum gen project.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dafg05/midiutils',
    packages=find_packages(),
    install_requires=[
        "numpy",
        "mido"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.6',
)