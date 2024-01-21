import boto3
import json

def create_account_assignment():
    client = boto3.client('sso-admin')
    response = client.create_account_assignment(
      InstanceArn='arn:aws:sso:::instance/ssoins-82596254a057c153',
      PermissionSetArn='arn:aws:sso:::permissionSet/ssoins-82596254a057c153/ps-926cd4002a525b71',
      PrincipalId='396e9428-d0e1-7080-315c-bce7c30554e7',
      PrincipalType='GROUP',
      TargetId='471112574468',
      TargetType='AWS_ACCOUNT'
    )
    print(f"AWS ACCOUNT {TargetId} attached successfully")
 
if __name__ == "__main__":
    create_account_assignment()
