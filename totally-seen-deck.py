# -*- coding: utf-8 -*-
# Copyright: Arthur Milchior <arthur@milchior.fr>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
"""Copyright: Arthur Milchior arthur@milchior.fr
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
Feel free to contribute to the code on
https://github.com/Arthur-Milchior/anki-totally-seen-deck
Add-on number 852406763

This add-on adds a button which allows you to see the list of decks
which are entirely seen.

If a deck is entirely seen, its children are not shown in the list.

The reason I wanted this deck is the following: when a deck is
entirely seen, it mostly means that it is time for me to add new cards
in this deck. Since I've got more than 400 decks, with a lot of
sub-sub-sub...decks this add-ons allows me to see which decks need attention.
"""


from aqt.deckbrowser import DeckBrowser
from aqt.utils import showWarning, askUser
from anki.utils import intTime
from aqt import mw
from aqt.qt import QAction
import aqt


def numberCardsInDeck (deck, name, time, constraint=None):
    """Put as nameValue the number of cards satisfying constraint in
    deck (not its descendant). If last nameValue was computed later than
    time, do not recompute it.

    return this value
    """
    did = deck['id']
    constraint = ("and %s" % constraint) if constraint else " "
    request= "select count(*) from cards where (did = %s or odid = %s) %s" % (did, did, constraint)
    def code():
        return mw.col.db.scalar(request)
    return setValueIfNew(code,deck,time, name)

def numberUnseenCardsInDeck (deck, time):
    return numberCardsInDeck(deck, "unseenCard", time, "queue=0" )

def numberCardsDescendant(deck, name, time, constraint=None):
    """Put as nameValue the number of cards satisfying constraint in this
    deck. Do the same thing for the descendant. Put as
    nameDescendantValue the number of cards satisfying constaint in
    this deck and its descendant.

    If last nameValue or nameDescendantValue was computed later than
    time, do not recompute it.
    """
    def code():
        child_list = mw.col.decks.children(deck['id'])
        setValue("leaf",deck,not child_list)
        unseen = numberCardsInDeck(deck, name, time, constraint)
        #showCancel("Number of cards in %s is %s"%(deck['name'],unseen))
        if unseen == None:
            raise deck
        for (_, childId) in child_list:
            childDeck = mw.col.decks.get(childId)
            nbCardChild = numberCardsInDeck(childDeck, name, time, constraint)
            #showCancel("Adding  %s cards in %s from %s"%(nbCardChild,deck['name'],childDeck['name']))
            unseen += nbCardChild
            if unseen == None:
                raise childDeck
        #showCancel("Total number of card in %s is %s"%(deck['name'],unseen))
        return unseen
    return setValueIfNew(code, deck, time,"%sDescendant"%name)

def numberUnseenCardsDescendant (deck,time):
    return numberCardsDescendant(deck,"unseenCard", time, "queue=0")

def noUnseen(deck, time=None):
    """Whether there is unseen card in deck of iin its
    descendant. Assuming no change since time."""
    time = time or intTime()
    return numberUnseenCardsDescendant(deck,time) == 0
    
def checkEmpty():
    """The list of decks without unseen cards, whose parents either
    does not exists, or have unseen cards."""
    col = mw.col
    emptys = []
    deckManager = col.decks
    decks = deckManager.decks
    time = intTime()
    for did in decks:
        deck = decks[did]
        name=deck['name']
        showCancel("Considering %s"%name)
        if noUnseen(deck, time) and did != 1:
            parentList =  name.split('::')[:-1]
            if parentList:
                parentName='::'.join(parentList)
                showCancel("Its parent is %s"%parentName)
                parentId = deckManager.id(parentName)
                showCancel("Its parent id is %s"%parentId)
                parent = decks[str(parentId)]
                if not noUnseen(parent, time):
                    emptys.append(name)
            else:
                emptys.append(name)
                showCancel("Its parent does not exists")
    #filter parent
    emptys=sorted(emptys)

    message = "Decks without unseen cards are: "
    for dName in emptys:
        message = "%s\n%s"%(message, dName)
    showWarning(message)


    
def executeIfNew(code, dic,time, name):
    """Execute code if dic[nameTime]<time, in this case change time"""
    if getTime(name, dic)< time:
        code()
        setTime(name, dic)

def setValueIfNew(code, dic, time, name):
    """If last computation is older than time, use code to compute the new
    value associated to name. In any case, return the value associated to this name.
    """
    def newCode():
        setValue(name,dic,code())
    executeIfNew(newCode,dic,time,name)
    return getValue(name,dic)

def setTime(name, dic, time=None):
    """set nameTime to time (intTime() by default). Return the time."""
    time = time or intTime()
    dic["%sTime"%name]=time
    return time

def getTime(name, dic):
    """set nameTime to now. Return the value."""
    return dic.get("%sTime"%name)

def setValue(name, dic,value):
    """set nameValue to value. Return the value"""
    if value==None:
        raise 
    longname="%sValue"%name
    #showCancel("%s is set to %s in %s"%(longname,value,dic['name']))
    dic[longname]=value
    return value

def getValue(name, dic):
    """Return dec[nameValue]."""
    return dic.get("%sValue"%name)


def showCancel(message):
    # if not askUser(message):
    #     raise
    return

action = QAction(aqt.mw)
action.setText("Empty decks")
mw.form.menuTools.addAction(action)
action.triggered.connect(checkEmpty)
