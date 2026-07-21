from mimosa.base_model import create_base_model


def test_create_base_model_defines_shared_sets_and_inputs():
    """The extracted base model must retain every shared model declaration."""
    model = create_base_model()

    assert model.regions.isordered()
    for name in (
        "beginyear",
        "dt",
        "tf",
        "t",
        "year",
        "year2100",
        "regions",
        "population",
        "global_population",
        "baseline_GDP",
        "global_baseline_GDP",
        "ssp_baseline_emissions",
        "MAC_SSP_calibration_factor",
    ):
        assert hasattr(model, name)
