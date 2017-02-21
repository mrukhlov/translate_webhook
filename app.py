import os
import requests
from requests import ConnectionError
import random

from language_list import _LANGUAGE_LIST as language_dict
from language_list import _LANGUAGE_CODE_LIST as language_code_dict

from translate_response import(
_TRANSLATE_W,
_TRANSLATE_W_FROM,
_TRANSLATE_W_TO,
_TRANSLATE_W_FROM_TO,
_TRANSLATE_INTO_W,
_TRANSLATE_RESULT,
_TRANSLATE_UNKOWN_LANGUAGE,
_TRANSLATE_ERROR,
_TRANSLATE_NETWORK_ERROR
)

_GOOGLE_API_KEY = ''
_LANGUAGE_DETECTION_SERVICE_URL = 'https://translation.googleapis.com/language/translate/v2/detect'
_TRANSLATION_SERVICE_URL = 'https://translation.googleapis.com/language/translate/v2'

from flask import (
	Flask,
	request,
	make_response,
	jsonify
)

app = Flask(__name__)
log = app.logger

@app.route('/webhook', methods=['POST'])
def webhook():
	req = request.get_json(silent=True, force=True)
	action = req.get("result").get('action')

	if action == 'translate.text':
		res = translate(req)
	else:
		log.error("Unexpeted action.")
		res = {"speech": 'error', "displayText": 'error'}

	return make_response(jsonify(res))

def translate(req):

	parameters = req['result']['parameters']
	context = req['result']['contexts']

	text = parameters.get('text')
	lang_from = parameters.get('lang-from')
	lang_to = parameters.get('lang-to')

	if not text:
		if not lang_from and not lang_to:
			res = random.choice(_TRANSLATE_W)
		elif lang_from and lang_to:
			res = random.choice(_TRANSLATE_W_FROM_TO).format(lang_from=lang_from, lang_to=lang_to)
		elif lang_from:
			res = random.choice(_TRANSLATE_W_FROM).format(lang=lang_from)
		elif lang_to:
			res = random.choice(_TRANSLATE_W_TO).format(lang=lang_to)
		return {"speech": res, "displayText": res, 'contextOut': context}

	if not lang_from:

		params = {
			'q': text,
			'key': _GOOGLE_API_KEY
		}

		try:
			r = requests.get(_LANGUAGE_DETECTION_SERVICE_URL, params=params)
		except ConnectionError:
			res = random.choice(_TRANSLATE_NETWORK_ERROR)
			return {"speech": res, "displayText": res, 'contextOut': context}

		try:
			lang_from = r.json()['data']['detections'][0][0]['language']
		except KeyError:
			res = random.choice(_TRANSLATE_ERROR)
			return {"speech": res, "displayText": res, 'contextOut': context}

	if not lang_to:
		if lang_from != 'English' and lang_from != 'en':
			lang_to = 'English'
		else:
			res = random.choice(_TRANSLATE_INTO_W)
			return {"speech": res, "displayText": res, 'contextOut': context}

	if lang_from in language_dict.keys():
		lang_from_code = language_dict[lang_from]
	elif lang_from in language_dict.values():
		lang_from_code = lang_from
	else:
		res = random.choice(_TRANSLATE_UNKOWN_LANGUAGE)
		return {"speech": res, "displayText": res}

	if lang_to in language_dict.keys():
		lang_to_code = language_dict[lang_to]
	elif lang_to in language_dict.values():
		lang_to_code = lang_to
	else:
		res = random.choice(_TRANSLATE_UNKOWN_LANGUAGE)
		return {"speech": res, "displayText": res}

	params = {
		'q': text,
		'source': lang_from_code,
		'target': lang_to_code,
		'format': 'text',
		'key': _GOOGLE_API_KEY
	}

	try:
		r = requests.get(_TRANSLATION_SERVICE_URL, params=params)
	except ConnectionError:
		res = random.choice(_TRANSLATE_NETWORK_ERROR)
		return {"speech": res, "displayText": res, 'contextOut': context}
	try:
		text = r.json().get('data').get('translations')[0].get('translatedText')
		if lang_from in language_dict.values():
			lang_from = language_code_dict[lang_from]

		try:
			res = random.choice(_TRANSLATE_RESULT).format(fromLang=lang_from, toLang=lang_to, text=text.capitalize())
		except UnicodeEncodeError:
			res = random.choice(_TRANSLATE_RESULT).format(fromLang=lang_from, toLang=lang_to, text=text.encode('utf8').capitalize())
	except KeyError:
		res = random.choice(_TRANSLATE_ERROR)

	return {"speech": res, "displayText": res, 'contextOut':context}


if __name__ == '__main__':
	port = int(os.getenv('PORT', 5001))

	app.run(
		debug=True,
		port=port,
		host='0.0.0.0'
	)