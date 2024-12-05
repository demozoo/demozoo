import re
import unicodedata
import markdown

from django.utils.html import strip_tags
from django.utils.safestring import mark_safe


def slugify_tag(value):
    """
    A version of django.utils.text.slugify that lets '.' characters through.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s\.-]', '', value).strip().lower()
    return mark_safe(re.sub(r'[-\s]+', '-', value))


def generate_search_title(s):
    # strip accents
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c))

    # normalise $ to S (special case for T$ at Saga Musix's insistence ;-) )
    s = s.replace('$', 's')

    # replace punctuation with spaces
    s = ''.join((' ' if unicodedata.category(c)[0] == 'P' else c) for c in s)

    # condense multiple spaces to single space; strip leading/trailing space; downcase
    s = re.sub(r'\s+', ' ', s).strip().lower()

    return s


def generate_sort_key(s):
    s = generate_search_title(s)

    # pad numbers with leading zeros
    s = re.sub(r'\d+', lambda m: '%09d' % (int(m.group(0))), s)

    # move "the" / "a" / "an" to the end
    s = re.sub(r'^(the|a|an)\s+(.*)$', r'\2 \1', s)

    return s


def strip_music_extensions(s):
    original_title = s
    # strip suffixes
    s = re.sub(r'\.(mod|gz)$', '', s, flags=re.I)
    # strip prefixes
    s = re.sub(
        r'^(mod|ahx|okt|med|dbm|stm|bp|mkii|tfmx|abk|aon|ay|bp3|bss|digi|dm1|dm2|dmu|dw|emod|fc13|fc14|fp|fred|gmc|hip|hipc|hvl|iff|jam|jcb|ml|mmd0|mmd1|mon|oss|psid|puma|qc|raw|rk|s3m|sa|sfx|sid1|sid2|smus|spl|ss|sun|tme|wav|xm)\.',  # noqa
        '', s, flags=re.I
    )

    # revert to original title if there's nothing left
    return s if s.strip() else original_title


md = markdown.Markdown(extensions=['nl2br'])


def strip_markup(str):
    return strip_tags(md.convert(str))
