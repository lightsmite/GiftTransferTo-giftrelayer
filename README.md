# Gift Transfer Bot

Скрипт `gift_transfer.py` автоматически передаёт **UNIQUE** и **LIMITED**
подарки (Гифты) из профиля Telegram другому пользователю
(**@giftrelayer** по умолчанию).

* Подарки, перечисленные в `exclude.txt`, пропускаются. Ссылка на подарок.
* Если Telegram запрашивает оплату Stars (обычно 25 ⭐), скрипт оплачивает
  их автоматически.  
* «Бесплатные» подарки переводятся так же.
* Непереводимые (`STARGIFT_NOT_UNIQUE`, `STARGIFT_USAGE_LIMITED`) — просто
  пропускаются, не прерывая работу.

## Установка

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
