# gmail-lazy-rules
Python script to make gmail tags and rules updated.

## Examples
### Json
```json
{
    "request" : [
        { 
            "email" : "myemail1@gmail.com", 
            "labels" : [
                "Testing", 
                "Development"
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
    ]
}
```