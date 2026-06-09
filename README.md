# neutral-density

[![Python package](https://github.com/d-sandborn/neutral-density/actions/workflows/python-package.yml/badge.svg)](https://github.com/d-sandborn/neutral-density/actions/workflows/python-package.yml) 
[![DOI](https://zenodo.org/badge/DOI/TBD.svg)](https://doi.org/TBD)

*a direct translation of Jackett's neutral density Fortran suite into Python*

This package solves the issue of calculating the neutral density oceanographic variable in Python. Other options include running the routines in the original [Fortran or MATLAB](https://www.teos-10.org/preteos10_software/neutral_density.html) published by D. Jackett & T. McDougall, or in Python via f2py like the [implementation](https://github.com/guidov/pygamman_f2py) by G. Vettoretti. The goal of this package is to expand the accessibility and repeatability of these routines and ease their integration into other scientific Python applications and packages. 

Please reach out with any comments or suggestions!

## Setup

### pip

```bash
pip install neutral-density
```

### conda

This work is not yet available via conda-forge , but that is a target for future development if interest warrants it. To install in a conda or mamba environment, continue with the local install, below, making sure to install all requirements before pip installation to avoid pip/conda conflicts. 

### local install

Clone to your machine.  Ensure pip, python, and all requirements are installed in a virtual environment (we suggest [this method](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)). Install by navigating to the unzipped directory and running the following command in a terminal emulator

```bash
python -m pip install -e .
```

## Summary of Functions

Main Module:

>`neutral_density.gamma_n()` calculates neutral densities for casts.
>
>`neutral_density.neutral_surfaces()` calculates neutral surfaces for casts.

Transect Module:

>`neutral_density.transect.read_goship_hy1()` imports a standard transect hydrofile.
>
>`neutral_density.transect.gamma_transect()` calculates neutral densities along a transect.
>
>`neutral_density.transect.neutral_surface_transect()` calculates neutral surfaces along a transect.


## Calculate neutral densities for casts

```python
import neutral_density as nd 

gamma, _, _ = nd.gamma_n(s = 35, t = 25, p = 10, along = 0, alat = 0)

gamma
>>> array([23.3304653])
```

Arguments to `gamma_n` must be for a single location or cast. They may be given as a single scalar value (float or int), or an array given as a list or Numpy array containing a series of values. `gamma_n` returns a tuple of three objects: an array of neutral densities, an array of lower gamma estimates, and an array of higher gamma estimates. Call `?gamma_n` for more information in its docstring. 

### `gamma_n` input arguments

| Parameter | Type | Units / Scale | Description |
| :--- | :--- | :--- | :--- |
| **`s`** | Array-like | psu (IPSS-78) | Salinity (practical) |
| **`t`** | Array-like | °C (IPTS-68) | In-situ temperature. |
| **`p`** | Array-like | db | Pressure (decibar). |
| **`along`** | Scalar | 0 to 360 | Longitude of the cast. |
| **`alat`** | Scalar | -80 to 64 | Latitude of the cast. |

### `gamma_n` returns

| Return Value | Type | Units | Description |
| :--- | :--- | :--- | :--- |
| **`gamma`** | 1D Array | kg m⁻³ | Neutral density values for the cast. |
| **`dg_lo`** | 1D Array | kg m⁻³ | Lower gamma error estimates. |
| **`dg_hi`** | 1D Array | kg m⁻³ | Upper gamma error estimates. |

> [!IMPORTANT]
> - **`-99.0`**: Algorithm failed to converge.
> - **`-99.1`**: Input data (S, T, or P) is outside the valid range of the equation of state.

> [!NOTE]
> Hydrographic parameters (`s`, `t`, `p`) must be the same length. Coordinates (`along`, `alat`) must be scalars. The function always returns 1D arrays, even for single-bottle inputs.

## Calculate neutral surfaces for casts

```python
s_ns = [34.0, 34.6, 34.7]

t_ns = [10.9, 2.3, 1.4]

p_ns = [260.1, 1953.1, 2943.4]

gamma_ns = nd.gamma_n(s_ns, t_ns, p_ns, 0, 0)[0]

gamma_ns
>>> array([26.07631029, 27.87443968, 28.10031321])

nd.neutral_surfaces(s_ns, t_ns, p_ns, gamma_ns, 28)

>>> (array([34.65640222]),
     array([1.79207646]),
     array([2511.65118682]),
 	 array([0.]),
 	 array([0.]),
 	 array([0.]))
```

Given a cast with S, T, P, and neutral densities, the S, T, and P at user-specified neutral densities can be interpolated with `neutral_surfaces`. This function returns six arrays: salinity on the neutral density surfaces, in situ temperature on the surfaces, pressure on the surfaces, surface salinity errors, surface temperature errors, and surface pressure errors.

### `neutral_surfaces` input arguments

| Parameter | Type | Units / Scale | Description |
| :--- | :--- | :--- | :--- |
| **`s`** | Array-like | psu (IPSS-78) | Salinity cast data. |
| **`t`** | Array-like | °C (IPTS-68) | In situ temperature. |
| **`p`** | Array-like | db | Pressure (decibar). |
| **`gamma`** | Array-like | kg m⁻³ | Neutral density values from `gamma_n`. |
| **`glevels`** | Array-like | kg m⁻³ | Target neutral density surfaces to locate. |

### `neutral_surfaces` returns

| Return Value | Type | Description |
| :--- | :--- | :--- |
| **`sns`**, **`tns`**, **`pns`** | 1D Arrays | S, T, and P interpolated onto the target surfaces. |
| **`dsns`**, **`dtns`**, **`dpns`** | 1D Arrays | Error estimates (non-zero indicates multiple crossings). |

> [!TIP]
> Output values of `-99.0` indicate the surface outcropped or undercropped the cast. Like `gamma_n`, this function always returns 1D NumPy arrays for consistency.

## Calculate neutral densities and surfaces along a transect

The `transect` submodule extends `gamma_n` and `neutral_surfaces` to operate
on an entire GO-SHIP section loaded from a WHP-Exchange `.hy1` bottle file.
All three functions return plain pandas DataFrames.

```python
import numpy as np
from neutral_density import transect as tx

# Parse the hydrofile
df = tx.read_goship_hy1("33RO20131223_hy1.csv")

# Compute γn for every bottle — returns a long-format DataFrame
gamma_df = tx.gamma_transect(df)

# Find neutral surfaces — pass gamma_df to skip recomputing γn
glevels = np.arange(26.0, 28.5, 0.1)
surf_df = tx.neutral_surface_transect(gamma_df, glevels)
```

Both transect functions also accept a file path directly, so the two-step
parse-then-compute pattern is optional:

```python
gamma_df = tx.gamma_transect("33RO20131223_hy1.csv")
surf_df  = tx.neutral_surface_transect("33RO20131223_hy1.csv", glevels)
```

### `read_goship_hy1(filepath, fill_value=-999, max_flag=2, sort_pressure=True)`

Parses a WHP-Exchange `.hy1` file into a clean DataFrame. Replaces −999 fill
values with `NaN`, drops bottles where `CTDSAL_FLAG_W > max_flag`, sorts each
cast by increasing pressure, and appends a `longitude_360` column (−180→+180
converted to 0→360) so `gamma_n` receives the longitude convention it expects.

### `gamma_transect(source, fill_value=-999, max_flag=2, its90_correction=True, verbose=True)`

Iterates cast-by-cast over the section, calling `gamma_n` for each one.
Returns a **long-format DataFrame** with one row per bottle:

| Column | Units | Description |
| :--- | :--- | :--- |
| `station`, `cast` | — | Station and cast numbers from the hydrofile. |
| `latitude`, `longitude` | °N, °E | Cast position (longitude in −180→+180). |
| `pressure` | dbar | Bottle pressure. |
| `salinity` | psu | CTD salinity. |
| `temperature` | °C (IPTS-68) | In-situ temperature. |
| `gamma` | kg m⁻³ | Neutral density. −99.0 = algorithm failure; −99.1 = outside valid EOS range. |
| `gamma_lo`, `gamma_hi` | kg m⁻³ | Lower and upper γn uncertainty estimates. |

> [!NOTE]
> Modern GO-SHIP CTD temperatures are reported on the ITS-90 scale, but EOS-80
> (on which γn is defined) uses IPTS-68. The correction T₆₈ = 1.00024 × T₉₀
> is applied by default. Set `its90_correction=False` only if your temperatures
> are already on IPTS-68.

### `neutral_surface_transect(source, glevels, fill_value=-999, max_flag=2, its90_correction=True, verbose=True)`

Locates each target neutral density surface in every cast along the section.
`source` can be a file path, a DataFrame from `read_goship_hy1`, or the
output of `gamma_transect` — passing the latter avoids recomputing γn.
Returns a **long-format DataFrame** with one row per (surface, cast) pair:

| Column | Units | Description |
| :--- | :--- | :--- |
| `gamma_level` | kg m⁻³ | The target neutral density surface. |
| `station`, `cast` | — | Station and cast numbers. |
| `latitude`, `longitude` | °N, °E | Cast position. |
| `pressure` | dbar | Pressure where the surface intersects the cast. |
| `salinity` | psu | Salinity on the surface. |
| `temperature` | °C (IPTS-68) | In-situ temperature on the surface. |
| `d_pressure`, `d_salinity`, `d_temperature` | dbar, psu, °C | Uncertainty estimates; non-zero indicates a multiply-defined surface. |

Rows where a surface outcrops or undercrops a cast are present but have `NaN`
in the pressure, salinity, and temperature columns, so every cast appears at
every surface level. This makes pivoting and plotting straightforward:

```python
# Pressure section on a latitude × γn grid
pivot = surf_df.pivot(index="gamma_level", columns="latitude", values="pressure")
```

## Speed

For raw numerical execution, you won't easily beat Fortran. This package provides high-level Python accessibility while approaching Fortran speeds by using Numba just-in-time (JIT) compilation.

The first time `gamma_n` or `neutral_surfaces` is called, Numba compiles Python code into machine instructions optimized for your CPU. This creates a one-time overhead of several seconds. Further calls execute at near-Fortran speeds. Recompilation only occurs if the input data types change, which is prevented in most cases by wrappers that cast all input into float types. JIT compilation provides a performance boost for iterative (i.e. in loops) processing of large datasets without the complexity of manual C or Cython bindings -- though those could be a useful future project. 

## Citation

Users wishing to cite this Python translation use:

> Sandborn, Daniel E., Kelly, Colette L. 2026. neutral-density v2026.2: a direct translation of Jackett's neutral density Fortran suite into Python. doi: TBD

Users wishing to cite the original neutral density work should cite:

> Jackett, David R., Trevor J. McDougall, 1997: A Neutral Density Variable for the World's Oceans. J. Phys. Oceanogr., 27, 237–263. doi: 10.1175/1520-0485(1997)0272.0.CO;2

## Disclaimer

The material embodied in this software is provided to you "as-is" and without warranty of any kind, express, implied or otherwise, including without limitation, any warranty of fitness for a particular purpose. In no event shall the authors be liable to you or anyone else for any direct, special, incidental, indirect or consequential damages of any kind, or any damages whatsoever, including without limitation, loss of profit, loss of use, savings or revenue, or the claims of third parties, whether or not the authors have been advised of the possibility of such loss, however caused and on any theory of liability, arising out of or in connection with the possession, use or performance of this software.
