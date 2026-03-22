import pytest
import numpy as np
import neutral_density as nd


def test_dummy():
    """Are internal tests working?"""
    assert 1 == 1


def imports():
    """Are the data files importing?"""
    nd.init_fdt()
