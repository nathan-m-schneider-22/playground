from google.protobuf import text_format
import s_item_pb2  # Assuming the compiled protobuf file is named s_item_pb2.py

# Create SItemProperty messages
property1 = s_item_pb2.SItemProperty(propertyTypeId="Strength", propertyValue=40)
property2 = s_item_pb2.SItemProperty(propertyTypeId="Agility", propertyValue=30)
property3 = s_item_pb2.SItemProperty(propertyTypeId="Intelligence", propertyValue=50)

# Create SItem messages
item1 = s_item_pb2.SItem(
    itemUniqueId=1,
    itemId="Item1",
    primaryPropertyArray=[property1, property2]
)
item2 = s_item_pb2.SItem(
    itemUniqueId=2,
    itemId="Item2",
    primaryPropertyArray=[property2, property3]
)
item3 = s_item_pb2.SItem(
    itemUniqueId=3,
    itemId="Item3",
    primaryPropertyArray=[property1, property3]
)

# Serialize the items
serialized_item1 = item1.SerializeToString()

print(bytes(serialized_item1))
f = open("export.bin",'wb')
f.write(bytes(serialized_item1))
serialized_item2 = item2.SerializeToString()
serialized_item3 = item3.SerializeToString()

# Deserialize the items
deserialized_item1 = s_item_pb2.SItem()
deserialized_item2 = s_item_pb2.SItem()
deserialized_item3 = s_item_pb2.SItem()

deserialized_item1.ParseFromString(serialized_item1)
deserialized_item2.ParseFromString(serialized_item2)
deserialized_item3.ParseFromString(serialized_item3)

# Print the deserialized messages
# print(text_format.MessageToString(deserialized_item1))
# print(text_format.MessageToString(deserialized_item2))
# print(text_format.MessageToString(deserialized_item3))
