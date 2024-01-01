import re

TYPES = [
    "acceso",
    "acera",
    "alameda",
    "aldapa",
    "aldea",
    "alqueria",
    "alto",
    "andador",
    "angosta",
    "apartamentos",
    "apartaments",
    "arrabal",
    "arroyo|arro",
    "atzucat",
    "autopista",
    "auzo",
    "avenida|av|avd|avda|ava",
    "avinguda",
    "baixada",
    "bajada",
    "barranco",
    "barreduela",
    "barrio|bo",
    "belena",
    "bide",
    "bulevar|blvr",
    "calexon",
    "calle|c|cl",
    "callizo",
    "calzada",
    "camino|co",
    "camino alto|coa",
    "camino bajo|cob",
    "camino viejo|cov",
    "campa",
    "canada",
    "canal",
    "canton",
    "carrer",
    "carril",
    "caserio",
    "cerro",
    "circunvalacion",
    "colonia",
    "complejo",
    "conjunto",
    "corralo",
    "corredera",
    "corredoira",
    "corrillo",
    "corriol",
    "cortijo",
    "costa",
    "cuesta|cta",
    "drecera",
    "enparantza",
    "entrada",
    "escalera",
    "espalda",
    "estrada",
    "etxadi",
    "explanada",
    "extramuros",
    "extrarradio|extr",
    "finca",
    "galeria",
    "glorieta|gta",
    "gran via",
    "grupo",
    "ibilbide",
    "illa",
    "jardin",
    "kalea",
    "karrera",
    "ladera",
    "leku",
    "loma",
    "lugar",
    "malecon",
    "mazo",
    "moll",
    "monte",
    "muelle",
    "pago",
    "paraje",
    "paratge",
    "parque",
    "particular",
    "paseo|po",
    "paseo alto|poa",
    "paseo bajo|pob",
    "pista",
    "placa",
    "placeta",
    "playa",
    "plaza|pza|pl|plza",
    "plazoleta",
    "plazuela",
    "poblado",
    "poligono",
    "pracina",
    "praia",
    "prolongacion",
    "puente|pte",
    "puerto",
    "pujada",
    "raco",
    "ramal",
    "rambla|rbla",
    "rampa",
    "raval",
    "ribera|riba",
    "riera",
    "rincon",
    "rinconada",
    "ronda|rda",
    "rotonda|rot",
    "rua",
    "rueiro",
    "ruela",
    "sector",
    "sendero",
    "serventia",
    "subida",
    "talde",
    "torrent",
    "transito",
    "transversal",
    "trasera",
    "travesia|tra",
    "travessera",
    "travessia",
    "urbanizacion",
    "vega",
    "veinat",
    "venela",
    "vereda|vera|vda",
    "via",
    "xardin",
    "zearkaleta",
    "zona",
]
TYPES_REGEX = "|".join(TYPES)
ORDINAL_REGEX = "[a-z]"

FOLD = {
    # "bis": "b",
    # "ter": "t",
    # "quater": "q",
    # "quinquies": "c",
    # "sexies": "s",
}

# Try to match address pattern when the search string contains extra info (for
# example "22 rue des Fleurs 59350 Lille" will be extracted from
# "XYZ Ets bâtiment B 22 rue des Fleurs 59350 Lille Cedex 23").
EXTRACT_ADDRESS_PATTERN = re.compile(
    "(" + TYPES_REGEX + ")"
    + r"\b.*"
    + r"(\d{1,4}(\b" + ORDINAL_REGEX + r")?),?"
    + r"\b(\d{5})?.*",
    flags=re.IGNORECASE,
)

# Match "bis", "ter", "b", etc.
ORDINAL_PATTERN = re.compile(r"\b(" + ORDINAL_REGEX + r")\b", flags=re.IGNORECASE)

# Match "rue", "boulevard", "bd", etc.
TYPES_PATTERN = re.compile(r"\b(" + TYPES_REGEX + r")\b", flags=re.IGNORECASE)


# Match number + ordinal, once glued by glue_ordinal (or typed like this in the
# search string, for example "6bis", "234ter").
FOLD_PATTERN = re.compile(r"^(\d{1,4})(" + ORDINAL_REGEX + ")$", flags=re.IGNORECASE)


