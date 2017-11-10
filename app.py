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

# Adapted from https://stackoverflow.com/a/12576755
def subpattern_exists(mylist, pattern):
    if len(pattern) > len(mylist):
        return False
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            return True
    return False

# index/home page
@app.route("/")
def home():
    return render_template("index.html", title="Which language are you studying?")

# Language page
@app.route("/lang/<lang>", methods=['GET', 'POST'])
def lang(lang):
    # Default page access
    if request.method == 'GET':
        # If the language hasn't been defined in the database, it needs to be created
        if mongo.db[lang].count() == 0:
            return render_template("create.html", title=lang)
        else:
            return "This language has definitions but this program isn't done."
    # If we're updating the grammar file via create.html, we handle that
    elif request.method == 'POST':
        data = request.form['langDef'].split('\n')
        display = ""
        prevIndent = 0
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
                elif key == "Display":
                    display = value
                elif "Rules" in breadcrumbs:
                    assert len(breadcrumbs) == 2 # we should be at second level for rules
                    # TODO: Handle rule creation
                elif "Attribute" in breadcrumbs:
                    assert len(breadcrumbs) >= 3 # we should be past the third level if we're defining attributes
                    obj = breadcrumbs[0:len(breadcrumbs) - 2]
                    attributeName = key
                    possibleValues = re.split(r',\s*', value)
                    attribute = (possibleValues, obj, attributeName)
                    attributes.append(attribute)
                    parsop.append("ATTRIBUTE:\t%s.%s, values: %s" % ('.'.join(obj), attributeName, ', '.join(possibleValues)))
                elif "Special" in breadcrumbs:
                    assert len(breadcrumbs) >= 4
                    start = breadcrumbs.index('Special') + 1
                    itemName = breadcrumbs[start]
                    obj = breadcrumbs[0:start+1]
                    attributeValues = breadcrumbs[start + 1:len(breadcrumbs)]
                    attributeList = []
                    for attributeValue in attributeValues:
                        for attribute in attributes:
                            if attributeValue in attribute[0] and subpattern_exists(obj, attribute[1]):
                                attributeList.append((attribute[2], attributeValue))
                    parsop.append("SPECIAL:\t%s %s, attributes: %s" % (itemName, value, ', '.join(': '.join(x) for x in attributeList)))
            prevIndent = indent
        return render_template("creation-report.html", title=display, parsop='\n'.join(parsop), bcop='\n'.join(bcop))
    else:
        return "HTTP 405 Method Not Allowed"
