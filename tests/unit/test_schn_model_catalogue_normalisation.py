from scripts.check_schn_model_catalogue import normalise


def test_version_and_year_noise_are_removed() -> None:
    value = "Final Model SoCP for Obstetrics & Gynaecology v1.2 - 26 Sep 2023.pdf"
    assert normalise(value) == "obstetrics and gynaecology 26 sep"
