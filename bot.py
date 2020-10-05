import os
import asyncio
from aiohttp import web

import discord

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, StickerMessage, TextSendMessage


class BotVars:
	"""bot variables"""
	def __init__(self, var_names):
		for var_info in var_names:
			value = os.environ.get(var_info.name)
			if value is None:
				print("Specify {0} as environment variable.".format(var_info.name))
				if var_info.required:
					exit(1)
			setattr(self, var_info.name, value)

	@staticmethod
	def load():
		class VarInfo:
			def __init__(self, name: str, required: bool):
				self.name = name
				self.required = required

		_var_names = [
			VarInfo('LINE_CHANNEL_SECRET', True),
			VarInfo('LINE_CHANNEL_ACCESS_TOKEN', True),
			VarInfo('DISCORD_BOT_TOKEN', True),
			VarInfo('LINE_GROUP_ID', False),
			VarInfo('DISCORD_CHANNEL_ID', False)]
		return BotVars(_var_names)


bot_vars = BotVars.load()

client = discord.Client()
line_bot_api = LineBotApi(bot_vars.LINE_CHANNEL_ACCESS_TOKEN)
line_parser = WebhookParser(bot_vars.LINE_CHANNEL_SECRET)

app = web.Application()
routes = web.RouteTableDef()


@client.event
async def on_ready():
	print("logged in as {0.user}".format(client))
	runner = web.AppRunner(app)
	await runner.setup()
	port = os.environ.get('PORT')
	site = web.TCPSite(runner, host='0.0.0.0', port=port)
	print("web.TCPSite = {0}:{1}".format(site._host, site._port))
	await site.start()


@client.event
async def on_message(message):
	# ignore own message
	if message.author == client.user:
		return
	# ignore bot message
	if message.author.bot:
		return

	# EXTRA COMMANDS
	if message.content == '/show-channel-id':
		await message.channel.send(message.channel.id)
		return  # exit if proceed any command.

	# check channel id
	channel_id = bot_vars.DISCORD_CHANNEL_ID
	if channel_id is None:
		return

	# ignore if channel id is not matched.
	if message.channel.id != int(channel_id):
		return

	user_name = message.author.nick or message.author.name
	content = '{0}: {1}'.format(user_name, message.content)

	# send to LINE
	group_id = bot_vars.LINE_GROUP_ID
	if group_id is None:
		return
	line_bot_api.push_message(group_id, TextSendMessage(text=content))


async def _line_extra_command(event):
	if event.message.text == '/show-group-id':
		if event.source.type == 'group':
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(text=event.source.group_id))
		else:
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(text="ERROR: not from group"))
		return True
	return False


def _line_user_display_name_from_event(event):
	profile = None
	if event.source.type == 'group':
		profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
	else:
		profile = line_bot_api.get_profile(event.source.user_id)
	if profile:
		return profile.display_name
	return "unknown"


async def _line_to_discord(event):
	# ignore not MessageEvent
	if not isinstance(event, MessageEvent):
		return

	# EXTRA COMMANDS
	if isinstance(event.message, TextMessage):
		if await _line_extra_command(event):
			return  # exit if proceed any command.

	# get line user name
	display_name = _line_user_display_name_from_event(event)
	content = None

	# message handlers
	if isinstance(event.message, TextMessage):
		# TextMessage
		content = '{0}: {1}'.format(display_name, event.message.text)
	elif isinstance(event.message, StickerMessage):
		# StickerMessage
		content = '{0}がスタンプを送信しました'.format(display_name)
	else:
		# other
		content = '{0}がLINEで何かしました'.format(display_name)

	# add group name if send from group
	if event.source.type == 'group':
		group_summary = line_bot_api.get_group_summary(event.source.group_id)
		content += '@{0}'.format(group_summary.group_name)

	# send to Discord
	channel_id = bot_vars.DISCORD_CHANNEL_ID
	if channel_id is None:
		return
	channel = client.get_channel(int(channel_id))
	if channel is not None:
		await channel.send(content)


@routes.post("/callback")
async def callback(request):
	"""LINE Message API endpoint"""
	signature = request.headers['X-Line-Signature']
	body = await request.text()
	try:
		events = line_parser.parse(body, signature)
		for event in events:
			await _line_to_discord(event)
	except LineBotApiError as e:
		print("got exception from LINE Message API: {0}".format(e.message))
		for m in e.error.details:
			print("  {0} : {1}".format(m.property, m.message))
		return web.Response(status=200)
	except InvalidSignatureError:
		return web.Response(status=400)

	return web.Response()


app.add_routes(routes)


client.run(bot_vars.DISCORD_BOT_TOKEN)
