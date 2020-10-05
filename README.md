# dislinbot
DiscordのテキストチャンネルとLineのグループの間のメッセージ転送ボット。(Heroku用)


## 使い方

Herokuの登録の方法や、LINEとDiscordでボット作成に必要なシークレット、トークンの取得方法については割愛。

### ボット用のトークンを設定(必須)
[LINE Developers](https://developers.line.biz/ja/)でボット(公式チャンネル)用のチャンネルシークレットとチャンネルアクセストークン(長期)を取得。  
[Discord Developer Portal](https://discord.com/developers/applications)でボット用のトークンを取得。  
  
heroku config:setで以下の環境変数を設定。

<pre>
LINE_CHANNEL_SECRET = LINEのチャンネルシークレット
LINE_CHANNEL_ACCESS_TOKEN = LINEのチャンネルアクセストークン(長期)
DISCORD_BOT_TOKEN = DiscordのBotのトークン
</pre>

### メッセージを転送するDiscordチャンネルとLINEグループのIDを調べて設定

herokuにdeployして動作していることを確認する。  
LINEのグループIDボットをLINEのグループに追加して"/show-group-id"とメッセージを送る。  
するとLINEのグループIDを返してくれるのでそれをメモ。  
今度はDiscordでLINEグループのメッセージの転送先のテキストチャンネルで"/show-channel-id"とメッセージを送る。  
するとそのチャンネルのIDを返してくれるのでそれもメモ。  
  
メモしたそれぞれのIDをheroku config:setで環境変数として追加で設定する。  

<pre>
LINE_GROUP_ID = LINEグループID
DISCORD_CHANNEL_ID = DiscordチャンネルID
</pre>

以上でDiscordのテキストチャンネルとLINEのグループ同士でメッセージを転送し合うようになってくれるはず。

