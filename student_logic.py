from history_tools import append_event


def make_initial_records():
    """Возвращает стартовый список из 6 лабораторных образцов для инициализации базы."""
    return [
        {'code': 'LAB001', 'department': 'Участок А', 'status': 'registered', 'reject_reason': ''},
        {'code': 'LAB002', 'department': 'Участок А', 'status': 'accepted', 'reject_reason': ''},
        {'code': 'LAB003', 'department': 'Участок Б', 'status': 'processed', 'reject_reason': ''},
        {'code': 'LAB004', 'department': 'Участок Б', 'status': 'released', 'reject_reason': ''},
        {'code': 'LAB005', 'department': 'Участок А', 'status': 'rejected', 'reject_reason': 'Нарушена учебная маркировка'},
        {'code': 'LAB006', 'department': 'Участок Б', 'status': 'registered', 'reject_reason': ''}
    ]


def make_initial_state():
    """Создаёт единый словарь состояния проекта: список записей, пустую историю и справочник участков."""
    return {
        "records": make_initial_records(),
        "history": [],
        "extra": {"departments": ["Участок А", "Участок Б"]}
    }


def find_sample(samples, code):
    """Ищет образец в списке samples по точному совпадению кода. Возвращает словарь или None."""
    for s in samples:
        if s['code'] == code:
            return s
    return None


def register_sample(samples, code, department):
    """Регистрирует новый образец после очистки кода, проверки формата LABxxx, уникальности и участка."""
    # Убираем лишние пробелы по краям и переводим буквы в верхний регистр
    c = str(code).strip().upper()

    # Проверяем длину (6 символов), префикс LAB и наличие 3 цифр в конце
    if not (c.startswith("LAB") and len(c) == 6 and c[3:].isdigit()):
        return {'ok': False, 'message': 'Неверный формат кода образца. Ожидается LABxxx', 'record_id': None}

    # Проверяем, нет ли уже такого кода в реестре
    if find_sample(samples, c) is not None:
        return {'ok': False, 'message': 'Образец с таким кодом уже зарегистрирован', 'record_id': None}

    # Проверяем корректность выбранного производственного участка
    if department not in ['Участок А', 'Участок Б']:
        return {'ok': False, 'message': 'Неверно указан производственный участок', 'record_id': None}

    # Добавляем новую запись со стартовым статусом registered
    samples.append({'code': c, 'department': department, 'status': 'registered', 'reject_reason': ''})
    return {'ok': True, 'message': 'Образец успешно внесен в базу данных', 'record_id': c}


def reject_sample(samples, code, reason):
    """Переводит образец в статус брака ('rejected') на начальных этапах с обязательной причиной."""
    c = str(code).strip().upper()
    s = find_sample(samples, c)
    if not s:
        return {'ok': False, 'message': 'Образец с указанным кодом не обнаружен', 'record_id': None}

    # Браковать можно только до начала основной обработки
    if s['status'] not in ['registered', 'accepted']:
        return {'ok': False, 'message': 'Невозможно отбраковать образец на данном этапе обработки', 'record_id': None}

    # Очищаем причину от пробелов и проверяем, что она не пустая
    r = str(reason).strip()
    if not r:
        return {'ok': False, 'message': 'Причина отбраковки обязательна для заполнения', 'record_id': None}

    s['status'] = 'rejected'
    s['reject_reason'] = r
    return {'ok': True, 'message': 'Образец успешно переведен в категорию брака', 'record_id': c}


def select_samples(samples, department=None, status=None, fragment=None):
    """Возвращает новый отфильтрованный список образцов по заданным непустым критериям."""
    res = []
    for s in samples:
        # Пропускаем записи, которые не подходят под активные фильтры
        if department and s['department'] != department:
            continue
        if status and s['status'] != status:
            continue
        if fragment and fragment.upper() not in s['code'].upper():
            continue
        res.append(s)
    return res


def available_actions(samples, code):
    """Возвращает подсказку и список доступных действий для одного образца без изменения данных."""
    c = str(code).strip().upper()
    s = find_sample(samples, c)
    if s is None:
        return {'ok': False, 'message': 'код не найден', 'actions': []}

    st = s.get('status')
    if st == 'registered':
        return {'ok': True, 'message': 'образец зарегистрирован', 'actions': ['Принять', 'Отклонить']}
    if st == 'accepted':
        return {'ok': True, 'message': 'образец принят', 'actions': ['Обработать', 'Отклонить']}
    if st == 'processed':
        return {'ok': True, 'message': 'образец обработан', 'actions': ['Выдать']}
    if st in ['released', 'rejected']:
        return {'ok': True, 'message': 'образец завершён', 'actions': []}
    return {'ok': True, 'message': 'неизвестный статус', 'actions': []}
def parse_sample_codes(raw_text):
    """Разбирает многострочный ввод по запятым, точкам с запятой и пробелам, убирая дубликаты."""
    # Заменяем запятые и точки с запятой на пробелы, затем разбиваем строку на части
    parts = str(raw_text).replace(",", " ").replace(";", " ").split()
    out, seen = [], set()

    for p in parts:
        c = p.strip().upper()
        # Добавляем код только при первом появлении, сохраняя порядок ввода
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def check_stage(sample, target_status):
    """Проверяет допустимость перехода на целевой этап без изменения базы. Возвращает (bool, str)."""
    if sample is None:
        return False, "Образец не найден"

    cur = sample.get("status")
    if cur == "rejected":
        return False, "Отклонённый образец нельзя вернуть в работу"
    if cur == target_status:
        return False, f"Образец уже находится в статусе {target_status}"

    # Словарь строго последовательных переходов жизненного цикла
    allowed = {"registered": "accepted", "accepted": "processed", "processed": "released"}
    if cur not in allowed or allowed[cur] != target_status:
        return False, f"Недопустимый переход из {cur} в {target_status}"

    return True, f"Переход в {target_status} разрешён"


