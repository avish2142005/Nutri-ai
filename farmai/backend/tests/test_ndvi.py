"""Unit tests for NDVI vegetation index calculations and edge cases.
"""
import numpy as np


def compute_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red) with zero-division guard and clipping."""
    denominator = nir + red
    # Guard against divide by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(denominator > 1e-6, (nir - red) / denominator, 0.0)
    # Clip to valid range [-1.0, 1.0]
    ndvi = np.clip(ndvi, -1.0, 1.0)
    return ndvi


def test_ndvi_known_expected_values():
    """Test NDVI calculation against known algebraic values."""
    # Healthy vegetation: high NIR, low Red
    nir = np.array([0.8, 0.6, 0.5])
    red = np.array([0.1, 0.2, 0.1])
    # Expected: (0.8-0.1)/(0.8+0.1) = 0.7/0.9 = 0.7777...
    expected = (nir - red) / (nir + red)
    calculated = compute_ndvi(nir, red)
    np.testing.assert_allclose(calculated, expected, rtol=1e-5)


def test_ndvi_zero_denominator_guard():
    """Test that zero NIR and zero Red safely yields 0.0 without crash or NaN."""
    nir = np.array([0.0, 0.0])
    red = np.array([0.0, 0.0])
    calculated = compute_ndvi(nir, red)
    assert not np.isnan(calculated).any()
    assert (calculated == 0.0).all()


def test_ndvi_clipping():
    """Test that extreme or invalid values are strictly clipped between -1.0 and 1.0."""
    nir = np.array([1.5, 0.0])
    red = np.array([0.0, 1.5])
    calculated = compute_ndvi(nir, red)
    assert (calculated <= 1.0).all()
    assert (calculated >= -1.0).all()
