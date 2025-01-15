# gmail-lazy-rules
Python script to make gmail tags and rules updated.

## Usage
``` cmd
python rules.py path/to/filters.json
```

## Note
To create sublabels, use the directory format. That is parentLabel/childLabel/grandchildLabel

## Examples
### Json
```json
{
    "senders" : [
        { 
            "email" : "myemail1@gmail.com", 
            "labels" : [
                "Testing", 
                "Development"
                ], 
            "toInbox" : true 
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