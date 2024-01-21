# 対象読者
* AWSのユーザ管理方式を検討している人/改善したいと考えている人
* Organizations有無によるIdentity Centerの機能差を理解したい人
* 各種方式のIaCスクリプトサンプルが欲しい人
* Identity Centerの初期セットアップについて知りたい人


# きっかけ
先日、従前までOrganizationsの利用が必須条件だったIdentity Centerが、Organizationsを利用せずとも利用できるようになりました。
https://aws.amazon.com/jp/about-aws/whats-new/2023/11/aws-iam-identity-center-account-instance-evaluation-adoption-managed-applications/

Organizationsを必要としないシステムについてもIdentity Centerが利用できるようになったことで、ユーザ管理方式の幅が広がり、最適な方式を探りたくなったので比較・検証してみることとします。


# 先に結論
個人的には拡張性を考慮するとOrganizationsありでIdentity Centerを利用するのがベストかなと感じました。
ある程度IAMを理解して設計している方であれば、Identity Center自体はそこまで複雑ではないですし、初期構築もステップこそ多いですがほかのメリットを押しのけてまで不採用にするほどではありません。

以下検証結果のまとめ表です。

| 方式 | 初期構築容易性 | 運用性 | 堅牢性 | その他拡張性 |
| ---- | :----: | :----: | :----: | :----: |
| IAMユーザ | ○ | △ | △ | × |
| IAMユーザ＋Role | ○ | ○ | △ | × |
| Identity Center（Organizationsなし） | - | - | - | △ |
| Identity Center（Organizationsなし） | △ | ○ | ○ | ○ |

以降は各方式の説明や検証内容、IaCコード等を備忘的に整理しています。

