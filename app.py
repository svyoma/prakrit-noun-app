from flask import Flask, request, render_template, jsonify
from aksharamukha import transliterate
import os

app = Flask(__name__)

# Helper functions

def detect_script(text):
    if any('\u0900' <= c <= '\u097F' for c in text):
        return 'Devanagari'
    return 'HK'

def transliterate_to_hk(text):
    return transliterate.process('Devanagari', 'HK', text) if detect_script(text) == 'Devanagari' else text

def transliterate_output(text, target):
    return transliterate.process('HK', target, text)

def remove_last_vowel(word):
    for i in reversed(range(len(word))):
        if word[i] in 'aeiou':
            return word[:i] + word[i+1:]
    return word

def replace_vowel(word, replacement, ending, is_a):
    if is_a and ending == 'a':
        return word.rsplit('a', 1)[0] + replacement
    elif ending in 'iu':
        new_vowel = replacement if replacement else ('I' if ending == 'i' else 'U')
        return word.rsplit(ending, 1)[0] + new_vowel
    return word

def replace_last_vowel(word, to):
    chars = list(word)
    for i in range(len(chars) - 1, -1, -1):
        if chars[i] in "aiuAIU":
            chars[i] = to
            break
    return ''.join(chars)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    word = request.form.get('word', '').strip()
    gender = request.form.get('gender', 'masculine')

    if not word:
        return jsonify({'error': 'Empty input'})

    word = transliterate_to_hk(word)
    ending = word[-1] if word else ''

    data = []
    skip_cases = set()

    if gender == 'neuter':
        no_vowel = remove_last_vowel(word)
        a_to_A = replace_vowel(word, 'A', ending, True)
        i_u_to_IU = replace_vowel(word, '', ending, False)

        def combine_plural(base):
            return [f"{base}iM", f"{base}i~", f"{base}Ni"]

        sg_M = f"{word}M"
        if ending == 'a':
            plural_base = a_to_A
        elif ending == 'i':
            plural_base = i_u_to_IU
        elif ending == 'u':
            plural_base = i_u_to_IU
        else:
            plural_base = word

        data.append({
            'case': 'First Case',
            'hk': {'sg': [sg_M], 'pl': combine_plural(plural_base)},
            'devanagari': {
                'sg': [transliterate_output(sg_M, 'Devanagari')],
                'pl': [transliterate_output(f, 'Devanagari') for f in combine_plural(plural_base)]
            }
        })

        data.append({
            'case': 'Second Case',
            'hk': {'sg': [sg_M], 'pl': combine_plural(plural_base)},
            'devanagari': {
                'sg': [transliterate_output(sg_M, 'Devanagari')],
                'pl': [transliterate_output(f, 'Devanagari') for f in combine_plural(plural_base)]
            }
        })

        gender = 'masculine'
        skip_cases = {'First Case', 'Second Case'}

    if gender == 'feminine':
        base_long, base_short, extra_a = '', '', False
        if ending == 'a':
            base_long = replace_last_vowel(word, 'A')
            base_short = replace_last_vowel(word, 'a')
        elif ending == 'A':
            base_long = word
            base_short = replace_last_vowel(word, 'a')
        elif ending == 'i':
            base_long = replace_last_vowel(word, 'I')
            base_short = replace_last_vowel(word, 'i')
        elif ending == 'I':
            base_long = word
            base_short = replace_last_vowel(word, 'i')
            extra_a = True
        elif ending == 'u':
            base_long = replace_last_vowel(word, 'U')
            base_short = replace_last_vowel(word, 'u')
        elif ending == 'U':
            base_long = word
            base_short = replace_last_vowel(word, 'u')
        else:
            base_long = base_short = word

        forms = [
            ("First Case",
             [base_long] if ending == 'A' else [base_long] + ([word + 'A'] if extra_a else []) if ending in 'iIuU' else [base_long, base_long + 'u', base_long + 'o'],
             [base_long, base_long + 'u', base_long + 'o'] if ending == 'A' else [base_long] + ([word + 'A'] if extra_a else []) + [base_long + 'u', base_long + 'o'] if ending in 'iIuU' else [base_long, base_long + 'u', base_long + 'o']),

            ("Second Case",
             [base_short + 'M'],
             [base_long, base_long + 'u', base_long + 'o'] if ending == 'A' else [base_long] + ([word + 'A'] if extra_a else []) + [base_long + 'u', base_long + 'o'] if ending in 'iIuU' else [base_long, base_long + 'u', base_long + 'o']),

            ("Third Case",
             [base_long + 'a', base_long + 'i', base_long + 'e'] if ending == 'A' else [base_long + 'a', base_long + 'A', base_long + 'i', base_long + 'e'],
             [base_long + 'hi', base_long + 'hiM', base_long + 'hi~']),

            ("Fourth Case",
             [base_long + 'a', base_long + 'i', base_long + 'e'] if ending == 'A' else [base_long + 'a', base_long + 'A', base_long + 'i', base_long + 'e'],
             [base_long + 'Na', base_long + 'NaM']),

            ("Fifth Case",
            [base_short + 'tto'] + [base_long + s for s in (['a', 'i', 'e', 'o', 'u', 'hinto'] if ending == 'A' else ['a', 'A', 'i', 'e', 'o', 'u', 'hinto'])],
            [base_short + 'tto', base_long + 'o', base_long + 'u', base_long + 'hinto', base_long + 'sunto']),

            ("Sixth Case",
             [base_long + 'a', base_long + 'i', base_long + 'e'] if ending == 'A' else [base_long + 'a', base_long + 'A', base_long + 'i', base_long + 'e'],
             [base_long + 'Na', base_long + 'NaM']),

            ("Seventh Case",
             [base_long + 'a', base_long + 'i', base_long + 'e'] if ending == 'A' else [base_long + 'a', base_long + 'A', base_long + 'i', base_long + 'e'],
             [base_long + 'su', base_long + 'suM']),
        ]

        for name, sg, pl in forms:
            data.append({
                'case': name,
                'hk': {'sg': sg, 'pl': pl},
                'devanagari': {
                    'sg': [transliterate_output(f, 'Devanagari') for f in sg],
                    'pl': [transliterate_output(f, 'Devanagari') for f in pl]
                }
            })
    else:
        no_vowel = remove_last_vowel(word)
        a_to_A = replace_vowel(word, 'A', ending, True)
        a_to_e = replace_vowel(word, 'e', ending, True)
        i_u_to_IU = replace_vowel(word, '', ending, False)

        def build_forms(suffixes):
            return [f"{b}{s}" for s, b in suffixes]

        cases = [
            ("First Case",
             [('o', no_vowel)] if ending == 'a' else [("", i_u_to_IU)] if ending in 'iu' else [],
             [("", a_to_A)] if ending == 'a' else [("a_u", no_vowel), ("ao", no_vowel), ("", i_u_to_IU), ("No", word)] if ending == 'i' else [("au", no_vowel), ("ao", no_vowel), ("", i_u_to_IU), ("No", word), ("avo", no_vowel)] if ending == 'u' else []),

            ("Second Case",
             [("M", word)],
             [("", a_to_A), ("", a_to_e)] if ending == 'a' else [(i_u_to_IU, ""), ("No", word)] if ending in 'iu' else []),

            ("Third Case",
             [("Na", a_to_e), ("NaM", a_to_e)] if ending == 'a' else [("NA", word)] if ending in 'iu' else [],
             [("hi", a_to_e), ("hiM", a_to_e), ("hi~", a_to_e)] if ending == 'a' else [("hi", i_u_to_IU), ("hiM", i_u_to_IU), ("hi~", i_u_to_IU)] if ending in 'iu' else []),

            ("Fourth Case",
             [("ssa", word)] if ending == 'a' else [("ssa", word), ("No", word)] if ending in 'iu' else [],
             [("Na", a_to_A), ("NaM", a_to_A)] if ending == 'a' else [("Na", i_u_to_IU), ("NaM", i_u_to_IU)] if ending in 'iu' else []),

            ("Fifth Case",
             [("tto", word), ("o", a_to_A), ("u", a_to_A), ("hi", a_to_A), ("hinto", a_to_A)] if ending == 'a' else [("tto", word), ("o", i_u_to_IU), ("u", i_u_to_IU), ("hinto", i_u_to_IU), ("No", word)] if ending in 'iu' else [],
             [("tto", word), ("o", a_to_A), ("u", a_to_A), ("hi", a_to_A), ("hi", a_to_e), ("hinto", a_to_A), ("hinto", a_to_e), ("sunto", a_to_A), ("sunto", a_to_e)] if ending == 'a' else [("tto", word), ("o", i_u_to_IU), ("u", i_u_to_IU), ("hinto", i_u_to_IU), ("sunto", i_u_to_IU)] if ending in 'iu' else []),

            ("Sixth Case",
             [("ssa", word)] if ending == 'a' else [("ssa", word), ("No", word)] if ending in 'iu' else [],
             [("Na", a_to_A), ("NaM", a_to_A)] if ending == 'a' else [("Na", i_u_to_IU), ("NaM", i_u_to_IU)] if ending in 'iu' else []),

            ("Seventh Case",
             [("e", no_vowel), ("mmi", word)] if ending == 'a' else [("mmi", word)] if ending in 'iu' else [],
             [("su", a_to_e), ("suM", a_to_e)] if ending == 'a' else [("su", i_u_to_IU), ("suM", i_u_to_IU)] if ending in 'iu' else []),
        ]

        for name, singular_suffixes, plural_suffixes in cases:
            if name in skip_cases:
                continue
            hk_sg = build_forms(singular_suffixes)
            hk_pl = build_forms(plural_suffixes)
            data.append({
                'case': name,
                'hk': {'sg': hk_sg, 'pl': hk_pl},
                'devanagari': {
                    'sg': [transliterate_output(f, 'Devanagari') for f in hk_sg],
                    'pl': [transliterate_output(f, 'Devanagari') for f in hk_pl]
                }
            })

    return jsonify(data)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
