# Declensr
## What this is
**Declensr** is a web-based utility built in [Flask](http://flask.pocoo.org/) designed to aid with studying foreign language grammars. It does this by generating worksheet-style exercises given a description of an arbitrary grammar and a schema for the exercises.

## Dependencies
Declensr depends on:
* Python 2.7
* [Flask](http://flask.pocoo.org/)
* [MongoDB](https://www.mongodb.com/)
* [PyMongo](https://api.mongodb.com/python/current/)
* [Flask_PyMongo](https://github.com/dcrosta/flask-pymongo)

It is also recommended (per standard Python development practices) that you use `virtualenv` while developing.

## Getting started
To build Declensr:
1. Download and install MongoDB
2. Clone the repo
3. Inside the repo, run `virtualenv .` to create the virtualenv
4. On Unix-based systems, run `source bin/activate` to enter the virtualenv. On Windows, run `Scripts\activate`
5. Install the dependencies with pip. They will all be automatically installed if you run `pip flask_pymongo`.
6. In a separate terminal, navigate to the `mongod` executable and run it
7. In the original terminal, set your environment variables. On Unix-based systems, run `export FLASK_APP=app.py`, while on Windows run `set FLASK_APP=app.py`. If you would like debugging to be enabled, run `export FLASK_DEBUG=1` or `set FLASK_DEBUG=1`, depending on your platform.
8. Run the application with the command `flask run --host=0.0.0.0`. Navigate to the web app at http://localhost:5000.

## Ways you can contribute
Declensr is completely FOSS and designed to be highly extensible. If you want to use Declensr to study a language that has not been implemented yet, you will need to do some legwork to get it working. If you do this, please open a pull request to the main repo so everyone else can enjoy that language as well!

### Creating new wordlists
In the future, Declensr will be able to auto-generate wordlists from Wiktionary. In the meantime, manual entry of vocabulary is greatly appreciated!

### Creating new exercises
If grammars are Declensr's skeleton, then exercises are its organs. Exercises make Declensr worth using, and we can never have enough. If you think of an exercise useful to you, Declensr makes it easy to implement that exercise. Once you've done that, make a pull request and share it with everyone!

**TODO: Documentation for Exercises**

Some exercises may require adding new functionality to Declensr. If you're confident about programming it yourself, feel free to do so and open a pull request. If not, [open an issue](https://github.com/jonfortescue/declensr/issues) describing what functionality you'll need for the exercise and label it "request: functionality" and "request: exercise."

### Implementing new grammars
For some languages, all the functionality you need will already be built into Declensr's codebase. In these cases, all you need to do is create a new grammar definition for Declensr to parse. Thankfully, this isn't to difficult.

In the future, Declensr will be able to auto-generate grammars from Wiktionary templates. In the meantime, you can base your grammar on the existing grammar files, such as [`greek.grammar`](https://github.com/jonfortescue/declensr/blob/master/grammars/greek.grammar).

#### Classes, Items, and Attributes
Grammars are treated as tree structures, where grammar concepts are divided into *Classes* (e.g. "Nouns", "Verbs"), *Items* (e.g. "Articles", "Pronouns"), and *Types* (specific ways the concept is handled under that grammar) with individual *Attributes*. Using the example of nouns,
the values under each individual *Type* or *Item* will determine the noun declension given the specific set of attributes.

```
Noun:
  Attribute:
    Number: Singular, Plural
    Gender: Masculine, Feminine, Neuter
    Case: Nominative, Accusative, Genitive, Vocative
  Special:
    [KEY]Definite Article:
      Singular:
        Masculine:
          Nominative: ο
          Accusative: [[0|το, τον]]
          Genitive: του
```

The above fragment defines the *Class* **Noun** and denotes the specific *Attributes* **Nouns** can have (in this case, a grammatical number, gender, and case). It then defines a specific *Item* (the **Definite Article**). From this fragment, we can see that the **Singular, Masculine, Nominative Definite Article** is **ο**, while the **Singular, Masculine, Genitive Definite Article** is **του**.

#### Rules
The above fragment also reveals another feature of grammars: disambiguating *Rules*. Some inflections can have multiple forms depending on the context. Rules help exercises disambiguate between these forms so the proper form is displayed. The syntax for this is ``[[RULE-NUMBER|item0, item1, ...]]``. In this case, the rule used is rule 0, which we can see is:

```
Rules:
  0: \1 ([αειουηωάέίόύήώκπτξψ]|μπ|ντ|γκ)
```

Rule 0 tells us to use the item at index `1` if the given regular expression returns a match, which effectively means that the **Singular, Masculine, Accusative Definite Article** is **τον** when it precedes a vowel or one of a few consonants/double consonants and **το** otherwise. *Rules* are always defined at the beginning of the grammar and can be used on any value. Currently, *Rules* can either match a regular expression or a grammar *Class*.

#### More on Attributes
Attributes can be defined anywhere in the structure. In the above example, they apply to the *Noun* Class. However, a subtype of *Noun*, the *Pronoun*, needs additional specific attributes. Thus, we can define it as follows:
```
Noun: ...
  Special: ...
    [KEY]Pronoun:
      Attribute:
        Strength: Emphatic, Clitic
        Person: 1st, 2nd, 3rd
```

This fragment defines the **Pronoun** *Item* and gives it its own set of *Attributes*. These *Attributes* stack with those already defined under the noun *Class*, so we can define an individual **Pronoun** as follows:
```
Noun: ...
  Special: ...
    [KEY]Pronoun:
      Emphatic:
        Singular: ...
          3rd:
            Masculine:
              Nominative: αυτός
              Accusative: αυτόν
              Genitive: αυτού`
```

#### Types
*Types* define specific inflection modes for a particular grammar Class. In our previous example of Greek noun declensions:

```
Noun: ...
  Type:
    Masculine:
      [KEY]el-nM-ος-οι-1:
        Singular:
          Nominative: {{0}}ός
          Accusative: {{0}}ό
          Genitive: {{0}}ού
          Vocative: {{0}}έ
        Plural:
          Nominative: {{0}}οί
          Accusative: {{0}}ών
          Genitive: {{0}}ούς
          Vocative: {{0}}οί
```

It is worth noting from this that the **Masculine** *Attribute* precedes the *Type* declaration. This means that all declensions in that type have the gender **Masculine**. This allows one to quickly define a large number of *Types* with common *Attributes*.

The `{{0}}` on this *Type* determine which **stem** will be used by Declensr. This particular *Type* only has one stem, but some *Types*...

```
      [KEY]el-nM-ος-οι-3b:
        Singular:
          Nominative: {{0}}ος
          Accusative: {{0}}ο
          Genitive: {{1}}ου
          Vocative: {{0}}ε
        Plural:
          Nominative: {{0}}οι
          Accusative: {{1}}ους
          Genitive: {{1}}ων
          Vocative: {{0}}οι
```

can have multiple stems. In this case, **Nominative**, **Accusative** **Singular**, and **Vocative** nouns will all take the first stem, while the **Genitive** and **Accusative** **Plural** forms will take the second.

#### Wiktionary
These formats are based on [Wiktionary](https://en.wiktionary.org/)'s inflection templates (see [here](https://en.wiktionary.org/wiki/Template:el-nM-%CE%BF%CF%82-%CE%BF%CE%B9-3b) for an example). It is highly recommended that you use Wiktionary as a source for your own grammars, as they are extremely thorough in defining their templates. There are collections of these templates for easy reference; see [here](https://en.wiktionary.org/wiki/Wiktionary:Greek_noun_inflection-table_templates) for the Greek noun example.

### Implementing new functionality
Some languages will not fit into the grammar framework currently provided by Declensr. For these languages, you will have to implement new grammar syntaxes and add code to parse them. If you don't know Python, try the crash course over at Codecademy for a brief intro and take a look at the Flask and PyMongo documentation if anything is confusing you. If you already know Python, just [take a look](https://github.com/jonfortescue/declensr/blob/master/app.py#L105) at the core code for grammar parsing and add your syntax in. **Please, avoid changing any existing sytnax parsing outside of bugfixes.** Changing the existing syntax will break the existing grammars. Instead, simply add on new functionality that doesn't affect the old logic.

If you don't know how to program or don't have the time to implement the new functionality, please [open an issue](https://github.com/jonfortescue/declensr/issues) and tag it "request: functionality." Mention the language you're trying to add and briefly describe the functionality you need in order to properly add that language.