::: message
本記事を読み進めていくとわかりますが、アカウントインスタンス（OrganizationsなしのIdentity Centerインスタンス）はIAMユーザの代替にすることはできません。（[アカウントインスタンスには権限セットが作成できないことが判明…
](#%E3%82%A2%E3%82%AB%E3%82%A6%E3%83%B3%E3%83%88%E3%82%A4%E3%83%B3%E3%82%B9%E3%82%BF%E3%83%B3%E3%82%B9%E3%81%AB%E3%81%AF%E8%A8%B1%E5%8F%AF%E3%82%BB%E3%83%83%E3%83%88%E3%81%8C%E4%BD%9C%E6%88%90%E3%81%A7%E3%81%8D%E3%81%AA%E3%81%84%E3%81%93%E3%81%A8%E3%81%8C%E5%88%A4%E6%98%8E%E2%80%A6)）今後のアップデートに期待です…
:::
# ユーザ管理方式と比較観点
本記事で検証を進めていく管理方式とその比較観点について記載します。
## ユーザ管理方式

| 方式 | 説明 |
| ---- | ---- |
| IAMユーザ | IAMユーザをグループに所属させ、<br>グループの権限の範囲で各種操作を行う方式 |
| IAMユーザ＋Role | IAMグループにSwitch Roleを行うだけのの最小限の権限を与え、<br>権限を必要とする運用ははAssume Roleを利用して行う方式 <br>個人的に最もよく利用する構成 |
| Identity Center | 今回追加されたOrganizationsなしでIdentity Centerを利用する方式<br>IAMユーザは持たない |
| Identity Center＋<br>外部Idp | OrganizationsありでIdentity Centerを利用する方式<br>IAMユーザは持たない |

## 比較観点
| 観点 | 説明 |
| ---- | ---- |
| 初期構築容易性 | 初期構築の難易度を評価 |
| 運用性 | ユーザの追加・削除、ユーザを用いた運用性を評価 |
| 堅牢性（セキュリティ） | 外部からの攻撃や情報流出時の堅牢性を評価 |
| その他拡張性 | その方式特有の優位点を評価 |


# 比較
今回は各方式で以下のよくある運用を実施することで、各比較観点を検証していきます。
* 初期構築
* ユーザ追加および担当者へのログイン情報の配布
* CLIを使った操作
* Session Managerを利用したサーバログイン
* ユーザの削除

## IAMユーザ
### 初期構築容易性
担当者がログインできるまでに以下のステップで構築を行います。

1. rootユーザーでIAMユーザ/グループを作成します。
2. IAMグループに対してポリシーを作成して権限を割り当てます。
3. IAMユーザのID/PWを担当者に展開します。

ステップが非常に少なく、CFnのテンプレートを作ってしまえば一瞬で片が付くので非常に構築が容易だといえます。

今回は以下のCFnテンプレートを利用して構築を行いました。
CFnに対応しているので、ユーザ数が増えてもお手軽にスケールできることはこの構成の優れた点だと考えます。
::: details iamテンプレート
```yaml
---
---
AWSTemplateFormatVersion: "2010-09-09"
Description: A sample template
Resources:
  # IAMUser用のグループ
  IAMGroup:
    Type: AWS::IAM::Group
    Properties:
      GroupName: test-group

  IAMPolicy:
    Type: 'AWS::IAM::Policy'
    Properties:
      PolicyName: test-policy
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Action:
              - "ec2:*"
              - "ssm:*"
              - "iam:ChangePassword"
            Resource: '*'
            Condition:
              BoolIfExists:
                aws:MultiFactorAuthPresent: 'true'
      Groups:
        - !Ref IAMGroup

  IAMPolicy2:
    Type: 'AWS::IAM::Policy'
    Properties:
      PolicyName: test-policy2
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Action:
              - "iam:ChangePassword"
            Resource: '*'
      Groups:
        - !Ref IAMGroup
  # IAMUser
  IAMUser:
    Type: AWS::IAM::User
    Properties:
      Groups: 
        - test-group
      LoginProfile: 
        Password: ************
        PasswordResetRequired: true
      UserName: test-user
```
:::
:::message
ただし、CFnの場合パスワードのランダマイズはできなさそうなので、担当者以外の人間も初期PWを知ってしまう可能性があるので注意が必要です。
:::

### 運用性
#### 1. ユーザの追加
先述の通り追加は非常に簡単です。

#### 2. CLI操作および、Session Managerでのサーバ接続
AWS CLIを利用してローカル環境でポートフォワードを構成し、サーバに接続してみます。
まずローカル環境でAWS CLIを利用するための長期的なアクセスキーを払い出します。

![](https://storage.googleapis.com/zenn-user-upload/404080d58ebe-20240101.png)
:::message
警告文の通り、長期的なアクセスキーを払い出すことはベストプラクティスから逸しているので推奨されていません。
:::

次にローカル環境のホームディレクトリの.aws/credentialsに払い出し済みのアクセスキー/シークレットアクセスキーを設定します。

![](https://storage.googleapis.com/zenn-user-upload/30a44b50518d-20240101.png)

CLIを用いてポートフォワーディングを構成し、Teratermを用いてターゲットに接続を試行します。
正常にポートフォワーディングが構成でき、ログインプロンプトが起動したことが確認できました。
::: details CLIコマンド
``` powershell
aws ssm start-session --target i-07d93d09436a5471d --document-name AWS-StartPortForwardingSession --parameters portNumber=22,localPortNumber=10022
```
:::
![](https://storage.googleapis.com/zenn-user-upload/ad697ab4bbbe-20240101.gif)


#### 3. ユーザの削除
IAMユーザ自体を削除してしまえば、払い出し済みのアクセスキーも無効化されるため、後片付けも非常に容易といえるでしょう。
![](https://storage.googleapis.com/zenn-user-upload/b48f64d7fe34-20240101.png)

::: message
cloud formationでユーザを削除する際には、MFAデバイスを削除してからでないとIAMユーザの削除に失敗します。

:::

### 堅牢性
アカウントID、ユーザ名、PWの3つの要素が流出すると、ユーザの権限で悪意のあるオペレーションを実行されてしまいます。

またMFAデバイスを強制するためのハードルが少し高いです。
後述するAssume Role方式では、Assume Roleアクションを定義するポリシーに対してCondition句でMFAデバイスを強制させればよいのですが、グループとユーザのみであると、許可するアクションに対してCondition句をつけなければなりません。このため、AWSのマネージドポリシーをそのまま使いづらいため、MFAデバイスを強制するためのハードルが高いと表現しています。


### 可監査性
運用性でStartSessionコマンドを発行した際のAPIアクションがCloud Trailに記録されています。
ユーザ名とアクションが特定できましたので、監査可能な状態といえるでしょう。
![](https://storage.googleapis.com/zenn-user-upload/66ecb60a9833-20240101.png)

### その他拡張性
特にありません。

## IAMユーザ ＋ Role
### 初期構築容易性
担当者がログインできるまでに以下のステップで構築を行います。

1. rootユーザーでIAMユーザ/グループを作成します。
2. IAMグループに対してポリシーを作成して権限を割り当てます。ここでスイッチ先のRoleを指定sするとともに、MFAデバイスを強制します。
3. ユーザがスイッチする先のRoleを作成します。信頼ポリシーに構築先アカウントのIAMユーザが引き受けられるように設定します。Roleに付与するポリシーにはMFAを強制するCondition句を付与しなくてもよいため、AWSマネージドなポリシーを付与することも可能です。
4. IAMユーザのID/PWを担当者に展開します。

IAMユーザのみの方式と比較し、1ステップ増えはしましたが、こちらも難易度は高くないといえるでしょう。
加えてMFAデバイスの強制をassume roleアクションだけに絞っているため、実際に運用で利用するポリシーをシンプルに保つことができます。

### 運用性
#### 1. ユーザの追加
IAMユーザのみの方式と同じく、IAMグループにユーザを追加するだけでよいので非常に簡単です。

#### 2. CLI操作および、Session Managerでのサーバ接続
今回は引き受けられるRoleが存在するので、長期的なアクセスキーを払い出さずとも接続することが可能です。
以下のコマンドを発行することで一時的なクレデンシャルを発行します。

```a:AWS CLI
 aws sts assume-role --role-arn arn:aws:iam::447491875444:role/test2-role --role-session-name test
```

```a:戻り値
{
    "Credentials": {
        "AccessKeyId": "AS*************",
        "SecretAccessKey": "mSu**************************",
        "SessionToken": "IQoJb3JpZ2luX2VjEKb//////////wEaCXVzLWVhc3QtMSJIMEYCIQCdABtg8okGGUMOpZPsBieBGRdPeItF6198gJAGV2YhwwIhAKLnG7evEpYj3TPKPf+L1n9z0bmm1IepUdtT/1+Wa9R5KpUCCD4QABoMNDQ3NDkxODc1NDQ0Igz/B2n7NHaWIMvydLkq8gFOJaWqagap3PwmY+w7uElcLOUuark4vbCLDpHAlDLLWeSIdpjY7h8p0BfnRDkJosz+fZbvqL14uNoucwxHVrqbe4c/lVIq1KVuhQi/GxbQe6doq8rkSpTC0xtcLuNCh9Z4OfZ6WMG/i5XGlOGLxXqdjpfG0/ksNAJpOBxb927PY57WeWw9ZPygtX6WsL45uR1NkJ/4FWOQnpHer5ssoqy8vwP4VuA1decK13yDZJd4jX/aOyxJeBxnhm2Mhs+pbpVnh42a5uBG5k4uUg/wdHh7LLFtet+76neAG99ss69Eg2ptJmEf2+ZbuDvIlJIaAokHTTD6ss6sBjqcAXHNOGg1SBTEX54osLl1oTb1ci3yHOl5OFhIJz1UO0d1AehLYtZ7R4Usvy4eoI9yGm+L5qs6TV1v+C0qhCNFIDo+SS3WfEtMu03gQWQqFxGgWO1r91bAPkN5Ivr0wGCLWM0Lg8KbYUQ43vnDYrS0bPBpYbHPiE5Tbw4*************",
        "Expiration": "2024-01-02T06:04:58+00:00"
    },
    "AssumedRoleUser": {
        "AssumedRoleId": "AROAWQMEYEJ2AOGSFBHCP:test",
        "A
```

上記で取得したアクセスキー、シークレットアクセスキー、セッショントークンを~.aws/credentialsに記載します。
![](https://storage.googleapis.com/zenn-user-upload/18d46baa9dcc-20240102.png)

その後はIAMユーザの時同様、AWS CLIを用いてポートフォワーディングを構成し、接続します。
![](https://storage.googleapis.com/zenn-user-upload/cc9b6ab9aa4c-20240102.gif)

#### 3. ユーザの削除
こちらも先と同様、IAMユーザを削除してしまえばよいため、後片付けも非常に容易といえるでしょう。
::: message
Assume Roleで払い出された一時クレデンシャル情報は、ユーザーを削除した後もクレデンシャルの有効期限までは再利用可能なようなのでご注意ください。
![](https://storage.googleapis.com/zenn-user-upload/b3cfbb75b860-20240102.gif)
:::

### 堅牢性
この構成でAWS CLIを使って何かを実施する必要がある場合、2つの方式をとることができます。
1つは先と同じ、長期的なアクセスキーの払い出し。
2つ目はAssume Roleを利用した一時的なアクセスキーの払い出し。こちらはCloud Shell等でAssume Roleを行い、一時的なクレデンシャルを取得します。運用性の2.で利用していた手方式ですね。
こちらは長期的なアクセスキーの払い出しと比較して堅牢といえるでしょう。

### 可監査性
ユーザのみと比較すると1step増えますが、Cloud Trailのみで監査可能です。
以下画像の左側がAssumeRoleアクションの履歴です。
test2-userで実施されていることがわかります。
右側のイベントがStartSessionアクションの履歴です。
ユーザ名がtestとなっていますが、こちらはAssumeRole時に指定したセッションの名前に対応しています。
![](https://storage.googleapis.com/zenn-user-upload/a5c521041acb-20240102.png)

こちらはCloud TrailのAssumeRoleアクションのイベントレコードから確認することができます。
![](https://storage.googleapis.com/zenn-user-upload/3c5b99a4995f-20240102.png)

上記の通り、AssumeRole後のアクションとAssumeRole時のセッション名の紐づけという1stepが入るものの監査可能であるといえます。

### その他拡張性
特になし

## Identity Center（Organizationsなし）

### 初期構築容易性
以下の流れで構築します。
1. Identity Centerの有効化
2. Identity Centerの設定（Create UserAPI利用時のOTP、MFAデバイスの強制）
3. グループの作成
4. ユーザの作成
5. 権限セットの作成

1.Identity Centerの有効化
まずはIdentity Centerを有効化します。
トップページから「有効化」をクリックします。
![](https://storage.googleapis.com/zenn-user-upload/66b59296c246-20240102.png)

Organizationsありとなしの2択を選択できますが、今回はなしを選択します。
![](https://storage.googleapis.com/zenn-user-upload/0d89808f5e6f-20240102.png)

必要に応じてタグを追加し、再度「有効化」をクリックします。
![](https://storage.googleapis.com/zenn-user-upload/7a39c433c781-20240102.png)

するとしばらくたつとリソースの構築が完了し、ダッシュボードが開きます。
![](https://storage.googleapis.com/zenn-user-upload/126ac73ce24c-20240102.png)

・・・中略（一応こちらに検証のログは残しておきます）・・・

5. 権限セットの作成
Identity CenterのAPIリファレンスから、CreatePermissionSet APIをたたいて権限セットを作ろうとしました…

https://docs.aws.amazon.com/ja_jp/singlesignon/latest/APIReference/API_CreatePermissionSet.html

```
[cloudshell-user@ip-10-132-39-203 ~]$ ls -l
total 4
-rw-r--r--. 1 cloudshell-user cloudshell-user 1193 Jan  6 08:28 create-permissionset.py
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ cat create-permissionset.py 
import boto3
import json

def create_permission_set(instance_arm):
    client = boto3.client('sso-admin')
    response = client.create_permission_set(
        Description='test',
        InstanceArn=instance_arm,
        Name='group1-permission-set',
        Tags=[
            {
                'Key': 'Name',
                'Value': 'group1-permission-set'
            },
        ]
    )
    print(f"Permission Set {response['name']} created successfully")
    
    return response['PermissionSet']['PermissionSetArn']

def attach_managed_policy_to_permission_set(instance_arm,permission_set_arn):
    client = boto3.client('sso-admin')
    response = client.attach_managed_policy_to_permission_set(
        InstanceArn=instance_arm,
        ManagedPolicyArn='arn:aws:iam::aws:policy/PowerUserAccess',
        PermissionSetArn=permission_set_arn
    )
    print(f"Managed Policy {response['name']} attached successfully")
 
if __name__ == "__main__":
    instance_arm = "arn:aws:sso:::instance/ssoins-72231698d13b8cc7"
    permission_set_arn = create_permission_set(instance_arm)
    attach_managed_policy_to_permission_set(instance_arm,permission_set_arn)
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ python create-permissionset.py 
Traceback (most recent call last):
  File "/home/cloudshell-user/create-permissionset.py", line 32, in <module>
    permission_set_arn = create_permission_set(instance_arm)
  File "/home/cloudshell-user/create-permissionset.py", line 6, in create_permission_set
    response = client.create_permission_set(
  File "/usr/local/lib/python3.9/site-packages/botocore/client.py", line 535, in _api_call
    return self._make_api_call(operation_name, kwargs)
  File "/usr/local/lib/python3.9/site-packages/botocore/client.py", line 980, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.errorfactory.ValidationException: An error occurred (ValidationException) when calling the CreatePermissionSet operation: The operation is not supported for this Identity Center instance
```

### アカウントインスタンスには権限セットが作成できないことが判明…
**The operation is not supported for this Identity Center instance**
なんとOrganizationsなしのIdentity Center Instanceには非対応でした…
確かにリリース記事をよく読んでみるとマネージドアプリケーションへの対応にしか言及されていませんでした…
> これによりお客様は、Amazon CodeCatalyst など、サポートされている AWS マネージドアプリケーションをすばやく評価できるようになります。

ダメ押しにドキュメントにもAWSアカウントへのアクセスはサポートされない旨の記載がありました…
> Account instances don't support permission sets and therefore don't support access to AWS accounts.

https://docs.aws.amazon.com/singlesignon/latest/userguide/account-instances-identity-center.html#supported-aws-applications

この記事を書くきっかけになった方式が実現できなかったことを知ってショックですが、引き続き検証を続けていきます。

## Identity Center（Organizationsあり）

### 初期構築容易性
以下の流れで構築します。
1. Identity Centerの有効化
2. Identity Centerの設定（Create UserAPI利用時のOTP、MFAデバイスの強制）
3. グループの作成
4. ユーザの作成
5. 権限セットの作成
6. アカウントアサイン


#### 1. Identity Centerの有効化
Identity Center（Organizationsなし）と同様にIdentity Center インスタンスを起動します。
今回は「AWS Organizationsで有効にする」を選択します。
![](https://storage.googleapis.com/zenn-user-upload/2ffcc3dc677f-20240108.png)

数分後作成されました。
![](https://storage.googleapis.com/zenn-user-upload/d436cc7445df-20240108.png)

#### 2. Identity Centerの設定（Create UserAPI利用時のOTP、MFAデバイスの強制）
次にIdentity Centerの設定を行います。
左ペインから「設定」を選択します。

まずはCreate UserAPI利用時のOTP送信を有効化します。
こちらはユーザ作成をCLIやSDK等で行う際に利用します。詳細は後述します。
![](https://storage.googleapis.com/zenn-user-upload/91df4d05e5c4-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/a351ea0b20d5-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/0c7e7fa5e5a2-20240108.png)

続いてMFAの強制について設定します。
デフォルト設定は以下の通りです。
初回サインイン時にMFAデバイスの登録が強制されており、以降はサインインコンテキストが変更された場合のみ要求されます。

![](https://storage.googleapis.com/zenn-user-upload/09694a1b2744-20240108.png)

今回は他の方式に揃えて「サインインごと」に変更しました。
![](https://storage.googleapis.com/zenn-user-upload/c15b69b7177a-20240102.png)
![](https://storage.googleapis.com/zenn-user-upload/70d0080a7aee-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/e2db5e890eb0-20240108.png)

#### 3. グループの作成
Identity CenterやIdentity StoreはCloudFormationが対応していない部分が多いため、各種APIをSDKから叩いていくことにします。
グループの作成にはIdentity StoreのCreateGroup APIを利用します。
https://docs.aws.amazon.com/singlesignon/latest/IdentityStoreAPIReference/API_CreateGroup.html


::: details create-group.py
```python
import boto3
import json

# Identity StoreのIDを指定
identity_store_id = "d-********"

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
```
:::

Identity StoreのIDは設定のアイデンティティソースに記載があります。以下の右下部分に見えるd-で始まるIDです。
![](https://storage.googleapis.com/zenn-user-upload/d96dc4780887-20240102.png)


上記スクリプトをCloud Shell上で実行し、グループを正常に作成することができました。
![](https://storage.googleapis.com/zenn-user-upload/0d823b903166-20240108.png)


::: message
Identity Centerを関連のAPIは、IdpとしてのIdentity Storeと、権限セットやアカウントアサイン設定などをつかさどるIdentity Centerの2つがあります。
Identity Center側だけを見ているとユーザ作成のAPIが見つからないので要注意です。
:::

#### 4. ユーザの作成
続いてグループに所属させるユーザの作成を行います。
こちらもIdentity StoreのAPIであるCreateUser APIを利用します。
https://docs.aws.amazon.com/singlesignon/latest/IdentityStoreAPIReference/API_CreateUser.html

ユーザの作成とグループへの所属までを行うスクリプトを作成しました。
運用も見据えてユーザ固有の定義はJSONに外だししています。

::: details create-user.py
```
import boto3
import json

# Identity StoreのIDを指定
identity_store_id = "d-*******"

# ユーザ情報を読み込む
user_info_file = "user_info.json"

# AWS SSOにユーザを追加
def create_user(user_data):
    client = boto3.client("identitystore")

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

```
:::

::: details user_info.json
```json
[
  {
    "user_name": "user1",
    "name": {
      "Formatted": "John Doe",
      "FamilyName": "Doe",
      "GivenName": "John"
    },
    "emails": [
      {
        "Primary": true,
        "Type": "Work",
        "Value": "john.doe@example.com"
      }
    ],
    "displayname": "John Doe",
    "language": "en-US",
    "groups": ["Group1","Group2"]
  },
  {
    "user_name": "user2",
    "name": {
      "Formatted": "Jane Smith",
      "FamilyName": "Smith",
      "GivenName": "Jane"
    },
    "emails": [
      {
        "Primary": true,
        "Type": "Work",
        "Value": "***************@gmail.com"
      }
    ],
    "displayname": "Jane Smith",
    "language": "ja-JP",
    "groups": ["Group1","Group3"]
  }
]
```
:::

こちらもCloud Shellで実行し、2人のユーザを作成することができました。
![](https://storage.googleapis.com/zenn-user-upload/21c85dcdb26c-20240108.png)

#### 5. 権限セットの作成
続いて先ほどまでに作成したユーザに与える権限セットを作成します。
こちらはIdentity CenterのCreatePermissionSet APIとAttachManagedPolicytoPermissionSet APIを利用します。
前者を使い権限セットを作成し、後者を使って作成した権限セットにマネージドポリシーを割り当てます。

::: details create-permission-set.py
``` python
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
    instance_arn = "arn:aws:sso:::instance/************"
    permission_set_arn = create_permission_set(instance_arn)
    attach_managed_policy_to_permission_set(instance_arn,permission_set_arn)

```

こちらもCloud Shell上で実行し、権限セットを作成しました。
![](https://storage.googleapis.com/zenn-user-upload/513fb555d2a7-20240108.png)


#### 6. アカウントアサイン
最後に作成した許可セットを適用するAWSアカウントとプリンシパルをアサインします。
こちらはIdentity CenterのCreateAccountAssignment APIを用います。

https://docs.aws.amazon.com/ja_jp/singlesignon/latest/APIReference/API_CreateAccountAssignment.html
::: details create-account-assignment.py
import boto3
import json

def create_account_assignment():
    client = boto3.client('sso-admin')
    response = client.create_account_assignment(
      InstanceArn='arn:aws:sso:::instance/*****************
      PermissionSetArn='arn:aws:sso:::permissionSet/*****************',
      PrincipalId='*****************',
      PrincipalType='GROUP',
      TargetId='4*************',
      TargetType='AWS_ACCOUNT'
    )
    print(f"AWS ACCOUNT attached successfully")
 
if __name__ == "__main__":
    create_account_assignment()

:::

こちらも無事作成できました。
![](https://storage.googleapis.com/zenn-user-upload/9ad194b66bba-20240108.png)

これをもってグループ1に所属するユーザは、AWSアカウント（4**************）に対して、権限セット（group1-permission-set）に含まれる権限（PowerUserAccess）を行使できるようになります。



### 運用性
#### 1．ユーザの作成
[Identity Center（Organizationsあり）/ 4. ユーザの作成
](#4.-%E3%83%A6%E3%83%BC%E3%82%B6%E3%81%AE%E4%BD%9C%E6%88%90)で行ったように、APIが用意されているので、スクリプトを作ってしまえば作成は非常に簡単といえるでしょう。

#### 2.
Identity Centerの優れた点の1つと考えているのがこの機能です。
SSOポータルからクレデンシャル取得
![](https://storage.googleapis.com/zenn-user-upload/cb51278e099f-20240108.png)

### 堅牢性


![](https://storage.googleapis.com/zenn-user-upload/196a04cc3b48-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/58d3fbb531df-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/290d3af0e6c9-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/087d37e4e451-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/0bfab873a4dc-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/345864e7aaf8-20240108.png)
![](https://storage.googleapis.com/zenn-user-upload/7175f0c2efbc-20240108.png)

### 可監査性


### その他拡張性
特にありません。
### ログイン



# まとめ
| 方式 | 初期構築容易性 | 運用性 | 堅牢性 | その他拡張性 |
| ---- | :----: | :----: | :----: | :----: |
| IAMユーザ | ○ | △ | △ | × |
| IAMユーザ＋Role | ○ | △ | △ | × |
| Identity Center | - | - | - | △ |
| Identity Center＋<br>外部Idp | △ | ○ | ○ | ○ |

[^1]: アプリケーションへの対応が


---

### 徒労に終わった検証ログを供養します

2. Identity Centerの設定（Create UserAPI利用時のOTP、MFAデバイスの強制）
次にIdentity Centerの設定を行います。
左ペインから「設定」を選択します。
![](https://storage.googleapis.com/zenn-user-upload/5f5b83f9ed6a-20240102.png)

まずはCreate UserAPI利用時のOTP送信を有効化します。
こちらはユーザ作成をCLIやSDK等で行う際に利用します。詳細は後述します。
![](https://storage.googleapis.com/zenn-user-upload/2f2571e328e0-20240102.png)

続いてMFAの強制について設定します。
デフォルト設定は以下の通りです。
初回サインイン時にMFAデバイスの登録が強制されており、以降はサインインコンテキストが変更された場合のみ要求されます。

![](https://storage.googleapis.com/zenn-user-upload/fc1b415b36bc-20240102.png)

今回は他の方式に揃えて「サインインごと」に変更しました。
![](https://storage.googleapis.com/zenn-user-upload/c15b69b7177a-20240102.png)

3. グループの作成
続いてグループの作成です。ここからはAWS CLIを活用していきます。
他の方式ではCloudFormationを利用していましたが、2024年1月2日時点ではIdentity Centerには未対応のようなので、Create Group APIをboto3で叩きます。
https://docs.aws.amazon.com/singlesignon/latest/IdentityStoreAPIReference/API_CreateGroup.html

まず、グループが作成されていないことを確認します。
![](https://storage.googleapis.com/zenn-user-upload/125b433c7f7a-20240102.png)

次にCLIの引数として必要なIDストアIDを確認します。
設定のアイデンティティソースに記載があります。以下の右下部分に見えるd-で始まるIDです。
![](https://storage.googleapis.com/zenn-user-upload/d96dc4780887-20240102.png)

実行してみます。
``` CLI:create-group.sh
[cloudshell-user@ip-10-132-39-203 ~]$ ls -l create-group.py
-rw-r--r--. 1 cloudshell-user cloudshell-user 794 Jan  6 07:26 create-group.py
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ cat create-group.py
import boto3
import json

# AWS SSOインスタンスのID
identity_store_id = "d-9067f0aaba"

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
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ python create-group.py
Group b4a88488-b031-708a-8ad8-75f15d2267eb created successfully
Group c4e81478-0021-70dc-e9b6-334c99c00332 created successfully
Group 4448c4b8-d0f1-70ce-aebe-fadd4baa3e93 created successfully
[cloudshell-user@ip-10-132-39-203 ~]$ 
```

正常に作成することができました。
![](https://storage.googleapis.com/zenn-user-upload/18a3a43b45c6-20240106.png)

4. ユーザの作成
続いてユーザを作成し、グループにマッピングします。
bashでJSONを取り扱うのが大変だったので、今回はpythonのSDKを使って作成しています。


ユーザがいないことを確認。
![](https://storage.googleapis.com/zenn-user-upload/7820ba50ea3a-20240102.png)

ユーザ情報を定義するJSONファイルをpythonスクリプトが読み込んで、Create User APIおよび、CreateGroupMembership APIをたたくことでユーザを作成します。
https://docs.aws.amazon.com/singlesignon/latest/IdentityStoreAPIReference/API_CreateUser.html
https://docs.aws.amazon.com/singlesignon/latest/IdentityStoreAPIReference/API_CreateGroupMembership.html

ユーザの定義ファイルとして「user_info.json」をpythonスクリプトと同じディレクトリに置くことでjsonを読み込み、複数のユーザを一気に作成します。
::: details Cloud Shell
```python
[cloudshell-user@ip-10-132-39-203 ~]$ cat create-user.py 
import boto3
import json

# AWS SSOインスタンスのID
identity_store_id = "d-9067f0aaba"

# ユーザ情報を読み込む
user_info_file = "user_info.json"

# グループ名とグループIDのマッピング
group_mapping = {
    "Group1": "group_id_1",
    "Group2": "group_id_2",
    "Group3": "group_id_3"
}

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
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ 
[cloudshell-user@ip-10-132-39-203 ~]$ python create-user.py 
User user1 created successfully
User user1 added to Group Group1 successfully
User user1 added to Group Group2 successfully
User user2 created successfully
User user2 added to Group Group1 successfully
User user2 added to Group Group3 successfully
```
:::
ユーザが2人作成されていることを確認します。
![](https://storage.googleapis.com/zenn-user-upload/747a39db15a3-20240106.png)

グループに所属していることを確認します。
![](https://storage.googleapis.com/zenn-user-upload/317c8adec86e-20240106.png)
