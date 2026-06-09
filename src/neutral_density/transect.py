"""
transect.py
-----------
Plug-in to the neutral_density module that extends gamma_n and
neutral_surfaces to operate on an entire GO-SHIP hydrographic section
loaded from a WHP-Exchange (.hy1) bottle-data CSV file.

Public API
----------
read_goship_hy1(filepath, fill_value, max_flag, sort_pressure)
    Parse and clean a WHP-Exchange .hy1 file into a tidy DataFrame.

gamma_transect(source, fill_value, max_flag, its90_correction, verbose)
    Compute neutral density γn for every quality-controlled bottle
    across all casts in the section.  Returns a long-format DataFrame
    with one row per bottle.

neutral_surface_transect(source, glevels, fill_value, max_flag,
                          its90_correction, verbose)
    Find where a set of neutral density surfaces intersect each cast.
    Returns a long-format DataFrame with one row per (surface, cast) pair.

Notes
-----
Temperature conversion
    Modern GO-SHIP CTD temperatures are reported on the ITS-90 scale,
    whereas EOS-80 (on which γn is based) is defined on IPTS-68.
    The correction  T_68 = 1.00024 × T_90  is applied by default and
    can be disabled with ``its90_correction=False``.

Longitude convention
    WHP-Exchange files use −180 → +180.  gamma_n requires 0 → 360.
    The conversion is applied internally.

Fill / flag handling
    WHP-Exchange missing values default to −999.  Bottles are retained
    only when CTDPRS, CTDTMP, and CTDSAL all carry quality flags ≤
    max_flag (default 2, i.e. "good").
"""

from __future__ import annotations

import warnings
from typing import Sequence

import numpy as np
import pandas as pd

try:
    from . import gamma_n, neutral_surfaces          # package usage
except ImportError:
    from neutral_density import gamma_n, neutral_surfaces  # direct usage

_WHP_FILL = -999.0
_ITS90_TO_IPTS68 = 1.00024  # T_IPTS68 = T_ITS90 * 1.00024
_MISS = -90.0                # sentinel threshold from neutral_surfaces


def read_goship_hy1(
    filepath: str,
    fill_value: float = _WHP_FILL,
    max_flag: int = 2,
    sort_pressure: bool = True,
) -> pd.DataFrame:
    """Parse a WHP-Exchange .hy1 bottle-data CSV into a clean DataFrame.

    Parameters
    ----------
    filepath : str
        Path to the .hy1 file (comma-separated, one header row).
    fill_value : float, optional
        Value used in the file for missing data (default -999).
    max_flag : int, optional
        Maximum acceptable WOCE quality flag for CTDSAL (default 2 = "good").
        Set to 3 to also accept "questionable but acceptable" data.
    sort_pressure : bool, optional
        If True (default), sort each cast by increasing pressure.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with fill values replaced by NaN and bottles
        with unacceptable quality flags removed.  A ``longitude_360``
        column is added (-180 to +180 converted to 0 to 360 for gamma_n).
    """
    df = pd.read_csv(filepath, index_col=0)
    df.columns = df.columns.str.strip()

    numeric_cols = df.select_dtypes(include="number").columns
    df[numeric_cols] = df[numeric_cols].replace(fill_value, np.nan)

    mask = (
        df["CTDPRS"].notna()
        & df["CTDTMP"].notna()
        & df["CTDSAL"].notna()
        & (df["CTDSAL_FLAG_W"] <= max_flag)
    )
    df = df[mask].copy()

    df["longitude_360"] = df["LONGITUDE"] % 360.0

    if sort_pressure:
        df = df.sort_values(["STNNBR", "CASTNO", "CTDPRS"])

    return df.reset_index(drop=True)


