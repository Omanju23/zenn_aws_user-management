#!/bin/bash

# Identity StoreのIDを指定
identity_store_id = "[Identity StoreのID]"

# ユーザの情報
display_name="test_group"
description="test group"

# AWS SSOにユーザを追加
aws identitystore create-group \
  --identity-store-id $identity_store_id \
  --display-name $display_name \
  --description "$description"