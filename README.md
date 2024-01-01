# Addok plugin for Spain specifics

## Installation

    pip install addok-spain


## Configuration

- Add QUERY_PROCESSORS_PYPATHS

    QUERY_PROCESSORS_PYPATHS = [
        …,
        "addok_spain.extract_address",
        "addok_spain.clean_query",
    ]

- Add PROCESSORS_PYPATHS

    PROCESSORS_PYPATHS = [
        …,
        "addok_spain.glue_ordinal",
        "addok_spain.fold_ordinal",
        "addok_spain.flag_housenumber",
        …,
    ]

- Replace default `make_labels` by Spain dedicated one:

    SEARCH_RESULT_PROCESSORS_PYPATHS = [
        'addok_spain.make_labels',
        …,
    ]
