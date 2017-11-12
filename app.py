 # -*- coding: utf-8 -*-
from flask import Flask, Markup, render_template, request, redirect
from flask_pymongo import PyMongo
import sys
import re
from bson.objectid import ObjectId

# without this, encoding issues cause errors
reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
mongo = PyMongo(app) # establish MongoDB connection

# constants
RULES_LEVEL = 2
ATTRIBUTE_LEVEL = 3
TYPE_LEVEL = 3
SPECIAL_LEVEL = 4

def nav_header(crumbs):
    header = """<nav aria-label="breadcrumb" role="navigation">"""
    header += """\t<ol class="breadcrumb">"""
    for page in crumbs[:-1]:
        header += """<li class="breadcrumb-item"><a href="%s">%s</a></li>""" % (page[1], page[0])
    header += """<li class="breadcrumb-item active" aria-current="page">%s</li>""" % (crumbs[-1][0])
    header += "\t</ol>"
    header += "</nav>"
    return Markup(header)

# Adapted from https://stackoverflow.com/a/12576755
def subpattern_exists(mylist, pattern):
    if len(pattern) > len(mylist):
        return False
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            return True
    return False

def extract_attributes(header, attributes, breadcrumbs):
    start = breadcrumbs.index(header)
    attributeValues = breadcrumbs[start + 1:len(breadcrumbs)]
    for item in attributeValues:
        if "[KEY]" in item:
            assert len(item) > 5
            itemName = item[5:]
            namespace = breadcrumbs[0:breadcrumbs.index(item)+1]
    attributeList = []
    for attributeValue in attributeValues:
        if attributeValue == "[KEY]%s" % (itemName):
            continue
        for attribute in attributes:
            if attributeValue in attribute[0] and subpattern_exists(namespace, attribute[1]):
                attributeList.append((attribute[2], attributeValue))
    return (itemName, namespace, attributeList)

def vocab_add_edit_generic_get(lang):
    name = mongo.db[lang].find_one({u'type': u'display'})['value']
    typesFromDb = mongo.db[lang].find({u'namespace': u'grammar', u'type': u'type'})
    types = []
    numStemsForType = {}
    for typ in typesFromDb:
        types.append(typ['name'])
    types = list(set(types))
    types.sort()
    maxStemNum = 0
    for typ in types:
        numStemsForType[typ] = number_stems_in_type(mongo.db[lang], typ)
        if numStemsForType[typ] > maxStemNum:
            maxStemNum = numStemsForType[typ]
    return (name, types, numStemsForType, maxStemNum)

def vocab_add_edit_generic_post(lang):
    vocabType = request.form['type']
    stems = request.form.getlist('stemBox')[0:number_stems_in_type(mongo.db[lang], vocabType)]
    return (vocabType, stems)

def number_stems_in_type(db, typeName):
    types = db.find({u'namespace': 'grammar', u'name': typeName})
    maxStemNum = 0
    for typ in types:
        if re.match(r'\{\{(\d+)\}\}', typ['value']) is None:
            print typ
            stemNum = 0
        else:
            stemNum = int(re.match(r'\{\{(\d+)\}\}', typ['value']).group(1))
        if stemNum > maxStemNum:
            maxStemNum = stemNum
    return maxStemNum + 1

def get_default_word(db, stem, typeName):
    ending = re.sub(r'\{\{\d+\}\}', '', db.find_one({u'namespace': u'grammar', u'name': typeName})['value'])
    return stem + ending

def construct_breadcrumbs(line, prevIndent, breadcrumbs):
    pair = re.split(r':\s*', line)
    indent = pair[0].count('  ')
    key = pair[0].strip()
    if len(pair) > 1:
        value = pair[1].strip()

    if len(breadcrumbs) == 0:
        breadcrumbs.append(key)
    elif indent == prevIndent:
        breadcrumbs.pop()
        breadcrumbs.append(key)
    elif indent > prevIndent:
        breadcrumbs.append(key)
    elif indent < prevIndent:
        assert (prevIndent - indent + 1) <= len(breadcrumbs)
        for i in range(prevIndent - indent + 1):
            breadcrumbs.pop()
        breadcrumbs.append(key)

    return (indent, key, value)

