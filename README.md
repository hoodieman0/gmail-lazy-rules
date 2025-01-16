# gmail-lazy-rules

![License](https://img.shields.io/github/license/hoodieman0/gmail-lazy-rules)
![Issues](https://img.shields.io/github/issues/hoodieman0/gmail-lazy-rules)
![Contributors](https://img.shields.io/github/contributors/hoodieman0/gmail-lazy-rules?color=Red)
![LastCommit](https://img.shields.io/github/last-commit/hoodieman0/gmail-lazy-rules)

A simple Python script to automatically make gmail labels (tags) and filters 
(rules). 
Takes a formatted JSON file as an input to determine what to create or update.

Requires prior authorization of the desired Gmail account to edit.


## Usage
A valid JSON is required to run the script; see the <a href="#json">JSON</a> 
section for more information.
``` cmd
python rules.py path/to/rules.json
```

<a id="json"> </a>
## JSON Format
The following is an example JSON file to show some of the possible combinations
for inputs. The keys "labels", "senders", and "subjects" are required to exist
but do not need to be filled. 

```json
{
    "labels" : [
        {
            "name" : "Testing", 
            "newName" : "Testing2.0", 
            "textColor" : "#a479e2"
        },
        {
            "name" : "Development/Testing", 
            "newName" : "Development/Testing", 
            "textColor" : "#16a765",
            "backgroundColor" : "#fad165"
        }
    ],
    "senders" : [
        { 
            "email" : "myemail1@gmail.com", 
            "labels" : [ 
                "Development/Testing",
                "NewTag"
                ], 
            "toInbox" : false 
        }
    ],
    "subjects" : [
        {
            "contains" : "Hello World" ,
            "labels" : [ "Development" ],
            "toInbox" : false 
        }
    ]
}
```


To create sublabels, use the directory format. That is: 
"parentLabel/childLabel/grandchildLabel".

The possible values for "textColor" and 
"backgroundColor" can be found in the <a href="docs/colors.md">colors.md</a> 
files in the docs folder.

When updating label names, new names that conflict with existing names will 
cause updating the label to abort.

Do not depend on the order in the JSON to be the order labels/filters are
created. The internal implementation does not guarantee that objects come in
as shown.

## Contributing and New Features
Create an issue in Github if you would like to see a new feature added 
or would like to add a new feature.