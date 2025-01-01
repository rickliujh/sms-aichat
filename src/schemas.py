INPUT = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$id": "http://example.com/example.json",
    "type": "object",
    "title": "Sample input schema",
    "description": "The Document generation path parameters, Document Type and Customer ID.",
    "required": ["pathParameters"],
    "properties": {
        "pathParameters": {
            "$id": "#/properties/pathParameters",
            "type": "object",
            "required": ["docType", "customerId"],
            "properties": {
                "docType": {
                    "$id": "#/properties/pathParameters/docType",
                    "type": "string",
                    "title": "The Document Type to Generate",
                    "examples": ["TestDoc", "WELCOME"],
                    "maxLength": 30,
                },
                "customerId": {
                    "$id": "#/properties/pathParameters/customerId",
                    "type": "string",
                    "title": "The Customer ID to send the document",
                    "examples": ["TestCustomer", "TestCustomer01"],
                    "maxLength": 30,
                },
            },
        }
    },
}
