"""Р“РѕС‚РѕРІС‹Р№ С„Р°Р№Р»РѕРІС‹Р№ Р°РґР°РїС‚РµСЂ РґРЅСЏ 3. РџСЂРµРґРјРµС‚РЅС‹Рµ РїСЂР°РІРёР»Р° Р·РґРµСЃСЊ РЅРµ Р·Р°РґР°СЋС‚СЃСЏ."""
import json
from pathlib import Path

FORMAT_VERSION = 1


def _answer(ok, message, state):
    return {"ok": ok, "message": message, "state": state}


def validate_container(state):
    """РџСЂРѕРІРµСЂРёС‚СЊ С‚РѕР»СЊРєРѕ РѕР±С‰СѓСЋ РѕР±РѕР»РѕС‡РєСѓ, РЅРµ РїРѕР»СЏ С‚Р°Р»РѕРЅРѕРІ РёР»Рё Р°РЅРєРµС‚."""
    if not isinstance(state, dict):
        return "РЎРѕСЃС‚РѕСЏРЅРёРµ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ СЃР»РѕРІР°СЂС‘Рј."
    if not isinstance(state.get("records"), list):
        return "Р’ СЃРѕСЃС‚РѕСЏРЅРёРё РЅСѓР¶РµРЅ СЃРїРёСЃРѕРє records."
    if not isinstance(state.get("history"), list):
        return "Р’ СЃРѕСЃС‚РѕСЏРЅРёРё РЅСѓР¶РµРЅ СЃРїРёСЃРѕРє history."
    if not isinstance(state.get("extra"), dict):
        return "Р’ СЃРѕСЃС‚РѕСЏРЅРёРё РЅСѓР¶РµРЅ СЃР»РѕРІР°СЂСЊ extra."
    return ""


def save_state(path, project, state):
    """Р’РµСЂРЅСѓС‚СЊ ok/message/state. Р§РёСЃР»Р° Рё bool СЃРѕС…СЂР°РЅСЏСЋС‚ СЃРІРѕР№ С‚РёРї."""
    error = validate_container(state)
    if error:
        return _answer(False, error, None)
    payload = {"format_version": FORMAT_VERSION,
               "project": project, "state": state}
    try:
        text = json.dumps(payload, ensure_ascii=False, indent=2,
                          allow_nan=False)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(target)
    except (OSError, TypeError, ValueError) as error:
        return _answer(False, "РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕС…СЂР°РЅРёС‚СЊ: " + str(error), None)
    return _answer(True, "РЎРѕСЃС‚РѕСЏРЅРёРµ СЃРѕС…СЂР°РЅРµРЅРѕ.", None)


def load_state(path, expected_project):
    """Р—Р°РіСЂСѓР·РёС‚СЊ РѕС‚РґРµР»СЊРЅРѕ. РўРµРєСѓС‰СѓСЋ РїСЂРѕРіСЂР°РјРјСѓ СЌС‚Р° С„СѓРЅРєС†РёСЏ РЅРµ РјРµРЅСЏРµС‚."""
    try:
        text = Path(path).read_text(encoding="utf-8")
        payload = json.loads(text)
    except (OSError, UnicodeError, ValueError) as error:
        return _answer(False, "РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕС‡РёС‚Р°С‚СЊ: " + str(error), None)
    if not isinstance(payload, dict):
        return _answer(False, "Р¤Р°Р№Р» РЅРµ СЃРѕРґРµСЂР¶РёС‚ СЃР»РѕРІР°СЂСЊ СЃРѕСЃС‚РѕСЏРЅРёСЏ.", None)
    if payload.get("format_version") != FORMAT_VERSION:
        return _answer(False, "РќРµРёР·РІРµСЃС‚РЅР°СЏ РІРµСЂСЃРёСЏ С„Р°Р№Р»Р°.", None)
    if payload.get("project") != expected_project:
        return _answer(False, "Р­С‚РѕС‚ С„Р°Р№Р» РѕС‚РЅРѕСЃРёС‚СЃСЏ Рє РґСЂСѓРіРѕРјСѓ РїСЂРѕРµРєС‚Сѓ.", None)
    state = payload.get("state")
    error = validate_container(state)
    if error:
        return _answer(False, error, None)
    return _answer(True, "Р¤Р°Р№Р» РїСЂРѕС‡РёС‚Р°РЅ. РџСЂРѕРІРµСЂСЊС‚Рµ РїСЂРµРґРјРµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ.", state)


def export_document(path, text):
    """РЎРѕС…СЂР°РЅРёС‚СЊ РіРѕС‚РѕРІС‹Р№ СЂР°Р±РѕС‡РёР№ С‚РµРєСЃС‚; СЃРѕРґРµСЂР¶Р°РЅРёРµ С„РѕСЂРјРёСЂСѓРµС‚ РєРѕРјР°РЅРґР°."""
    if not isinstance(text, str):
        return _answer(False, "Р”Р»СЏ РґРѕРєСѓРјРµРЅС‚Р° РЅСѓР¶РµРЅ С‚РµРєСЃС‚.", None)
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    except OSError as error:
        return _answer(False, "РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РіСЂСѓР·РёС‚СЊ: " + str(error), None)
    return _answer(True, "Р Р°Р±РѕС‡РёР№ РґРѕРєСѓРјРµРЅС‚ РІС‹РіСЂСѓР¶РµРЅ.", None)