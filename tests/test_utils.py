import json

import pytest

from addok.batch import process_documents
from addok.core import search, Result
from addok.ds import get_document
from addok.helpers.text import Token
from addok_spain.utils import (clean_query, extract_address, flag_housenumber,
                                fold_ordinal, glue_ordinal, make_labels,
                                remove_leading_zeros)


@pytest.mark.parametrize("input,expected", [
    ("Calle Cervantes, 4, 46120 Alboraia",
     "Calle Cervantes, 4, 46120 Alboraia"),
])
def test_clean_query(input, expected):
    assert clean_query(input) == expected


@pytest.mark.parametrize("input,expected", [
    ("Miguel de Cervantes Calle Cervantes, 4, 46120 Alboraia",
     "Calle Cervantes, 4, 46120 Alboraia"),
])
def test_extract_address(input, expected):
    assert extract_address(input) == expected


@pytest.mark.parametrize("inputs,expected", [
    (['6', 'b'], ['6b']),
    (['6'], ['6']),
    (['calle', '600', 'b'], ['calle', '600b']),
])
def test_glue_ordinal(inputs, expected):
    tokens = [Token(input_) for input_ in inputs]
    assert list(glue_ordinal(tokens)) == expected


@pytest.mark.parametrize("inputs,expected", [
    (['6'], False),
    (['calle', '6'], False),
    (['calle', 'baja', '93031'], False),  # postcode
    (['calle', 'baja', '6'], True),
    (['calle', 'baja', '60b'], True),
    (['calle', 'baja', '600t'], True),
    (['calle', 'baja', '6', '33000', 'Ciu'], True),
    (['c', 'de', 'roro', '614'], True),
    ([], False),  # Case of an empty string after clean query. Should not fail.
])
def test_flag_housenumber(inputs, expected):
    tokens = [Token(input_) for input_ in inputs]
    tokens = list(flag_housenumber(tokens))
    assert tokens == inputs
    token = next(filter(lambda token: token[0] == '6', tokens or []), None)
    assert ((token and token.kind) == 'housenumber') == expected


# @pytest.mark.parametrize("input,expected", [
#     ('60bis', '60b'),
# ])
# def test_fold_ordinal(input, expected):
#     assert fold_ordinal(Token(input)) == expected


@pytest.mark.parametrize("input,expected", [
    ('03', '3'),
    ('00009', '9'),
    ('02230', '02230'),  # Do not affect postcodes.
    ('0', '0'),
])
def test_remove_leading_zeros(input, expected):
    assert remove_leading_zeros(input) == expected


def test_index_housenumbers_use_processors(config):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'street',
        'name': 'calle des Lilas',
        'city': 'Paris',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '1 b': {
                'lat': '48.325451',
                'lon': '2.25651'
            }
        }
    }
    process_documents(json.dumps(doc))
    stored = get_document('d|yyyy')
    assert stored['housenumbers']['1b']['raw'] == '1 b'


@pytest.mark.parametrize("input,expected", [
    ('calle 1 de mayo, troyes', False),
    ('calle 1 de mayo, 1, troyes', '1'),
    ('calle 1 de mayo, 3, troyes', '3'),
    ('calle 1 de mayo, 3 b, troyes', '3 b'),
    ('calle 1 de mayo, 3, 33000 troyes', '3'),
    ('calle 1 de mayo, 3 b, 33000 troyes', '3 b'),
    ('c 1 de mayo, 3 b, troyes', '3 b'),
    ('c 1 de mayo, 3b, troyes', '3 b'),
])
def test_match_housenumber(input, expected):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'street',
        'name': 'calle 1 de mayo',
        'city': 'Troyes',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '3': {
                'lat': '48.325451',
                'lon': '2.25651'
            },
            '3 b': {
                'lat': '48.325451',
                'lon': '2.25651'
            },
            '1': {
                'lat': '48.325451',
                'lon': '2.25651'
            },
        }
    }
    process_documents(json.dumps(doc))
    result = search(input)[0]
    assert (result.type == 'housenumber') == bool(expected)
    if expected:
        assert result.housenumber == expected


def test_match_housenumber_with_multiple_tokens(config):
    config.SYNONYMS = {'18': 'dix huit'}
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'street',
        'name': 'calle 1 de mayo',
        'city': 'Troyes',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '1': {
                'lat': '48.8',
                'lon': '2.25651'
            },
            '10': {
                'lat': '48.10',
                'lon': '2.25651'
            },
            '18': {
                'lat': '48.18',
                'lon': '2.25651'
            },
        }
    }
    process_documents(json.dumps(doc))
    result = search('calle 1 de mayo, 1')[0]
    assert result.housenumber == '1'
    assert result.lat == '48.8'
    result = search('calle 1 de mayo, 10')[0]
    assert result.housenumber == '10'
    assert result.lat == '48.10'
    result = search('calle 1 de mayo, 18')[0]
    assert result.housenumber == '18'
    assert result.lat == '48.18'


def test_make_labels(config):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'street',
        'name': 'calle des Lilas',
        'city': 'Paris',
        'postcode': '75010',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '1 b': {
                'lat': '48.325451',
                'lon': '2.25651'
            }
        }
    }
    process_documents(json.dumps(doc))
    result = Result(get_document('d|yyyy'))
    result.housenumber = '1 b'  # Simulate match_housenumber
    make_labels(None, result)
    assert result.labels == [
        'calle des Lilas, 1 b, 75010 Paris',
        'calle des Lilas, 75010 Paris',
        'calle des Lilas, 1 b, 75010',
        'calle des Lilas, 75010',
        'calle des Lilas, 1 b, Paris',
        'calle des Lilas, Paris',
        'calle des Lilas, 1 b',
        'calle des Lilas'
    ]


def test_make_municipality_labels(config):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'municipality',
        'name': 'Lille',
        'city': 'Lille',
        'postcode': '59000',
        'lat': '49.32545',
        'lon': '4.2565',
    }
    process_documents(json.dumps(doc))
    result = Result(get_document('d|yyyy'))
    make_labels(None, result)
    assert result.labels == [
        'Lille',
        '59000 Lille',
        'Lille 59000',
    ]