def render_html_from_schema(schema, tabs):
    html = ""
    for key in schema.keys():
        html += "\n"
        keyFormat = re.match(r'([\w-]+)(\[\d+\])?(\{\{[\w\s-]+\}\})?', key)
        keySafe = keyFormat.group(1)
        keyScript = keyFormat.group(3)
        attribute = ""

        if keyScript is not None:
            keyScript = keyScript[2:-2]
            keyScriptFormat = re.match(r'([\w-]+) ([\w\s-]+)', keyScript)
            command = keyScriptFormat.group(1)
            argument = keyScriptFormat.group(2)

            if command == "Span":
                attribute = " colspan=4"

        if keySafe == "Heading-1":
            html += "%s<h1%s>" % (tabs, attribute)
        elif keySafe == "Heading-2":
            html += "%s<h2%s>" % (tabs, attribute)
        elif keySafe == "Heading-3":
            html += "%s<h3%s>" % (tabs, attribute)
        elif keySafe == "Heading-4":
            html += "%s<h4%s>" % (tabs, attribute)
        elif keySafe == "Table":
            html += "%s<table class=\"table\"%s>" % (tabs, attribute)
        elif keySafe == "Table-Group":
            html += "%s<tbody%s>" % (tabs, attribute)
        elif keySafe == "Row":
            html += "%s<tr%s>" % (tabs, attribute)
        elif keySafe == "Table-Heading":
            html += "%s<th%s>" % (tabs, attribute)
        elif keySafe == "Cell":
            html += "%s<td%s>" % (tabs, attribute)

        if type(schema[key]) is not dict:
            html += schema[key]
        else:
            html += render_html_from_schema(schema[key], tabs + "\t")

        if keySafe == "Heading-1":
            html += "</h1>"
        elif keySafe == "Heading-2":
            html += "</h2>"
        elif keySafe == "Heading-3":
            html += "</h3>"
        elif keySafe == "Heading-4":
            html += "</h4>"
        elif keySafe == "Table":
            html += "%s</table>" % (tabs)
        elif keySafe == "Table-Group":
            html += "%s</tbody>" % (tabs)
        elif keySafe == "Row":
            html += "%s</tr>" % (tabs)
        elif keySafe == "Table-Heading":
            html += "</th>"
        elif keySafe == "Cell":
            html += "</td>"
        html += "\n"
    return html

# index/home page
@app.route("/")
def home():
    languages = mongo.db.lang.find()
    return render_template("index.html", title="Declensr", header="Which language are you studying?", languages=languages,
                           nav=nav_header([("Declensr", "/")]))

