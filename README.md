# neutral_density

*a direct translation of Jackett’s neutral density Fortran suite into Python*

This package solves the issue of calculating the neutral density oceanographic variable in Python. Other options include running the routines in the original [Fortran or MATLAB](https://www.teos-10.org/preteos10_software/neutral_density.html), or in Python via f2py. This translation owes much to the [implementation](https://github.com/guidov/pygamman_f2py) of the latter by Guido Vettoretti, and adopts its general organization. The goal of this package is to expand the accessibility and repeatability of these routines and ease their integration into other scientific Python applications and packages. 

This is a work in progress. Please reach out with any comments or suggestions!


## Setup

Clone to your machine.  Ensure pip and python are installed in a virtual environment (we suggest [this method](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)). Install by navigating to the unzipped directory and running the following command in a terminal emulator

```bash
python -m pip install -e .
```

This work is not yet available via conda-forge or pypy, but this is a target for future development if interest warrants.

## Use

The first thing to do before using `neutral_density` is import the required Fortran data tables:

```python
import neutral_density as nd 
init_fdt(llp_path="path/to/llp.fdt", stga_path="path/to/stga.fdt")
```

Within the package, they may be found at `neutral_density/src/neutral_density/`. 

## Citation

Users wishing to cite this Python translation may temporarily (until a proper repository citation is created) use:

> Sandborn, Daniel E. 2026. neutral_density: a direct translation of Jackett’s neutral density Fortran suite into Python. 

Users wishing to cite the original neutral density work should cite:

> Jackett, David R., Trevor J. McDougall, 1997: A Neutral Density Variable for the World's Oceans. J. Phys. Oceanogr., 27, 237–263. doi: 10.1175/1520-0485(1997)0272.0.CO;2

## Disclaimer

The material embodied in this software is provided to you "as-is" and without warranty of any kind, express, implied or otherwise, including without limitation, any warranty of fitness for a particular purpose.In no event shall the authors be liable to you or anyone else for any direct, special, incidental, indirect or consequential damages of any kind, or any damages whatsoever, including without limitation, loss of profit, loss of use, savings or revenue, or the claims of third parties, whether or not the authors have been advised of the possibility of such loss, however caused and on any theory of liability, arising out of or in connection with the possession, use or performance of this software.
