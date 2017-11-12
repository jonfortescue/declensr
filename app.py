 # -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from flask_pymongo import PyMongo
import sys
import re

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

# index/home page
@app.route("/")
def home():
    languages = mongo.db.lang.find()
    return render_template("index.html", title="Declensr", header="Which language are you studying?", languages=languages)

# Language page
@app.route("/lang/<lang>", methods=['GET', 'POST', r'DELETE'])
def lang(lang):
    # Default page access
    if request.method == 'GET':
        # If the language hasn't been defined in the database, it needs to be created
        if mongo.db[lang].count() == 0:
            return render_template("create.html", title=lang)
        else:
            return render_template("dashboard.html", title="%s Dashboard" % (mongo.db[lang].find_one({u'type': u'display'})['value']),
                                   pronouns=mongo.db[lang].find({ u'type': u'special', u'name': u'Pronoun' }))
    # To delete a language
    elif request.method == r'DELETE':
        mongo.db[lang].remove()
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

            bcop.append(' -> '.join(breadcrumbs) + (' *' if value != "" else ''))

            if value != "":
                if key == "Language":
                    if value != lang:
                        return "This grammar (%s) is not for the selected language (%s)." % (value, lang)
                    langdb = mongo.db[lang]
                elif key == "Display":
                    display = value
                    langdb.insert_one({ 'namespace': 'grammar', 'type': 'display', 'value': display })
                    mongo.db.lang.insert_one({'lang': lang, 'name': 'Greek'})
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
        return render_template("creation-report.html", title=display, parsop='\n'.join(parsop), bcop='\n'.join(bcop))
    else:
        return "HTTP 405 Method Not Allowed"
