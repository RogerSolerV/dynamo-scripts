import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

import Autodesk
import RevitServices

from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager

clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

doc = DocumentManager.Instance.CurrentDBDocument

collector = FilteredElementCollector(doc)
doors = collector.OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()
ex = []
err = []

# for hardcoded parameters
paramToLookForName = 'NTI_RoomAssociation'
paramToChangeName = 'Mark'
pintVerbose = 1  # set to 0 for not printing corrected door names

# for Python Script  box inputs
# paramToLookForName = IN[0]
# paramToChangeName = IN[1]


def getNextLetter(position):
    if position > 25:  # from A to Z there are 25 chars
        return 'A' + getNextLetter(position - 26)
    return chr(ord('A') + position)


roomOptions = []
roomsHandled = []


def addRoomToOptions(room):
    try:
        index = roomsHandled.index(room)
        nextLetterPosition = roomOptions[index][1] + 1
        roomOptions[index][1] = nextLetterPosition
        return getNextLetter(nextLetterPosition)
    except ValueError:
        roomOptions.Add([room, 0])
        roomsHandled.Add(room)
        return getNextLetter(0)


# define a transaction variable and describe the transaction
t = Transaction(doc, 'rename all door names based on room they belong to')

# start a transaction in the Revit database
t.Start()

for door in doors:
    paramToLookFor = door.LookupParameter(paramToLookForName)
    paramToChange = door.LookupParameter(paramToChangeName)
    if paramToLookFor:
        paramToLookForValue = paramToLookFor.AsString()
        if paramToLookForValue:
            nextLetter = addRoomToOptions(paramToLookForValue)
            if nextLetter and paramToChange and not paramToChange.IsReadOnly:
                if pintVerbose:
                    ex.append(paramToLookForValue + " ------ " + nextLetter)
                paramToChange.Set(paramToLookForValue + " - " + nextLetter)
            else:
                err.append("Error with " + door.Name + ". Param to be changed or letter can't be calculated.")
        else:
            err.append("Error with " + door.Name + ". Param " + paramToLookForName + " not valid.")
    else:
        err.append("Error with " + door.Name + ". Param " + paramToLookForName + " not found.")

# once 1st full iteration is done, we do want to cleanup the ones only having one element. those would be named only by room name
for door in doors:
    paramToLookFor = door.LookupParameter(paramToLookForName)
    paramToChange = door.LookupParameter(paramToChangeName)
    if paramToLookFor:
        paramToLookForValue = paramToLookFor.AsString()
        if paramToLookForValue:
            try:
                paramToLookForValue = paramToLookFor.AsString()
                index = roomsHandled.index(paramToLookForValue)
                value = roomOptions[index][1]
                if value == 0 and paramToChange and not paramToChange.IsReadOnly:
                    paramToChange.Set(paramToLookForValue)
            except ValueError:
                err.append("Error with " + door.Name + ". Couldn't rename only door in a room")

# commit the transaction to the Revit database
t.Commit()

if err:
    ex.append(err)

OUT = ex
