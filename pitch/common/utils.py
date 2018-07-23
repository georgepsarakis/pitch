from boltons.iterutils import is_collection
from boltons.urlutils import URL


def compose_url(base_url, url):
    base_url = URL(base_url)
    url = URL(url)
    if not url.scheme:
        absolute_url = base_url.navigate(url.to_text())
    else:
        absolute_url = url
    return absolute_url.to_text()


def identity(x):
    return x


def to_iterable(obj):
    if not is_collection(obj):
        return [obj]
    return obj


def merge_dictionaries(a, b):
    r = a.copy()
    for k, v in b.items():
        if k in r and isinstance(r[k], dict):
            r[k] = merge_dictionaries(r[k], v)
        else:
            r[k] = v
    return r