# Language page
@app.route("/lang/<lang>", methods=['GET', 'POST', r'DELETE'])
def lang(lang):
    # Default page access
    if request.method == 'GET':
        # If the language hasn't been defined in the database, it needs to be created
        if mongo.db[lang].count() == 0:
            return render_template("create.html", title=lang, nav=nav_header([("Declensr", "/"), ("Create " + lang, "/lang/" + lang)]))
        else:
            display = mongo.db[lang].find_one({u'type': u'display'})['value']
            return render_template("dashboard.html", lang=lang, title="%s Dashboard" % (display),
                                   nav=nav_header([("Declensr", "/"), (display, "/lang/" + lang)]))
    # To delete a language
    elif request.method == r'DELETE':
        mongo.db[lang].remove()
        mongo.db.lang.remove({ 'lang': lang })
        return "Language deleted."
    # If we're updating the grammar file via create.html, we handle that
    elif request.method == 'POST':
        data = request.form['langDef'].split('\n')
        display = ""
        prevIndent = 0
        numRules = 0
        breadcrumbs = list()
        attributes = list()
        bcop = list()
        parsop = list()
        for line in data:
            if line.strip() == "":
                continue
            (indent, key, value) = construct_breadcrumbs(line, prevIndent, breadcrumbs)

            bcop.append(' -> '.join(breadcrumbs) + (' *' if value != "" else ''))

            if value != "":
                if key == "Language":
                    if value != lang:
                        return "This grammar (%s) is not for the selected language (%s)." % (value, lang)
                    langdb = mongo.db[lang]
                elif key == "Display":
                    display = value
                    langdb.insert_one({ 'namespace': 'grammar', 'type': 'display', 'value': display })
                    mongo.db.lang.insert_one({'lang': lang, 'name': display})
                elif "Rules" in breadcrumbs:
                    assert len(breadcrumbs) == RULES_LEVEL
                    assert int(key) == numRules
                    numRules += 1
                    parsop.append("RULE %d: %s" % (int(key), value))
                    langdb.insert_one({ 'namespace': 'grammar', 'type': 'rule', 'rule': value })
                elif "Attribute" in breadcrumbs:
                    assert len(breadcrumbs) >= ATTRIBUTE_LEVEL
                    obj = breadcrumbs[0:len(breadcrumbs) - 2] # 2 = distance of "Attribute" from end of breadcrumbs
                    attributeName = key
                    possibleValues = re.split(r',\s*', value)
                    attribute = (possibleValues, obj, attributeName)
                    attributes.append(attribute)
                    parsop.append("ATTRIBUTE:\t%s.%s, values: %s" % ('.'.join(obj), attributeName, ', '.join(possibleValues)))
                    langdb.insert_one({ 'namespace': 'grammar', 'type': 'attribute', 'name': attributeName, 'object': obj, 'values': possibleValues })
                elif "Special" in breadcrumbs:
                    assert len(breadcrumbs) >= SPECIAL_LEVEL
                    (itemName, obj, attributeList) = extract_attributes('Special', attributes, breadcrumbs)
                    parsop.append("SPECIAL:\t%s %s, attributes: %s" % (itemName, value, ', '.join(': '.join(x) for x in attributeList)))
                    dbvalue = { 'namespace': 'grammar', 'type': 'special', 'name': itemName, 'value': value }
                    for attribute in attributeList:
                        dbvalue[attribute[0]] = attribute[1]
                    langdb.insert_one(dbvalue)
                elif "Type" in breadcrumbs:
                    assert len(breadcrumbs) >= TYPE_LEVEL
                    (itemName, obj, attributeList) = extract_attributes('Type', attributes, breadcrumbs)
                    parsop.append("TYPE:\t\t%s %s, attributes: %s" % (itemName, value, ', '.join(': '.join(x) for x in attributeList)))
                    dbvalue = { 'namespace': 'grammar', 'type': 'type', 'name': itemName, 'value': value }
                    for attribute in attributeList:
                        dbvalue[attribute[0]] = attribute[1]
                    langdb.insert_one(dbvalue)
            prevIndent = indent
        return render_template("creation-report.html", title=display, parsop='\n'.join(parsop), bcop='\n'.join(bcop),
                               nav=nav_header([("Declensr", "/"), (display, "/lang/" + lang), ("Creation Report", "/")]))
    else:
        return "HTTP 405 Method Not Allowed"

# Vocab dashboard
@app.route("/lang/<lang>/vocab")
def vocab(lang):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        name = mongo.db[lang].find_one({u'type': u'display'})['value']
        vocab = mongo.db[lang].find({ u'namespace': u'vocab' })
        vocab = list(((get_default_word(mongo.db[lang], word['stems'][0], word['type']), word['_id']) for word in vocab))
        vocab.sort(key=lambda word: word[0].lower())
        return render_template("vocab.html", title="%s Vocab List" % (name), vocab=vocab,
                               nav=nav_header([("Declensr", "/"), (name, "/lang/" + lang), ("Vocab", "/lang/%s/vocab" % (lang))]))

