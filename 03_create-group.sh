#!/bin/bash

# AWS SSOインスタンスのID
identity_store_id="d-95677dbddb"

# ユーザの情報
display_name="test_group"
description="test group"

# AWS SSOにユーザを追加
aws identitystore create-group \
  --identity-store-id $identity_store_id \
  --display-name $display_name \
  --description "$description"