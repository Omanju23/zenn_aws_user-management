import boto3
import json

# Identity StoreのIDを指定
identity_store_id = "[Identity StoreのID]"

groups_data = [
    {"DisplayName": "Group1", "Description": "group1 description"},
    {"DisplayName": "Group2", "Description": "group2 description"},
    {"DisplayName": "Group3", "Description": "group3 description"}
]

# AWS SSOにグループを追加
def create_group(group_data):
    client = boto3.client("identitystore")

    response = client.create_group(
      IdentityStoreId=identity_store_id,
      DisplayName=group_data["DisplayName"],
      Description=group_data["Description"]
    )

    print(f"Group {response['GroupId']} created successfully")



if __name__ == "__main__":
    
    for group_data in groups_data:
        create_group(group_data)