def gamma_transect(
    source: "str | pd.DataFrame",
    fill_value: float = _WHP_FILL,
    max_flag: int = 2,
    its90_correction: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """Compute neutral density gamma_n across a GO-SHIP hydrographic section.

    Parameters
    ----------
    source : str or pd.DataFrame
        A file path to a .hy1 file or a DataFrame from
        :func:`read_goship_hy1`.
    fill_value : float, optional
        WHP fill value (default -999).  Ignored if *source* is a DataFrame.
    max_flag : int, optional
        Maximum acceptable quality flag (default 2).  Ignored if *source*
        is a DataFrame.
    its90_correction : bool, optional
        If True (default), multiply CTDTMP by 1.00024 to convert ITS-90
        to IPTS-68 before passing to gamma_n.
    verbose : bool, optional
        Print a one-line progress message per cast.

    Returns
    -------
    pd.DataFrame
        Long-format DataFrame, one row per bottle, with columns:

        ``station``, ``cast``, ``latitude``, ``longitude``,
        ``pressure``, ``salinity``, ``temperature``,
        ``gamma``, ``gamma_lo``, ``gamma_hi``

        Values of -99.0 in gamma indicate algorithm failure; -99.1
        indicates the bottle is outside the valid EOS range.

    Examples
    --------
    >>> df = gamma_transect("33RO20131223_hy1.csv")
    >>> df.head()
    """
    if isinstance(source, str):
        df = read_goship_hy1(source, fill_value=fill_value, max_flag=max_flag)
    else:
        df = source.copy()

    rows = []

    for (stn, cst), grp in df.groupby(["STNNBR", "CASTNO"], sort=True):
        grp = grp.sort_values("CTDPRS")

        prs = grp["CTDPRS"].to_numpy(dtype=np.float64)
        tmp = grp["CTDTMP"].to_numpy(dtype=np.float64)
        sal = grp["CTDSAL"].to_numpy(dtype=np.float64)
        lat = float(grp["LATITUDE"].iloc[0])
        lon_360 = float(grp["longitude_360"].iloc[0])
        lon = float(grp["LONGITUDE"].iloc[0])

        valid = np.isfinite(prs) & np.isfinite(tmp) & np.isfinite(sal)
        prs, tmp, sal = prs[valid], tmp[valid], sal[valid]

        if len(prs) < 2:
            warnings.warn(
                f"Station {stn} cast {cst}: fewer than 2 valid bottles — skipping.",
                UserWarning, stacklevel=2,
            )
            continue

        if its90_correction:
            tmp = tmp * _ITS90_TO_IPTS68

        if verbose:
            print(
                f"  Station {int(stn):>4d}  cast {int(cst)}"
                f"  lat {lat:+7.3f}  lon {lon:+8.3f}"
                f"  n={len(prs):>3d} bottles",
                flush=True,
            )

        gamma, dg_lo, dg_hi = gamma_n(sal, tmp, prs, lon_360, lat)

        rows.append(pd.DataFrame({
            "station":     np.full(len(prs), stn),
            "cast":        np.full(len(prs), cst),
            "latitude":    np.full(len(prs), lat),
            "longitude":   np.full(len(prs), lon),
            "pressure":    prs,
            "salinity":    sal,
            "temperature": tmp,
            "gamma":       gamma,
            "gamma_lo":    dg_lo,
            "gamma_hi":    dg_hi,
        }))

    if verbose:
        print(f"\nDone. Processed {len(rows)} casts.")

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def neutral_surface_transect(
    source: "str | pd.DataFrame",
    glevels: "Sequence[float] | np.ndarray",
    fill_value: float = _WHP_FILL,
    max_flag: int = 2,
    its90_correction: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """Find neutral-density surfaces across a GO-SHIP hydrographic section.

    Parameters
    ----------
    source : str or pd.DataFrame
        A .hy1 file path, a pre-parsed DataFrame from
        :func:`read_goship_hy1`, or the output of :func:`gamma_transect`
        (which already contains a ``gamma`` column, avoiding redundant
        computation).
    glevels : sequence of float
        Target neutral density values [kg/m3], e.g. [27.5, 27.7, 27.9, 28.1].
    fill_value, max_flag, its90_correction, verbose
        Same as in :func:`gamma_transect`.  Ignored when *source*
        already contains a ``gamma`` column.

    Returns
    -------
    pd.DataFrame
        Long-format DataFrame, one row per (surface, cast) pair, with columns:

        ``gamma_level``, ``station``, ``cast``, ``latitude``, ``longitude``,
        ``pressure``, ``salinity``, ``temperature``,
        ``d_pressure``, ``d_salinity``, ``d_temperature``

        Rows where the surface outcrops or undercrops have NaN in the
        pressure/salinity/temperature columns.  Non-zero ``d_*`` values
        indicate a multiply-defined surface.

    Examples
    --------
    >>> import numpy as np
    >>> glevels = np.arange(26.0, 28.5, 0.1)
    >>> df = neutral_surface_transect("33RO20131223_hy1.csv", glevels)
    >>> df.dropna(subset=["pressure"]).head()

    Pass a pre-computed gamma_transect result to skip redundant gamma_n calls:

    >>> gamma_df = gamma_transect("33RO20131223_hy1.csv")
    >>> surf_df  = neutral_surface_transect(gamma_df, glevels)
    """
    glevels = np.asarray(glevels, dtype=np.float64)

    # If source already has gamma (output of gamma_transect), use it directly;
    # otherwise compute gamma first.
    if isinstance(source, pd.DataFrame) and "gamma" in source.columns:
        gamma_df = source
    else:
        if verbose:
            print("Computing gamma_n for all casts ...\n")
        gamma_df = gamma_transect(
            source,
            fill_value=fill_value,
            max_flag=max_flag,
            its90_correction=its90_correction,
            verbose=verbose,
        )

    if verbose:
        print("\nFinding neutral surfaces ...")

    rows = []

    for (stn, cst), grp in gamma_df.groupby(["station", "cast"], sort=True):
        grp = grp.sort_values("pressure")
        lat = float(grp["latitude"].iloc[0])
        lon = float(grp["longitude"].iloc[0])

        valid = grp["gamma"] > 0.0
        if valid.sum() < 2:
            warnings.warn(
                f"Station {stn} cast {cst}: fewer than 2 bottles with valid gamma_n"
                " — surfaces skipped.",
                UserWarning, stacklevel=2,
            )
            for glev in glevels:
                rows.append(_nan_row(glev, stn, cst, lat, lon))
            continue

        g = grp[valid]
        sns, tns, pns, dsns, dtns, dpns = neutral_surfaces(
            g["salinity"].to_numpy(dtype=np.float64),
            g["temperature"].to_numpy(dtype=np.float64),
            g["pressure"].to_numpy(dtype=np.float64),
            g["gamma"].to_numpy(dtype=np.float64),
            glevels,
        )

        if verbose:
            n_found = int(np.sum(pns > _MISS))
            print(
                f"  Station {int(stn):>4d}  {n_found}/{len(glevels)} surfaces found",
                flush=True,
            )

        for ig, glev in enumerate(glevels):
            if pns[ig] > _MISS:
                rows.append({
                    "gamma_level":   glev,
                    "station":       stn,
                    "cast":          cst,
                    "latitude":      lat,
                    "longitude":     lon,
                    "pressure":      pns[ig],
                    "salinity":      sns[ig],
                    "temperature":   tns[ig],
                    "d_pressure":    dpns[ig],
                    "d_salinity":    dsns[ig],
                    "d_temperature": dtns[ig],
                })
            else:
                rows.append(_nan_row(glev, stn, cst, lat, lon))

    return pd.DataFrame(rows)


def _nan_row(glev, stn, cst, lat, lon) -> dict:
    """Return a row dict with NaN for all surface properties."""
    return {
        "gamma_level":   glev,
        "station":       stn,
        "cast":          cst,
        "latitude":      lat,
        "longitude":     lon,
        "pressure":      np.nan,
        "salinity":      np.nan,
        "temperature":   np.nan,
        "d_pressure":    np.nan,
        "d_salinity":    np.nan,
        "d_temperature": np.nan,
    }