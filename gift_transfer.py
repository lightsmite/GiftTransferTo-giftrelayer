# -*- coding: utf-8 -*-
"""
Передаёт все UNIQUE/LIMITED подарки в @giftrelayer.
• exclude.txt  — список slug-URL или id:NNN, которые НЕ трогаем.
• TG_SESSION_STRING или *.session или телефон/пароль — авторизация.
pip install --upgrade telethon python-dotenv
"""
import asyncio, sys
from pathlib import Path
from os import getenv
from dotenv import load_dotenv
from telethon import TelegramClient, errors, functions, types
from telethon.sessions import StringSession
from telethon.errors.rpcbaseerrors import BadRequestError

ROOT = Path(__file__).resolve().parent
# ---------- .env ----------
env_file = ROOT / '.env'
if not env_file.exists():
    print('❌ .env not found'); sys.exit(1)
load_dotenv(env_file)

def need(k): v = getenv(k); 0/0 if not v else None; return v
API_ID, API_HASH = int(need('TELEGRAM_API_ID')), need('TELEGRAM_API_HASH')
PHONE, PASSW     = getenv('TELEGRAM_PHONE_NUMBER'), getenv('TELEGRAM_PASSWORD')
SESSION_S        = getenv('TG_SESSION_STRING')
DEST_USERNAME    = 'giftrelayer'

# ---------- exclude.txt ----------
ex_f = ROOT / 'exclude.txt'
EXCLUDE = {l.strip() for l in ex_f.read_text(encoding='utf-8').splitlines()
           if ex_f.exists() and l.strip() and not l.lstrip().startswith('#')} if ex_f.exists() else set()

def key_of(gift: types.TypeStarGift) -> str:
    return f'https://t.me/nft/{gift.slug}' if getattr(gift, 'slug', None) else f'id:{gift.id}'

# ---------- session ----------
if SESSION_S:
    sess = StringSession(SESSION_S)
else:
    sf = list(ROOT.glob('*.session'))
    sess = sf[0].stem if len(sf) == 1 else StringSession()

client = TelegramClient(sess, API_ID, API_HASH)

async def login():
    await client.connect()
    if await client.is_user_authorized(): return
    if not PHONE: print('❌ PHONE needed'); sys.exit(1)
    await client.send_code_request(PHONE)
    code = input('Code: ').strip()
    try:
        await client.sign_in(PHONE, code)
    except errors.SessionPasswordNeededError:
        if not PASSW: print('❌ PASSWORD needed'); sys.exit(1)
        await client.sign_in(password=PASSW)
    if isinstance(client.session, StringSession):
        print('\nTG_SESSION_STRING:\n', client.session.save(), '\n')

async def main():
    await login()
    saved: types.payments.SavedStarGifts = await client(
        functions.payments.GetSavedStarGiftsRequest(peer=types.InputPeerSelf(),
                                                    offset='', limit=100))
    dst = await client.get_input_entity(DEST_USERNAME)

    gifts = [g for g in saved.gifts
             if (isinstance(g.gift, types.StarGiftUnique) or getattr(g.gift, 'limited', False))
             and key_of(g.gift) not in EXCLUDE]

    if not gifts:
        print('✅ Nothing to transfer'); return

    processed = set()
    for sg in gifts:
        if sg.msg_id in processed: continue
        processed.add(sg.msg_id)
        k = key_of(sg.gift)

        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=sg.msg_id),
            to_id=dst
        )
        try:
            form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
            price = sum(p.amount for p in form.invoice.prices)   # Stars
            if price == 0:
                # иногда Telegram всё-таки шлёт 0 → безопаснее прямой трансфер
                raise BadRequestError(400, 'NO_PAYMENT_NEEDED', None)
            print(f'➡️  {k} → @{DEST_USERNAME}  (-{price} Stars)')
            await client(functions.payments.SendStarsFormRequest(
                form_id=form.form_id, invoice=invoice))
            print(f'✅ Done {k}')
        except BadRequestError as e:
            if e.message == 'NO_PAYMENT_NEEDED':
                # бесплатный перевод
                try:
                    await client(functions.payments.TransferStarGiftRequest(
                        stargift=types.InputSavedStarGiftUser(msg_id=sg.msg_id),
                        to_id=dst
                    ))
                    print(f'✅ Free-transfer {k}')
                except BadRequestError as e2:
                    if e2.message in {'STARGIFT_NOT_UNIQUE', 'STARGIFT_USAGE_LIMITED'}:
                        print(f'⏩ Skip {k} ({e2.message})')
                    else:
                        raise
            elif e.message in {'STARGIFT_NOT_UNIQUE', 'STARGIFT_USAGE_LIMITED'}:
                print(f'⏩ Skip {k} ({e.message})')
            else:
                raise

if __name__ == '__main__':
    asyncio.run(main())