# Add vocab
@app.route("/lang/<lang>/vocab/add", methods=["GET", "POST"])
def add_vocab(lang):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        if request.method == "GET":
            (name, types, numStemsForType, maxStemNum) = vocab_add_edit_generic_get(lang)
            return render_template("vocab-add-edit.html", title="%s: Add Vocab Word" % (name), types=types, numStemsForType=numStemsForType,
                                   maxStemNum=maxStemNum, word=None, nav=nav_header([("Declensr", "/"), (name, "/lang/" + lang),
                                   ("Vocab", "/lang/%s/vocab" % (lang)), ("Add Word", "/lang/%s/vocab/add" % (lang))]))
        elif request.method == "POST":
            (vocabType, stems) = vocab_add_edit_generic_post(lang)
            mongo.db[lang].insert_one({ u'namespace': 'vocab', u'type': vocabType, u'stems': stems })
            return redirect("/lang/%s/vocab/add" % (lang))
        else:
            return "HTTP 405 Method Not Allowed"

# Edit a vocab word
@app.route("/lang/<lang>/vocab/<vocabid>", methods=["GET", "POST", r"DELETE"])
def edit_vocab(lang, vocabid):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        if request.method == "GET":
            (name, types, numStemsForType, maxStemNum) = vocab_add_edit_generic_get(lang)
            word = mongo.db[lang].find_one({"_id": ObjectId(vocabid)})
            word_display = get_default_word(mongo.db[lang], word['stems'][0], word['type'])
            return render_template("vocab-add-edit.html", title="%s: Editing %s" % (name, word_display), types=types, numStemsForType=numStemsForType,
                                   maxStemNum=maxStemNum, word=word, nav=nav_header([("Declensr", "/"), (name, "/lang/" + lang),
                                   ("Vocab", "/lang/%s/vocab" % (lang)), ("Editing " + word_display, "/lang/%s/vocab/%s" % (lang, vocabid))]))
        elif request.method == "POST":
            (vocabType, stems) = vocab_add_edit_generic_post(lang)
            mongo.db[lang].update_one({ u'_id': ObjectId(vocabid) }, { '$set': { u'type': vocabType, u'stems': stems } })
            return redirect("/lang/%s/vocab/%s" % (lang, vocabid))
        elif request.method == r"DELETE":
            mongo.db[lang].remove_one({ u'_id': ObjectId(vocabid) })
            return redirect("/lang/%s/vocab" % (lang))
        else:
            return "HTTP 405 Method Not Allowed"

# Exercise dashboard
@app.route("/lang/<lang>/exercises", methods=["GET", r"DELETE"])
def exercises(lang):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        if request.method == r'DELETE':
            mongo.db[lang].remove({ u'namespace': u'exercise' })
        name = mongo.db[lang].find_one({u'type': u'display'})['value']
        exercises = mongo.db[lang].find({ u'namespace': u'exercise' })
        return render_template("exercises.html", title="%s: Exercises" % (name), exercises=exercises,
                               nav=nav_header([("Declensr", "/"), (name, "/lang/" + lang), ("Exercises", "/lang/%s/exercises" % (lang))]))

