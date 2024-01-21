import boto3
import json

def create_account_assignment():
    client = boto3.client('sso-admin')
    response = client.create_account_assignment(
      InstanceArn='[SSOインスタンスのARN]',
      PermissionSetArn='[権限セットのARN]',
      PrincipalId='[プリンシパルID]',
      PrincipalType='GROUP',
      TargetId='[AWSアカウントID]',
      TargetType='AWS_ACCOUNT'
    )
    print(f"AWS ACCOUNT {TargetId} attached successfully")
 
if __name__ == "__main__":
    create_account_assignment()
