#!/bin/bash

# AWS SSOインスタンスのID
identity_store_id="d-9067f0aaba"

# ユーザ情報を読み込む
user_info_file="user_info.json"
users=$(jq -c '.[]' $user_info_file)

# 各ユーザを作成
for user in $users; do
  user_name=$(echo "$user" | jq -r '.user_name')
  email=$(echo "$user" | jq -r '.email')
  language=$(echo "$user" | jq -r '.language')

  # AWS SSOにユーザを追加
  aws identitystore create-user \
    --identity-store-id $identity_store_id \
    --user-name "$user_name" \
    --email "$email" \
    --preferred-language "$language"
done
