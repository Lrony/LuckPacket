from wxpy import *
import requests
import json
import sys
import re
import os

# 第一个参数为开启登陆缓存，可短时间内自动登陆
# 第二个参数为设置微信登陆二维码显示在终端，mac系统以外的请将参数设置为True即可
bot = Bot(cache_path = True, console_qr = True)

userInfo = []

############################################

# 检查手机号是否有效
def util_check_mobile(mobile):
	p2 = re.compile('^[1][3,4,5,6,7,8][0-9]{9}$')
	phonematch = p2.match(mobile)
	if phonematch:
		return True
	return False

# 检查是否为美团红包
def util_check_url_meituan(url):
	if 'activity.waimai.meituan.com' in url:
		return True
	return False

# 检查是否为饿了么红包
def util_check_url_eleme(url):
	if 'h5.ele.me/hongbao' in url:
		return True
	return False

# 添加需要领取的用户
def util_user_add(name, url):
	user = {'name': name, 'url': url}
	userInfo.append(user)
	print('user info size: ', len(userInfo))

# 查询URL存在的用户INDEX
def util_user_get_url_index(name):
	i = 0
	for info in userInfo:
		i = i +1
		if info['name'] == name:
			if info['url'] == None or info['url'] == '':
				return -1
			return i - 1
	return -1

# 查询用户URL
def util_user_get_url(index):
	return userInfo[index]['url']

# 删除用户
def util_user_del_user(index):
	userInfo.pop(index)

############################################

# 领取红包 https://github.com/game-helper/hongbao
def _wxpy_send_msg(user, msg):
	user.send(msg)

def _get_red_pack(user, link, mobile):
	try:
		data = {'url': link, 'mobile': mobile}
		geturl = 'https://hongbao.xxooweb.com/hongbao'
		r = requests.post(url=geturl, data=data)
		response = r.text
		if response is not None:
			result = json.loads(response)
			result = '领取结果：\n%s' % result['message']
			_wxpy_send_msg(user, result)
	except Exception as e:
		print(e)
		_wxpy_send_msg(user, '服务器开小差了，请重新发送手机号')

# 处理用户发送的文字类型消息
def _message_text(msg_text):
	user = msg_text.chat
	msgText = msg_text.text
	if user and user.is_friend:
		user.mark_as_read()
		if util_check_mobile(msgText):
			url_index = util_user_get_url_index(user.name)
			if url_index == -1:
				_wxpy_send_msg(user, '你还没转发红包')
			else:
				_wxpy_send_msg(user, '正在为您拼命抢大红包')
				url = util_user_get_url(url_index)
				_get_red_pack(user, url, msgText)
				util_user_del_user(url_index)

# 处理用户发送的分享类型消息
def _message_sharing(msg_sharing):
	user = msg_sharing.chat
	if user and user.is_friend:
		user.mark_as_read()
		uin = user.name
		url = msg_sharing.raw['Url']
		url = str(url).replace('&amp;', '&')
		if util_check_url_meituan(url):
			_wxpy_send_msg(user, '美团红包维护中，饿了么成为最大赢家，请使用饿了么')
			return
		if util_check_url_eleme(url):
			util_user_add(uin, url)
			_wxpy_send_msg(user, '请发送需要领取红包的手机号码')
	
############################################

# 注册消息总类
@bot.register()
def message(msg):
	# print(msg)
	if msg.type == 'Text':
		_message_text(msg)
	elif msg.type == 'Sharing':
		_message_sharing(msg)

# 注册好友请求类消息
@bot.register(msg_types=FRIENDS)
def auto_accept_friends(msg):
	# 接受好友 (msg.card 为该请求的用户对象)
	new_friend = bot.accept_friend(msg.card)
	# 或 new_friend = msg.card.accept()
	new_friend.send('Hi，转发外卖红包到此微信，收到提示后发送手机号')

embed()