# Match number once cleaned by glue_ordinal and fold_ordinal (for example
# "6b", "234t"…)
NUMBER_PATTERN = re.compile(r"\b\d{1,4}[a-z]?\b", flags=re.IGNORECASE)

CLEAN_PATTERNS = (
    (r"\.?ª", "a"),
    (r"\.?º", "o"),
    (r"([\d]{5})", r" \1 "),
    (r"\d{,2}(a) (planta|piso)", ""),
    (r" {2,}", " "),
    (r"(^| )c\.?/", " calle"),
)
CLEAN_COMPILED = list(
    (re.compile(pattern, flags=re.IGNORECASE), replacement)
    for pattern, replacement in CLEAN_PATTERNS
)


def clean_query(q):
    for pattern, repl in CLEAN_COMPILED:
        q = pattern.sub(repl, q)
    q = q.strip()
    return q


def extract_address(q):
    m = EXTRACT_ADDRESS_PATTERN.search(q)
    return m.group() if m else q


def neighborhood(iterable, first=None, last=None):
    """
    Yield the (previous, current, next) items given an iterable.

    You can specify a `first` and/or `last` item for bounds.
    """
    iterator = iter(iterable)
    previous = first
    try:
        current = next(iterator)  # Throws StopIteration if empty.
    except StopIteration:
        pass
    else:
        for next_ in iterator:
            yield (previous, current, next_)
            previous = current
            current = next_
        yield (previous, current, last)


def glue_ordinal(tokens):
    previous = None
    for _, token, next_ in neighborhood(tokens):
        if next_ and token.isdigit() and NUMBER_PATTERN.match(token):
            if previous is not None:
                yield previous
            previous = token
            continue
        if previous is not None:
            # Matches "bis" either followed by a type or nothing.
            if ORDINAL_PATTERN.match(token):
                raw = "{} {}".format(previous, token)
                # Space removed to maximize chances to get a hit.
                token = previous.update(raw.replace(" ", ""), raw=raw)
            else:
                # False positive.
                yield previous
            previous = None
        yield token


def flag_housenumber(tokens):
    # Flag first number.
    found = False
    for previous, token, next_ in neighborhood(tokens):
        if (
            previous is not None
            and NUMBER_PATTERN.match(token)
            and not TYPES_PATTERN.match(previous)
            and previous not in ('a', 'n', 'le', 'numero', 'proyecto', 'sector', 'm', 'poligono', 'ma', 'cm')
            and (not next_ or next_ not in ('a', 'de', 'del', 'el'))
            and not found
        ):
            token.kind = "housenumber"
            found = True
        yield token


def fold_ordinal(s):
    """3bis => 3b."""
    if s[0].isdigit() and not s.isdigit():
        try:
            number, ordinal = FOLD_PATTERN.findall(s)[0]
        except (IndexError, ValueError):
            pass
        else:
            s = s.update("{}{}".format(number, FOLD.get(ordinal.lower(), ordinal)))
    return s


def remove_leading_zeros(s):
    """0003 => 3."""
    # Limit digits from 1 to 3 in order to avoid processing postcodes.
    return re.sub(r"\b0+(\d{1,3})\b", "\g<1>", s, flags=re.IGNORECASE)


def make_labels(helper, result):
    if result.labels:
        return
    housenumber = getattr(result, "housenumber", None)

    def add(labels, label):
        labels.insert(0, label)

    city = result.city
    postcode = result.postcode
    names = result._rawattr("name")
    if not isinstance(names, (list, tuple)):
        names = [names]
    for name in names:
        labels = []
        label = name
        if postcode and result.type == "municipality":
            add(labels, "{} {}".format(label, postcode))
            add(labels, "{} {}".format(postcode, label))

        add(labels, label)
        if housenumber:
            add(labels, "{}, {}".format(label, housenumber))

        if city and city != label and city + '/' not in label and '/' + city not in label :
            add(labels, "{}, {}".format(label, city))
            if housenumber:
                add(labels, "{}, {}, {}".format(label, housenumber, city))

            if postcode:
                add(labels, "{}, {}".format(label, postcode))
                if housenumber:
                    add(labels, "{}, {}, {}".format(label, housenumber, postcode))
                add(labels, "{}, {} {}".format(label, postcode, city))
                if housenumber:
                    add(labels, "{}, {}, {} {}".format(label, housenumber, postcode, city))
        result.labels.extend(labels)