def change_stage(samples, code, target_status):
    """Переводит один образец на следующий этап после предварительной проверки check_stage."""
    c = str(code).strip().upper()
    s = find_sample(samples, c)
    ok, msg = check_stage(s, target_status)
    if not ok:
        return {'ok': False, 'message': msg, 'record_id': None}

    s['status'] = target_status
    return {'ok': True, 'message': f'Статус успешно изменен на {target_status}', 'record_id': c}


def prepare_stage_results(samples, raw_text, target_status):
    """Формирует предварительный протокол для списка кодов без изменения данных (режим предпросмотра)."""
    res = []
    for c in parse_sample_codes(raw_text):
        ok, msg = check_stage(find_sample(samples, c), target_status)
        res.append({'ok': ok, 'message': msg, 'record_id': c})
    return res


def change_stage_batch(samples, raw_text, target_status):
    """Выполняет пакетный переход для допустимых кодов из списка без записи в историю."""
    res = []
    for c in parse_sample_codes(raw_text):
        r = change_stage(samples, c, target_status)
        res.append({'ok': r['ok'], 'message': r['message'], 'record_id': c})
    return res


def change_stage_logged(state, code, target_status):
    """Переводит этап одного образца и записывает событие stage_change в историю только при успехе."""
    samples = state["records"]
    c = str(code).strip().upper()
    s = find_sample(samples, c)
    old_st = s["status"] if s else None  # Запоминаем старый статус до изменения

    r = change_stage(samples, c, target_status)
    if r["ok"]:
        append_event(state, action="stage_change", record_id=c, field="status", before=old_st, after=target_status, related_ids=[c], details=r["message"])
    return r


def change_stage_batch_logged(state, raw_text, target_status):
    """Выполняет групповой переход и фиксирует в журнале истории только успешные изменения."""
    res = []
    for c in parse_sample_codes(raw_text):
        r = change_stage_logged(state, c, target_status)
        res.append({'ok': r['ok'], 'message': r['message'], 'record_id': c})
    return res


def reject_sample_logged(state, code, reason):
    """Отклоняет образец и записывает прежние и новые статус и причину в историю."""
    samples = state["records"]
    c = str(code).strip().upper()
    s = find_sample(samples, c)
    old_d = {"status": s["status"], "reject_reason": s["reject_reason"]} if s else None

    r = reject_sample(samples, c, reason)
    if r["ok"]:
        new_d = {"status": s["status"], "reject_reason": s["reject_reason"]}
        append_event(state, action="reject", record_id=c, field="status_and_reason", before=old_d, after=new_d, related_ids=[c], details=f"Причина: {s['reject_reason']}")
    return r


def correct_department(state, code, department):
    """Исправляет производственный участок только до приёмки (в статусе registered) с записью в историю."""
    samples = state["records"]
    c = str(code).strip().upper()
    s = find_sample(samples, c)

    if s is None:
        return {'ok': False, 'message': 'Образец не найден', 'record_id': None}
    if s["status"] != "registered":
        return {'ok': False, 'message': 'Исправить участок можно только до приёмки (registered)', 'record_id': None}

    depts = state.get("extra", {}).get("departments", ["Участок А", "Участок Б"])
    if department not in depts:
        return {'ok': False, 'message': 'Неизвестный участок', 'record_id': None}

    old_d = s["department"]
    if old_d == department:
        return {'ok': False, 'message': f'Образец уже на участке {department}', 'record_id': None}

    s["department"] = department
    append_event(state, action="department_edit", record_id=c, field="department", before=old_d, after=department, related_ids=[c], details=f"{old_d} -> {department}")
    return {'ok': True, 'message': f'Участок {c} изменён на {department}', 'record_id': c}


def validate_project_state(candidate):
    """Проверяет структуру и предметные правила загруженного снимка state перед заменой рабочих данных."""
    errors = []
    if not isinstance(candidate, dict):
        return ["Данные не являются словарём."]

    recs, hist, extra = candidate.get("records"), candidate.get("history"), candidate.get("extra")
    if not isinstance(recs, list):
        return ["Поле records должно быть списком."]
    if not isinstance(hist, list):
        errors.append("Поле history должно быть списком.")
    if not isinstance(extra, dict):
        errors.append("Поле extra должно быть словарём.")

    depts = extra.get("departments", ["Участок А", "Участок Б"]) if isinstance(extra, dict) else ["Участок А", "Участок Б"]
    statuses = {"registered", "accepted", "processed", "released", "rejected"}
    seen = set()

    # Проверяем каждую запись реестра по предметным правилам
    for i, item in enumerate(recs, 1):
        if not isinstance(item, dict):
            errors.append(f"Запись {i} не словарь.")
            continue
        c, d, st, rsn = str(item.get("code", "")).strip(), item.get("department"), item.get("status"), str(item.get("reject_reason", "")).strip()

        if not c:
            errors.append(f"Запись {i}: пустой код.")
        elif c in seen:
            errors.append(f"Дубликат кода: {c}.")
        else:
            seen.add(c)

        if d not in depts:
            errors.append(f"{c}: неизвестный участок '{d}'.")
        if st not in statuses:
            errors.append(f"{c}: неизвестный статус '{st}'.")
        if st == "rejected" and not rsn:
            errors.append(f"{c}: для rejected нужна причина.")
        if st != "rejected" and rsn:
            errors.append(f"{c}: причина должна быть пустой для '{st}'.")

    return errors
