# Publish and Verify

## Publish

Publishing the election artifacts helps ensure third parties can verify the election. `publish.py` provides a publish method that serializes the key election artifacts. This makes use of the `Serializable` class exists to allow easy serializing to json files. These JSON files can then be shared and sent so others can verify. 

## Verify

Deserializing is the first step to verification. The `from_json` and `from_json_file` methods on `Serializable` are available to deserialize output JSON files back into their original classes. 
