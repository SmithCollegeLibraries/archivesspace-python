schema-research.md

The goal of this rabbit hole is to automagically define the fields in each object in python so that these don't have to be manually coded.
I can instead rely on the ArchivesSpace API to do the validation I suppose. I hope that the error reporting is good?

ArchivesSpace uses a JSON schema to validate fields (I think)
https://github.com/archivesspace/archivesspace/tree/master/common/schemas

It uses Draft 3 of the JSON schema spec
I was able to load a json schema validator for python and run it against one of the schemas.
https://pypi.python.org/pypi/jsonschema

See TEST_schema.py

I was able to turn ArchivesSpace's ruby JSON schema to real JSON by serializing it:

require 'json'
print(JSON.dump schema)

However the Python JSON parser was having issues with this output. I ended up just converting it into Python code.

Problems:
ArchivesSpace doesn't keep the schema in actual JSON but rather ruby code.
This would need to be converted to real JSON or Python.

ArchivesSpace adds a bespoke "ifmissing" rule to the schema.
https://github.com/archivesspace/archivesspace/blob/master/common/archivesspace_json_schema.rb
I would have to add an additional check to the schema validator to use this.

I'm not sure why they didn't just use "required"?!


http://json-schema.org/documentation.html
https://stackoverflow.com/questions/8307602/programmatically-generate-methods-for-a-class
