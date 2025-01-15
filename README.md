# gmail-lazy-rules
Python script to make gmail tags and rules updated.

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