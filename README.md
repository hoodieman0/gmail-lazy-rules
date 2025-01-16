# gmail-lazy-rules
Python script to make gmail tags and rules updated.

## Usage
``` cmd
python rules.py path/to/filters.json
```

## Note
To create sublabels, use the directory format. That is parentLabel/childLabel/grandchildLabel

Order in Json is not the order jobs get done.
When updating label names, new names that conflict with existing names will cause the whole label update to abort.

## Examples
### Json
```json
{
    "labels" : [
        {
            "name" : "Testing", 
            "newName" : "Testing2.0", 
            "textColor" : "#a479e2"
        },
        {
            "name" : "Development", 
            "newName" : "Development", 
            "textColor" : "#094228"
        },
        {
            "name" : "Development/Testing", 
            "newName" : "Development/Testing", 
            "textColor" : "#16a765",
            "backgroundColor" : "#fad165"
        },
        {
            "name" : "NewTag", 
            "textColor" : "#ffffff",
            "backgroundColor" : "#0d3b44"
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
        },
        { 
            "email" : "youremail2@gmail.com", 
            "labels" : [
                "Testing", 
                "Development", 
                "Recovery Email"
                ], 
            "toInbox" : false 
        }
    ],
    "subjects" : [
        {
            "contains" : "Hello" ,
            "labels" : [ "Development" ],
            "toInbox" : false 
        },
        {
            "contains" : "World",
            "labels" : [ "Testing" ],
            "toInbox" : false 
        }
    ]
}
```