"""
Модуль локализации — переводы интерфейса бота.
Поддерживаемые языки: русский, английский, таджикский.
"""

TEXTS = {
    "ru": {
        "welcome": (
            "🎵 <b>Добро пожаловать в {app_name}!</b>\n\n"
            "Привет, {name}! 👋\n\n"
            "Я помогу тебе найти и скачать музыку.\n\n"
            "🔍 Нажми <b>Поиск</b> или отправь название трека!"
        ),
        "btn_search": "🔍 Поиск",
        "btn_popular": "🔥 Популярное",
        "btn_help": "📞 Помощь",
        "btn_operator": "👤 Оператор",
        "btn_operator_1": "👤 Оператор 1",
        "btn_operator_2": "👤 Оператор 2",
        "btn_language": "🌍 Язык",        "btn_currency": "💱 Курс валют",
        "currency_loading": "💱 <b>Загружаю курсы валют...</b>",
        "currency_error": "❌ Не удалось получить курсы валют",        "search_prompt": "🔍 <b>Поиск музыки</b>\n\nВведи название трека или исполнителя:",
        "searching": "🔍 <b>Ищу:</b> {query}...",
        "not_found": "❌ Ничего не найдено. Попробуй другой запрос.",
        "loading_popular": "🔥 <b>Загружаю популярные треки...</b>",
        "popular_title": "🔥 <b>Популярная музыка</b>\n\nНажми на трек чтобы послушать 🎧",
        "popular_error": "❌ Не удалось загрузить популярные треки",
        "btn_refresh": "🔄 Обновить",
        "downloading": "🎧 <b>Скачиваю трек...</b>",
        "sending": "📤 <b>Отправляю...</b>",
        "download_fail": "❌ Не удалось скачать трек. Попробуй другой.",
        "file_too_big": "❌ Файл слишком большой (>50 МБ)",
        "quality_selection_hint": "⚙️ Выбор качества пока не используется автоматически. Нажми кнопку MP3 или MP4 ещё раз, если она доступна в сообщении.",
        "invalid_callback_data": "❌ Некорректные данные для операции.",
        "voice_chat_unavailable": "🎙 Голосовые чаты пока не настроены. Нужна интеграция с pytgcalls и управление групповым звонком.",
        "voice_play_unavailable": "🎵 Воспроизведение в голосовом чате пока отключено. Обычное скачивание и отправка треков уже работает.",
        "voice_pause_unavailable": "⏸ Голосовой плеер ещё не реализован.",
        "voice_resume_unavailable": "▶️ Голосовой плеер ещё не реализован.",
        "voice_leave_unavailable": "🚪 Бот сейчас не подключается к голосовым чатам.",
        "voice_now_playing_unavailable": "ℹ️ Сейчас голосовое воспроизведение не активно.",
        "help_text": (
            "<b>📋 Команды:</b>\n\n"
            "/search &lt;запрос&gt; — Поиск музыки\n"
            "/popular — Популярная музыка\n"
            "/help — Справка\n\n"
            "<b>👤 Связь с оператором:</b> кнопки ниже\n\n"
            "<b>💡 Совет:</b> Просто отправь название песни в чат!"
        ),
        "choose_language": "🌍 <b>Выбери язык / Choose language:</b>",
        "language_set": "✅ Язык установлен: <b>Русский</b> 🇷🇺",
        "default_reply": "🎵 Отправь название трека для поиска\nили нажми /start для меню",
        "url_detected": "🔗 Обнаружена ссылка!\n\nВыбери действие:",
        "url_invalid": "❌ Ссылка устарела или недоступна. Отправь её снова.",
        "url_added_to_queue": "➕ Ссылка добавлена в очередь.",
        "settings_title": "⚙️ <b>Настройки</b>\n\nВыбери, что хочешь изменить:",
        "settings_audio": "🎵 Качество аудио",
        "settings_video": "📹 Качество видео",
        "settings_language": "🌍 Язык",
        "settings_audio_choose": "🎵 <b>Выбери качество аудио:</b>",
        "settings_video_choose": "📹 <b>Выбери качество видео:</b>",
        "settings_audio_saved": "✅ Качество аудио сохранено: <b>{value} kbps</b>",
        "settings_video_saved": "✅ Качество видео сохранено: <b>{value}p</b>",
        "btn_referral": "👥 Рефералы",
        "btn_recognize": "🎤 Распознать",
        "recognize_prompt": "🎤 <b>Распознавание музыки</b>\n\nОтправь голосовое сообщение или аудиофайл, и я определю песню!",
        "recognizing": "🎤 <b>Распознаю музыку...</b> Подожди несколько секунд.",
        "recognize_result": (
            "🎵 <b>Песня найдена!</b>\n\n"
            "🎤 <b>{artist}</b>\n"
            "📀 <b>{title}</b>\n"
            "{extra}"
        ),
        "recognize_fail": "😔 Не удалось распознать музыку. Попробуй другой фрагмент.",
        "referral_stats": (
            "👥 <b>Реферальная программа</b>\n\n"
            "Приглашай друзей и получай бонусы!\n\n"
            "📊 <b>Твоя статистика:</b>\n"
            "  • Приглашено друзей: <b>{count}</b>\n\n"
            "🔗 <b>Твоя ссылка:</b>\n"
            "<code>{link}</code>\n\n"
            "Отправь эту ссылку друзьям!"
        ),
        "referral_welcome": "🎉 Тебя пригласил друг! Добро пожаловать!",
        "referral_new": "🎉 По твоей ссылке присоединился новый пользователь! Всего: {count}",
        "subscription_join_button": "📢 Подписаться на канал",
        "subscription_check_button": "✅ Проверить подписку",
        "subscription_required": (
            "📢 <b>Подпишись на наш канал {channel}</b>\n\n"
            "После подписки бот будет работать без ограничений.\n"
            "Без подписки доступно только <b>{limit}</b> бесплатных музыкальных действий.\n"
            "Осталось: <b>{remaining}</b>."
        ),
        "subscription_check_failed": (
            "⚠️ Не удалось проверить подписку на канал {channel}.\n\n"
            "Подпишись и нажми кнопку проверки снова.\n"
            "Без подписки доступно только <b>{limit}</b> бесплатных музыкальных действий.\n"
            "Осталось: <b>{remaining}</b>."
        ),
        "subscription_verified": "✅ Подписка подтверждена. Ограничения сняты.",
        "subscription_not_verified": "❌ Подписка не найдена. Подпишись на канал и нажми проверку снова.",
        "rate_limit": "⏳ Слишком много запросов. Попробуй позже.",
        "error": "❌ Ошибка: {error}",
    },
    "en": {
        "welcome": (
            "🎵 <b>Welcome to {app_name}!</b>\n\n"
            "Hi, {name}! 👋\n\n"
            "I'll help you find and download music.\n\n"
            "🔍 Press <b>Search</b> or send a song name!"
        ),
        "btn_search": "🔍 Search",
        "btn_popular": "🔥 Popular",
        "btn_help": "📞 Help",
        "btn_operator": "👤 Operator",
        "btn_operator_1": "👤 Operator 1",
        "btn_operator_2": "👤 Operator 2",
        "btn_language": "🌍 Language",        "btn_currency": "💱 Exchange rates",
        "currency_loading": "💱 <b>Loading exchange rates...</b>",
        "currency_error": "❌ Failed to load exchange rates",        "search_prompt": "🔍 <b>Search music</b>\n\nEnter track name or artist:",
        "searching": "🔍 <b>Searching:</b> {query}...",
        "not_found": "❌ Nothing found. Try another query.",
        "loading_popular": "🔥 <b>Loading popular tracks...</b>",
        "popular_title": "🔥 <b>Popular music</b>\n\nTap a track to listen 🎧",
        "popular_error": "❌ Failed to load popular tracks",
        "btn_refresh": "🔄 Refresh",
        "downloading": "🎧 <b>Downloading track...</b>",
        "sending": "📤 <b>Sending...</b>",
        "download_fail": "❌ Failed to download. Try another track.",
        "file_too_big": "❌ File is too large (>50 MB)",
        "quality_selection_hint": "⚙️ Quality selection is not used automatically yet. Press the MP3 or MP4 button again if it is available in the message.",
        "invalid_callback_data": "❌ Invalid operation data.",
        "voice_chat_unavailable": "🎙 Voice chats are not configured yet. pytgcalls integration and group call control are still needed.",
        "voice_play_unavailable": "🎵 Voice chat playback is currently disabled. Regular download and track sending already works.",
        "voice_pause_unavailable": "⏸ Voice playback is not implemented yet.",
        "voice_resume_unavailable": "▶️ Voice playback is not implemented yet.",
        "voice_leave_unavailable": "🚪 The bot is not connected to voice chats right now.",
        "voice_now_playing_unavailable": "ℹ️ Voice playback is currently inactive.",
        "help_text": (
            "<b>📋 Commands:</b>\n\n"
            "/search &lt;query&gt; — Search music\n"
            "/popular — Popular music\n"
            "/help — Help\n\n"
            "<b>👤 Contact operators:</b> buttons below\n\n"
            "<b>💡 Tip:</b> Just send a song name in the chat!"
        ),
        "choose_language": "🌍 <b>Выбери язык / Choose language:</b>",
        "language_set": "✅ Language set: <b>English</b> 🇬🇧",
        "default_reply": "🎵 Send a song name to search\nor press /start for menu",
        "url_detected": "🔗 Link detected!\n\nChoose an action:",
        "url_invalid": "❌ The link has expired or is unavailable. Send it again.",
        "url_added_to_queue": "➕ Link added to queue.",
        "settings_title": "⚙️ <b>Settings</b>\n\nChoose what you want to change:",
        "settings_audio": "🎵 Audio quality",
        "settings_video": "📹 Video quality",
        "settings_language": "🌍 Language",
        "settings_audio_choose": "🎵 <b>Choose audio quality:</b>",
        "settings_video_choose": "📹 <b>Choose video quality:</b>",
        "settings_audio_saved": "✅ Audio quality saved: <b>{value} kbps</b>",
        "settings_video_saved": "✅ Video quality saved: <b>{value}p</b>",
        "btn_referral": "👥 Referrals",
        "btn_recognize": "🎤 Recognize",
        "recognize_prompt": "🎤 <b>Music Recognition</b>\n\nSend a voice message or audio file, and I'll identify the song!",
        "recognizing": "🎤 <b>Recognizing music...</b> Please wait a few seconds.",
        "recognize_result": (
            "🎵 <b>Song found!</b>\n\n"
            "🎤 <b>{artist}</b>\n"
            "📀 <b>{title}</b>\n"
            "{extra}"
        ),
        "recognize_fail": "😔 Could not recognize the music. Try another clip.",
        "referral_stats": (
            "👥 <b>Referral Program</b>\n\n"
            "Invite friends and earn bonuses!\n\n"
            "📊 <b>Your stats:</b>\n"
            "  • Friends invited: <b>{count}</b>\n\n"
            "🔗 <b>Your link:</b>\n"
            "<code>{link}</code>\n\n"
            "Share this link with your friends!"
        ),
        "referral_welcome": "🎉 You were invited by a friend! Welcome!",
        "referral_new": "🎉 A new user joined via your link! Total: {count}",
        "subscription_join_button": "📢 Join channel",
        "subscription_check_button": "✅ Check subscription",
        "subscription_required": (
            "📢 <b>Subscribe to our channel {channel}</b>\n\n"
            "After subscribing, the bot will work without limits.\n"
            "Without a subscription only <b>{limit}</b> free music actions are available.\n"
            "Remaining: <b>{remaining}</b>."
        ),
        "subscription_check_failed": (
            "⚠️ Could not verify your subscription to {channel}.\n\n"
            "Subscribe and press the check button again.\n"
            "Without a subscription only <b>{limit}</b> free music actions are available.\n"
            "Remaining: <b>{remaining}</b>."
        ),
        "subscription_verified": "✅ Subscription confirmed. Limits removed.",
        "subscription_not_verified": "❌ Subscription not found. Join the channel and check again.",
        "rate_limit": "⏳ Too many requests. Try again later.",
        "error": "❌ Error: {error}",
    },
    "tg": {
        "welcome": (
            "🎵 <b>Хуш омадед ба {app_name}!</b>\n\n"
            "Салом, {name}! 👋\n\n"
            "Ман ба ту дар ёфтан ва боргирии мусиқӣ кӯмак мекунам.\n\n"
            "🔍 <b>Ҷустуҷӯ</b>-ро пахш кун ё номи суруд бинавис!"
        ),
        "btn_search": "🔍 Ҷустуҷӯ",
        "btn_popular": "🔥 Маъмул",
        "btn_help": "📞 Кӯмак",
        "btn_operator": "👤 Оператор",
        "btn_operator_1": "👤 Оператор 1",
        "btn_operator_2": "👤 Оператор 2",
        "btn_language": "🌍 Забон",        "btn_currency": "💱 Курби асъор",
        "currency_loading": "💱 <b>Курби асъор бор мешавад...</b>",
        "currency_error": "❌ Курби асъор бор нашуд",        "search_prompt": "🔍 <b>Ҷустуҷӯи мусиқӣ</b>\n\nНоми суруд ё хонандаро нависед:",
        "searching": "🔍 <b>Ҷустуҷӯ:</b> {query}...",
        "not_found": "❌ Чизе ёфт нашуд. Дархости дигар нависед.",
        "loading_popular": "🔥 <b>Суруди маъмул бор мешавад...</b>",
        "popular_title": "🔥 <b>Мусиқии маъмул</b>\n\nБарои шунидан суруд пахш кунед 🎧",
        "popular_error": "❌ Суруди маъмул бор нашуд",
        "btn_refresh": "🔄 Навсозӣ",
        "downloading": "🎧 <b>Суруд бор мешавад...</b>",
        "sending": "📤 <b>Фиристодан...</b>",
        "download_fail": "❌ Суруд бор нашуд. Дигареро санҷед.",
        "file_too_big": "❌ Файл хеле калон аст (>50 МБ)",
        "quality_selection_hint": "⚙️ Интихоби сифат ҳоло худкор истифода намешавад. Агар тугмаи MP3 ё MP4 дар паём бошад, онро боз пахш кунед.",
        "invalid_callback_data": "❌ Маълумоти амал нодуруст аст.",
        "voice_chat_unavailable": "🎙 Чатҳои овозӣ ҳоло танзим нашудаанд. Барои ин пайвастшавӣ бо pytgcalls ва идоракунии занги гурӯҳӣ лозим аст.",
        "voice_play_unavailable": "🎵 Пахши овозӣ дар чат ҳоло ғайрифаъол аст. Боргирӣ ва фиристодани оддии суруд аллакай кор мекунад.",
        "voice_pause_unavailable": "⏸ Плеери овозӣ ҳоло амалӣ нашудааст.",
        "voice_resume_unavailable": "▶️ Плеери овозӣ ҳоло амалӣ нашудааст.",
        "voice_leave_unavailable": "🚪 Бот ҳоло ба чатхои овозӣ пайваст намешавад.",
        "voice_now_playing_unavailable": "ℹ️ Пахши овозӣ ҳоло фаъол нест.",
        "help_text": (
            "<b>📋 Фармонҳо:</b>\n\n"
            "/search &lt;дархост&gt; — Ҷустуҷӯи мусиқӣ\n"
            "/popular — Мусиқии маъмул\n"
            "/help — Кӯмак\n\n"
            "<b>👤 Тамос бо операторон:</b> тугмаҳои поён\n\n"
            "<b>💡 Маслиҳат:</b> Номи сурудро дар чат нависед!"
        ),
        "choose_language": "🌍 <b>Забонро интихоб кунед / Выбери язык:</b>",
        "language_set": "✅ Забон интихоб шуд: <b>Тоҷикӣ</b> 🇹🇯",
        "default_reply": "🎵 Номи сурудро барои ҷустуҷӯ нависед\nё /start -ро пахш кунед",
        "url_detected": "🔗 Пайванд ёфт шуд!\n\nАмалро интихоб кунед:",
        "url_invalid": "❌ Пайванд кӯҳна шудааст ё дастрас нест. Онро боз фиристед.",
        "url_added_to_queue": "➕ Пайванд ба навбат илова шуд.",
        "settings_title": "⚙️ <b>Танзимот</b>\n\nИнтихоб кунед, ки чиро тағйир додан мехоҳед:",
        "settings_audio": "🎵 Сифати аудио",
        "settings_video": "📹 Сифати видео",
        "settings_language": "🌍 Забон",
        "settings_audio_choose": "🎵 <b>Сифати аудиоро интихоб кунед:</b>",
        "settings_video_choose": "📹 <b>Сифати видеоро интихоб кунед:</b>",
        "settings_audio_saved": "✅ Сифати аудио сабт шуд: <b>{value} kbps</b>",
        "settings_video_saved": "✅ Сифати видео сабт шуд: <b>{value}p</b>",
        "btn_referral": "👥 Рефералҳо",
        "btn_recognize": "🎤 Шинохтан",
        "recognize_prompt": "🎤 <b>Шинохтани мусиқӣ</b>\n\nПаёми овозӣ ё файли аудио фиристед, ман сурудро муайян мекунам!",
        "recognizing": "🎤 <b>Мусиқӣ шинохта мешавад...</b> Каме интизор шавед.",
        "recognize_result": (
            "🎵 <b>Суруд ёфт шуд!</b>\n\n"
            "🎤 <b>{artist}</b>\n"
            "📀 <b>{title}</b>\n"
            "{extra}"
        ),
        "recognize_fail": "😔 Мусиқиро шинохта нашуд. Пораи дигарро санҷед.",
        "referral_stats": (
            "👥 <b>Барномаи реферал</b>\n\n"
            "Дӯстонатонро даъват кунед!\n\n"
            "📊 <b>Омори шумо:</b>\n"
            "  • Дӯстони даъватшуда: <b>{count}</b>\n\n"
            "🔗 <b>Линки шумо:</b>\n"
            "<code>{link}</code>\n\n"
            "Ин линкро ба дӯстонатон фиристед!"
        ),
        "referral_welcome": "🎉 Шуморо дӯсттон даъват кард! Хуш омадед!",
        "referral_new": "🎉 Корбари нав аз линки шумо пайваст шуд! Ҳамагӣ: {count}",
        "subscription_join_button": "📢 Ба канал обуна шавед",
        "subscription_check_button": "✅ Обунаро санҷед",
        "subscription_required": (
            "📢 <b>Ба канали мо {channel} обуна шавед</b>\n\n"
            "Пас аз обуна бот бе маҳдудият кор мекунад.\n"
            "Бе обуна танҳо <b>{limit}</b> амалиёти ройгони мусиқӣ дастрас аст.\n"
            "Боқимонда: <b>{remaining}</b>."
        ),
        "subscription_check_failed": (
            "⚠️ Обуна ба {channel} санҷида нашуд.\n\n"
            "Обуна шавед ва тугмаи санҷишро боз пахш кунед.\n"
            "Бе обуна танҳо <b>{limit}</b> амалиёти ройгони мусиқӣ дастрас аст.\n"
            "Боқимонда: <b>{remaining}</b>."
        ),
        "subscription_verified": "✅ Обуна тасдиқ шуд. Маҳдудиятҳо бардошта шуданд.",
        "subscription_not_verified": "❌ Обуна ёфт нашуд. Ба канал обуна шавед ва боз санҷед.",
        "rate_limit": "⏳ Дархостҳо зиёд. Каме интизор шавед.",
        "error": "❌ Хатогӣ: {error}",
    },
    "uz": {
        "welcome": (
            "🎵 <b>{app_name} ga xush kelibsiz!</b>\n\n"
            "Salom, {name}! 👋\n\n"
            "Men sizga musiqa topish va yuklab olishda yordam beraman.\n\n"
            "🔍 <b>Qidiruv</b> tugmasini bosing yoki qo'shiq nomini yozing!"
        ),
        "btn_search": "🔍 Qidiruv",
        "btn_popular": "🔥 Mashhur",
        "btn_help": "📞 Yordam",
        "btn_operator": "👤 Operator",
        "btn_operator_1": "👤 Operator 1",
        "btn_operator_2": "👤 Operator 2",
        "btn_language": "🌍 Til",        "btn_currency": "💱 Valyuta kursi",
        "currency_loading": "💱 <b>Valyuta kurslari yuklanmoqda...</b>",
        "currency_error": "❌ Valyuta kurslarini yuklab bo'lmadi",        "search_prompt": "🔍 <b>Musiqa qidirish</b>\n\nQo'shiq nomi yoki ijrochi nomini kiriting:",
        "searching": "🔍 <b>Qidirilmoqda:</b> {query}...",
        "not_found": "❌ Hech narsa topilmadi. Boshqa so'rov kiriting.",
        "loading_popular": "🔥 <b>Mashhur qo'shiqlar yuklanmoqda...</b>",
        "popular_title": "🔥 <b>Mashhur musiqa</b>\n\nTinglash uchun qo'shiqni bosing 🎧",
        "popular_error": "❌ Mashhur qo'shiqlarni yuklab bo'lmadi",
        "btn_refresh": "🔄 Yangilash",
        "downloading": "🎧 <b>Qo'shiq yuklanmoqda...</b>",
        "sending": "📤 <b>Yuborilmoqda...</b>",
        "download_fail": "❌ Yuklab bo'lmadi. Boshqa qo'shiqni sinab ko'ring.",
        "file_too_big": "❌ Fayl juda katta (>50 MB)",
        "quality_selection_hint": "⚙️ Sifat tanlash hozircha avtomatik ishlatilmaydi. Agar xabarda MP3 yoki MP4 tugmasi bo'lsa, uni yana bosing.",
        "invalid_callback_data": "❌ Amal uchun ma'lumot noto'g'ri.",
        "voice_chat_unavailable": "🎙 Ovozli chatlar hali sozlanmagan. Buning uchun pytgcalls integratsiyasi va guruh qo'ng'irog'ini boshqarish kerak.",
        "voice_play_unavailable": "🎵 Ovozli chatda ijro hozircha o'chirilgan. Oddiy yuklab olish va trek yuborish allaqachon ishlaydi.",
        "voice_pause_unavailable": "⏸ Ovozli pleyer hali amalga oshirilmagan.",
        "voice_resume_unavailable": "▶️ Ovozli pleyer hali amalga oshirilmagan.",
        "voice_leave_unavailable": "🚪 Bot hozir ovozli chatlarga ulanmaydi.",
        "voice_now_playing_unavailable": "ℹ️ Hozir ovozli ijro faol emas.",
        "help_text": (
            "<b>📋 Buyruqlar:</b>\n\n"
            "/search &lt;so'rov&gt; — Musiqa qidirish\n"
            "/popular — Mashhur musiqa\n"
            "/help — Yordam\n\n"
            "<b>👤 Operatorlar bilan aloqa:</b> quyidagi tugmalar\n\n"
            "<b>💡 Maslahat:</b> Chatga qo'shiq nomini yozing!"
        ),
        "choose_language": "🌍 <b>Tilni tanlang / Выбери язык:</b>",
        "language_set": "✅ Til tanlandi: <b>O'zbekcha</b> 🇺🇿",
        "default_reply": "🎵 Qidirish uchun qo'shiq nomini yozing\nyoki /start bosing",
        "url_detected": "🔗 Havola aniqlandi!\n\nAmalni tanlang:",
        "url_invalid": "❌ Havola eskirgan yoki mavjud emas. Uni qayta yuboring.",
        "url_added_to_queue": "➕ Havola navbatga qo'shildi.",
        "settings_title": "⚙️ <b>Sozlamalar</b>\n\nNimani o'zgartirmoqchi ekaningizni tanlang:",
        "settings_audio": "🎵 Audio sifati",
        "settings_video": "📹 Video sifati",
        "settings_language": "🌍 Til",
        "settings_audio_choose": "🎵 <b>Audio sifatini tanlang:</b>",
        "settings_video_choose": "📹 <b>Video sifatini tanlang:</b>",
        "settings_audio_saved": "✅ Audio sifati saqlandi: <b>{value} kbps</b>",
        "settings_video_saved": "✅ Video sifati saqlandi: <b>{value}p</b>",
        "btn_referral": "👥 Referallar",
        "btn_recognize": "🎤 Aniqlash",
        "recognize_prompt": "🎤 <b>Musiqani aniqlash</b>\n\nOvozli xabar yoki audio fayl yuboring, men qo'shiqni aniqlayman!",
        "recognizing": "🎤 <b>Musiqa aniqlanmoqda...</b> Biroz kuting.",
        "recognize_result": (
            "🎵 <b>Qo'shiq topildi!</b>\n\n"
            "🎤 <b>{artist}</b>\n"
            "📀 <b>{title}</b>\n"
            "{extra}"
        ),
        "recognize_fail": "😔 Musiqani aniqlab bo'lmadi. Boshqa parchani sinab ko'ring.",
        "referral_stats": (
            "👥 <b>Referal dasturi</b>\n\n"
            "Do'stlaringizni taklif qiling!\n\n"
            "📊 <b>Statistikangiz:</b>\n"
            "  • Taklif qilingan do'stlar: <b>{count}</b>\n\n"
            "🔗 <b>Sizning havolangiz:</b>\n"
            "<code>{link}</code>\n\n"
            "Bu havolani do'stlaringizga yuboring!"
        ),
        "referral_welcome": "🎉 Sizni do'stingiz taklif qildi! Xush kelibsiz!",
        "referral_new": "🎉 Havolangiz orqali yangi foydalanuvchi qo'shildi! Jami: {count}",
        "subscription_join_button": "📢 Kanalga obuna bo'ling",
        "subscription_check_button": "✅ Obunani tekshirish",
        "subscription_required": (
            "📢 <b>{channel} kanalimizga obuna bo'ling</b>\n\n"
            "Obuna bo'lgandan keyin bot cheklovsiz ishlaydi.\n"
            "Obunasiz faqat <b>{limit}</b> ta bepul musiqiy amal mavjud.\n"
            "Qoldi: <b>{remaining}</b>."
        ),
        "subscription_check_failed": (
            "⚠️ {channel} ga obuna tekshirilmadi.\n\n"
            "Obuna bo'ling va tekshirish tugmasini yana bosing.\n"
            "Obunasiz faqat <b>{limit}</b> ta bepul musiqiy amal mavjud.\n"
            "Qoldi: <b>{remaining}</b>."
        ),
        "subscription_verified": "✅ Obuna tasdiqlandi. Cheklovlar olib tashlandi.",
        "subscription_not_verified": "❌ Obuna topilmadi. Kanalga obuna bo'lib, yana tekshiring.",
        "rate_limit": "⏳ So'rovlar ko'p. Biroz kuting.",
        "error": "❌ Xatolik: {error}",
    },
}


def get_text(key: str, lang: str = "ru", **kwargs) -> str:
    """Получает перевод по ключу и языку."""
    t = TEXTS.get(lang, TEXTS["ru"])
    text = t.get(key, TEXTS["ru"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text
