from canonical_curve_geometry import irregular_grid_geometry

def test_linear_function_has_zero_curvature_on_irregular_grid():
    x=[0,0.25,0.5,1.0,2.0,5.0]
    y=[3*v+7 for v in x]
    g=irregular_grid_geometry(x,y)
    assert all(abs(v-3.0)<1e-12 for v in g.interval_slopes)
    assert all(abs(v)<1e-12 for v in g.interior_curvatures)

def test_quadratic_function_has_constant_second_derivative():
    x=[0,0.25,0.5,1.0,1.5,3.0,5.0]
    y=[2*v*v+4*v+1 for v in x]
    g=irregular_grid_geometry(x,y)
    assert all(abs(v-4.0)<1e-12 for v in g.interior_curvatures)

def test_reject_non_increasing_grid():
    try:
        irregular_grid_geometry([0,1,1],[0,1,2])
        assert False
    except ValueError:
        pass
