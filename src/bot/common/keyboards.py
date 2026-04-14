from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню клиента"""
    kb = [
        [KeyboardButton(text="📋 Мои записи"), KeyboardButton(text="🚗 Мои автомобили")],
        [KeyboardButton(text="📝 Записаться"), KeyboardButton(text="⭐ Оставить отзыв")],
        [KeyboardButton(text="👤 Мой профиль")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню администратора"""
    kb = [
        [KeyboardButton(text="📅 Расписание на сегодня"), KeyboardButton(text="📅 Расписание на неделю")],
        [KeyboardButton(text="👥 Клиенты"), KeyboardButton(text="🔧 Мастера")],
        [KeyboardButton(text="🏗 Подъемники"), KeyboardButton(text="📊 Аналитика")],
        [KeyboardButton(text="📢 Рассылки"), KeyboardButton(text="⚙ Настройки")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def service_categories_keyboard() -> InlineKeyboardMarkup:
    """Выбор категории услуги"""
    buttons = [
        [InlineKeyboardButton(text="🔧 ТО", callback_data="cat:ТО")],
        [InlineKeyboardButton(text="🔍 Диагностика", callback_data="cat:Диагностика")],
        [InlineKeyboardButton(text="🛞 Шиномонтаж", callback_data="cat:Шиномонтаж")],
        [InlineKeyboardButton(text="🚗 Кузовной ремонт", callback_data="cat:Кузовной ремонт")],
        [InlineKeyboardButton(text="⚡ Электрика", callback_data="cat:Электрика")],
        [InlineKeyboardButton(text="🔩 Слесарка", callback_data="cat:Слесарка")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def services_keyboard(services: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Выбор конкретной услуги"""
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"svc:{sid}")] for name, sid in services]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def time_slots_keyboard(slots: list[dict], date_str: str) -> InlineKeyboardMarkup:
    """Выбор временного слота"""
    buttons = []
    row = []
    for slot in slots:
        if slot["available"]:
            time_str = f"{slot['start_time'].strftime('%H:%M')}-{slot['end_time'].strftime('%H:%M')}"
            row.append(InlineKeyboardButton(text=time_str, callback_data=f"slot:{date_str}:{slot['start_time'].strftime('%H:%M')}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cars_keyboard(cars: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Выбор автомобиля"""
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"car:{cid}")] for name, cid in cars]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def appointment_actions_keyboard(appointment_id: str) -> InlineKeyboardMarkup:
    """Действия с записью"""
    buttons = [
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel:{appointment_id}"),
            InlineKeyboardButton(text="🔄 Перенести", callback_data=f"reschedule:{appointment_id}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rating_keyboard(appointment_id: str) -> InlineKeyboardMarkup:
    """Оценка визита"""
    buttons = [
        [InlineKeyboardButton(text=str(i), callback_data=f"rate:{appointment_id}:{i}") for i in range(1, 6)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard(appointment_id: str) -> InlineKeyboardMarkup:
    """Подтверждение записи"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{appointment_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel:{appointment_id}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back:main")]
    ])


def dates_keyboard(dates: list[str]) -> InlineKeyboardMarkup:
    """Выбор даты записи"""
    buttons = []
    row = []
    for d in dates:
        row.append(InlineKeyboardButton(text=d, callback_data=f"date:{d}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
