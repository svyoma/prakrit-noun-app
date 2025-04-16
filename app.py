from aksharamukha import transliterate
from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = '''
<!doctype html>
<title>Prakrit Word Form Generator</title>
<h2>Enter a Prakrit Word</h2>
<form method="post">
  <input type="text" name="word" required>
  <input type="submit" value="Generate Forms">
</form>

{% if forms %}
  <h3>Generated Forms</h3>
  <table border=1 cellpadding=8>
    <tr>
      <th>Case</th><th>Singular</th><th>Plural</th>
    </tr>
    {% for row in forms %}
      <tr>
        <td><strong>{{ row.name }}</strong></td>
        <td>{{ row.singular|join(', ') }}</td>
        <td>{{ row.plural|join(', ') }}</td>
      </tr>
    {% endfor %}
  </table>
{% endif %}
'''

def to_devanagari(text):
    return transliterate.process('HK', 'Devanagari', text)

def remove_last_vowel(word):
    for i in reversed(range(len(word))):
        if word[i] in 'aeiou':
            return word[:i] + word[i+1:]
    return word

def replace_vowel(word, replacement, ending, is_a):
    if is_a and ending == 'a':
        return word.rsplit('a', 1)[0] + replacement
    elif ending == 'i' or ending == 'u':
        new_vowel = replacement if replacement else ('I' if ending == 'i' else 'U')
        return word.rsplit(ending, 1)[0] + new_vowel
    return word

@app.route('/', methods=['GET', 'POST'])
def index():
    forms = []
    if request.method == 'POST':
        word = request.form['word'].strip()
        if not word:
            return render_template_string(HTML_TEMPLATE, forms=None)

        ending = word[-1]
        no_vowel = remove_last_vowel(word)
        a_to_A = replace_vowel(word, 'A', ending, True)
        a_to_e = replace_vowel(word, 'e', ending, True)
        i_u_to_IU = replace_vowel(word, '', ending, False)

        def build_forms(name, singular, plural):
            return {
    "name": name,
    "singular": [to_devanagari(f"{b}{s}") for s, b in singular],
    "plural": [to_devanagari(f"{b}{s}") for s, b in plural]
}
        cases = [
            ("First Case",
             [('o', no_vowel)] if ending == 'a' else [("", i_u_to_IU)] if ending in 'iu' else [],
             [("", a_to_A)] if ending == 'a' else [("a_u", no_vowel), ("ao", no_vowel), ("", i_u_to_IU)] if ending in 'iu' else []),

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

        forms = [build_forms(name, singular, plural) for name, singular, plural in cases if singular or plural]

    return render_template_string(HTML_TEMPLATE, forms=forms)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