# Add an exercise
@app.route("/lang/<lang>/exercises/add", methods=["GET", "POST"])
def add_exercises(lang):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        name = mongo.db[lang].find_one({u'type': u'display'})['value']
        if request.method =="GET":
            return render_template("exercise-add-edit.html", title="%s: Add Exercises" % (name), nav=nav_header([("Declensr", "/"),
                                   (name, "/lang/" + lang), ("Exercises", "/lang/%s/exercises" % (lang)), ("Add Exercises", "/lang/%s/exercises/add" % (lang))]))
        elif request.method == "POST":
            data = request.form['exerciseSchema'].split('\n')
            prevIndent = 0
            breadcrumbs = list()
            bcop = list()
            parsop = list()
            exercises = {}
            for line in data:
                if line.strip() == "":
                    continue
                (indent, key, value) = construct_breadcrumbs(line, prevIndent, breadcrumbs)

                bcop.append(' -> '.join(breadcrumbs) + (' *' if value != "" else ''))

                assert len(breadcrumbs) > 0
                exerciseName = breadcrumbs[0]
                if indent == 0:
                    exercises[exerciseName] = { 'namespace': 'exercise', 'name': exerciseName }
                    exercises[exerciseName]["Display"] = {}
                    parsop.append("NEW EXERCISE: " + exerciseName)
                elif "Display" in breadcrumbs[1] and value == "":
                    assert len(breadcrumbs) > 1
                    assert re.match(r'Display(\d+)', breadcrumbs[1])
                    displayIndex = re.match(r'Display(\d+)', breadcrumbs[1]).group(1)
                    if indent == 1:
                        exercises[exerciseName]["Display"][displayIndex] = {}
                        parsop.append("NEW DISPLAY[%s]: %s" % (displayIndex, exerciseName))
                    else:
                        assert len(breadcrumbs) > 2
                        displayTree = breadcrumbs[2:-1]
                        currentNode = exercises[exerciseName]["Display"][displayIndex]
                        for node in displayTree:
                            currentNode = currentNode[node]
                        currentNode[breadcrumbs[-1]] = {}
                        parsop.append("DISPLAY NODE: Display[%s].%s.%s (%s)" % (displayIndex, '.'.join(displayTree), breadcrumbs[-1], exerciseName))
                elif value != "":
                    if indent == 1:
                        assert len(breadcrumbs) > 1
                        item = breadcrumbs[1]
                        isArray =  re.match(r'(\w+)(\d+)', item)
                        if isArray:
                            item = isArray.group(1)
                            index = isArray.group(2)
                            exercises[exerciseName][item] = {}
                            exercises[exerciseName][item][index] = value
                            parsop.append("PROPERTY: %s[%s] of %s in %s" % (item, index, value, exerciseName))
                        else:
                            exercises[exerciseName][item] = value
                            parsop.append("PROPERTY: %s of %s in %s" % (item, value, exerciseName))
                    elif "Display" in breadcrumbs[1]:
                        displayIndex =  re.match(r'Display(\d+)', breadcrumbs[1]).group(1)
                        displayTree = breadcrumbs[2:-1]
                        currentNode = exercises[exerciseName]["Display"][displayIndex]
                        for node in displayTree:
                            currentNode = currentNode[node]
                        currentNode[breadcrumbs[-1]] = value
                        parsop.append("DISPLAY NODE: Display[%s].%s.%s: %s (%s)" % (displayIndex, '.'.join(displayTree), breadcrumbs[-1], value, exerciseName))

                prevIndent = indent
            for exercise in exercises.keys():
                mongo.db[lang].insert_one(exercises[exercise])
            return render_template("creation-report.html", title="%s Exercises Added" % (name), parsop='\n'.join(parsop), bcop='\n'.join(bcop))

# Preview an exercise
@app.route("/lang/<lang>/exercises/<exercise_id>")
def preview_exercise(lang, exercise_id):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        name = mongo.db[lang].find_one({u'type': u'display'})['value']
        exercise = mongo.db[lang].find_one({ u'_id': ObjectId(exercise_id) })
        displays = {}
        for displayKey in exercise['Display'].keys():
            currentDisplay = exercise['Display'][displayKey]
            tabs = ""
            displays[displayKey] = Markup(render_html_from_schema(currentDisplay, tabs))
        return render_template("exercise-preview.html", title="Greek Exercise: " + exercise['name'], displays=displays)

# Edit an exercise
@app.route("/lang/<lang>/exercises/<exercise>/edit")
def edit_exercise(lang, exercise):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        name = mongo.db[lang].find_one({u'type': u'display'})['value']
        return "Not yet defined. (%s, %s)" % (name, exercise)

# Do an exercise
@app.route("/lang/<lang>/exercises/<exercise>/do")
def do_exercise(lang, exercise):
    if mongo.db[lang].count() == 0:
        return redirect("/lang/%s" % (lang))
    else:
        name = mongo.db[lang].find_one({u'type': u'display'})['value']
        return "Not yet defined. (%s, %s)" % (name, exercise)
