"""Setup.py script for the ebcpy-framework"""

import setuptools

# read the contents of your README file
from pathlib import Path
readme_path = Path(__file__).parent.joinpath("README.md")
long_description = readme_path.read_text()

EXTRAS_REQUIRE = {
    'full': [
        'openpyxl>=3.0.5',
        'xlrd>=2.0.1',
        'pymoo>=0.4.2',
    ]
}

INSTALL_REQUIRES = [
    'numpy>=1.19.5',
    'matplotlib>=3.3.4',
    'scipy>=1.5.4',
    'pandas>=1.1.5',
    'tables>=3.6.1',
    'scikit-learn>=0.24.2',
    'fmpy>=0.2.27',
    'pydantic>=1.8.2',
    'h5py>=3.1.0'
]
SETUP_REQUIRES = INSTALL_REQUIRES.copy()  # Add all open-source packages to setup-requires

setuptools.setup(
    name='ebcpy',
    version='0.2.2',
    description='Python Library used for different python modules'
                ' for the analysis and optimization of energy systems, '
                'buildings and indoor climate ',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RWTH-EBC/ebcpy',
    download_url='https://github.com/RWTH-EBC/ebcpy/archive/refs/tags/0.2.2.tar.gz',
    license='BSD 3-Clause',
    author='RWTH Aachen University, E.ON Energy Research Center, Institute '
           'of Energy Efficient Buildings and Indoor Climate',
    author_email='fabian.wuellhorst@eonerc.rwth-aachen.de',
    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    keywords=[
        'simulation', 'building', 'energy',
        'time-series-data', 'comfort',
        'black-box optimization'
    ],
    packages=setuptools.find_packages(exclude=['img']),
    extras_require=EXTRAS_REQUIRE,
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
)
