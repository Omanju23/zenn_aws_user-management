import boto3
import json

def create_permission_set(instance_arn):
    client = boto3.client('sso-admin')
    response = client.create_permission_set(
        Description='test',
        InstanceArn=instance_arn,
        Name='group1-permission-set',
        Tags=[
            {
                'Key': 'Name',
                'Value': 'group1-permission-set'
            },
        ]
    )
    print(f"Permission Set {response['PermissionSet']['Name']} created successfully")
    
    return response['PermissionSet']['PermissionSetArn']

def attach_managed_policy_to_permission_set(instance_arn,permission_set_arn):
    client = boto3.client('sso-admin')
    response = client.attach_managed_policy_to_permission_set(
        InstanceArn=instance_arn,
        ManagedPolicyArn='arn:aws:iam::aws:policy/PowerUserAccess',
        PermissionSetArn=permission_set_arn
    )
    print(f"Managed Policy attached successfully")
 
if __name__ == "__main__":
    instance_arn = "[Identity CenterのインスタンスARN]"
    permission_set_arn = create_permission_set(instance_arn)
    attach_managed_policy_to_permission_set(instance_arn,permission_set_arn)
