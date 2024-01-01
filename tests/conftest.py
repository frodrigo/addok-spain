def pytest_configure():
    from addok.config import config
    config.QUERY_PROCESSORS_PYPATHS = [
        "addok_spain.extract_address",
        "addok_spain.clean_query",
        "addok_spain.remove_leading_zeros",
    ]
    config.SEARCH_RESULT_PROCESSORS_PYPATHS = [
        'addok.helpers.results.match_housenumber',
        'addok_spain.make_labels',
        'addok.helpers.results.score_by_importance',
        'addok.helpers.results.score_by_autocomplete_distance',
        'addok.helpers.results.score_by_ngram_distance',
        'addok.helpers.results.score_by_geo_distance',
    ]
    config.PROCESSORS_PYPATHS = [
        "addok.helpers.text.tokenize",
        "addok.helpers.text.normalize",
        "addok_spain.glue_ordinal",
        "addok_spain.fold_ordinal",
        "addok_spain.flag_housenumber",
        "addok.helpers.text.synonymize",
    ]
