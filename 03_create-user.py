import boto3
import json

# AWS SSOインスタンスのID
identity_store_id = "d-97675f6d9e"

# ユーザ情報を読み込む
user_info_file = "user_info.json"

# AWS SSOにユーザを追加
def create_user(user_data):
    client = boto3.client("identitystore")

    # 1つ目のメールアドレスのみを使うように修正
    primary_email = user_data["emails"][0]

    response = client.create_user(
        IdentityStoreId=identity_store_id,
        UserName=user_data["user_name"],
        Name=user_data["name"],
        Emails=[
            {
                "Primary": primary_email["Primary"],
                "Type": primary_email["Type"],
                "Value": primary_email["Value"],
            }
        ],
        DisplayName=user_data.get("displayname", ""),  
        PreferredLanguage=user_data.get("language", "en-US"),
    )
    
    # 作成されたユーザのIDを取得
    user_id = response["UserId"]  
    
    print(f"User {user_data['user_name']} created successfully")

    # ListGroups APIを使用してグループの情報を取得
    groups_response = client.list_groups(IdentityStoreId=identity_store_id)
    group_id_mapping = {group["DisplayName"]: group["GroupId"] for group in groups_response.get("Groups", [])}

    # グループへの紐づけ
    for group_name in user_data.get("groups", []):
        group_id = group_id_mapping.get(group_name)
        if group_id:
            response = client.create_group_membership(
                IdentityStoreId=identity_store_id,
                GroupId=group_id,
                MemberId={
                    'UserId': user_id
                }
            )
            print(f"User {user_data['user_name']} added to Group {group_name} successfully")
        else:
            print(f"Error: Group ID not found for Group {group_name}")



if __name__ == "__main__":
    with open(user_info_file, "r") as file:
        users_data = json.load(file)

    for user_data in users_data:
        create_user(user_data)
