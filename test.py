# import below, to work Telegram Bot with Django Rest Framework properly
# start

import sys

sys.dont_write_bytecode = True

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django

django.setup()

from app import models

from asgiref.sync import sync_to_async
# end

import os

from telegram import (
    Update,
    LabeledPrice,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    ShippingQueryHandler,
    PreCheckoutQueryHandler,
    CallbackQueryHandler,
)
import requests


TELEGRAM_BOT_TOKEN = "5565038506:AAE5p97y4rW8r6yt4nXwEgg9Adea1UzYJmE"
DEFAULT_PAYMENT_URL = 'https://checkout.paycom.uz/632db4263ea226c2b6ff9e51'

_about = """
Bot orqali o\'z mahsulotlaringizni oson va tez tarzda soting.

Botdan foydalanish uchun quyidagi amallarni bajaring:
 - Botga /start buyrug\'ini yuboring
 - Ismingizni kiriting
 - Telefon raqamingizni yuboring

Mahsulot qo\'shish, ko\'rish, o\'chirish uchun quyidagi amallarni bajaring:
 - Mahsulotingizni qo\'shish uchun /add buyrug\'ini yuboring yoki "Mahsulot qo\'shish" tugmasini bosing
 - Mahsulotlaringizni ko\'rish uchun /show buyrug\'ini yuboring yoki "Mening mahsulotlarim" tugmasini bosing
 - Mahsulotingizni o\'chirish uchun /del buyrug\'ini yuboring yoki "Mahsulotni o\'chirish" tugmasini bosing
    
Mahsulotni sotish uchun quyidagi amallarni bajaring:
 - Mahsulotingizni tanlang va Forward qiling
    
Commands xaqida ma\'lumot olish uchun /cmd buyrug\'ini yuboring
"""

_commands = """
/start - Botni ishga tushirish
/menu - Bosh menyuni ochish
/add - Mahsulot qo\'shish
/show - Mahsulotlarni ko\'rish
/del - Mahsulotni o\'chirish
/doc - Bot haqida
/end - Botni to\'xtatish
"""

_commands_ = {
    'start': "start_handler",
    'menu': "menu_handler",
    'add': "add_product_handler",
    'show': "show_products_handler",
    'del': "delete_product_handler",
    'doc': "doc_handler",
    'end': "end_handler",
}

MAIN_MENU_KEYBOARD = [['Mahsulot qo\'shish'], ['Mening mahsulotlarim'], ['Mahsulotni o\'chirish']]
SECONDARY_MENU_KEYBOARD = [['Kategoriya', 'Nom'], ['Tavsif', 'Narx'], ['Rasm', 'Eltib Berish', "To\'lov"], ['Status', 'Orqaga']]

(USERNAME,
 PHONE_NUMBER,
 MENU,
 ADD_PRODUCT,
 SHOW_PRODUCTS,
 DELETE_PRODUCT,
 STATUS,
 CATEGORY,
 TITLE,
 DESCRIPTION,
 PRICE,
 PHOTO,
 SHIPPING_CHOICE,
 WITH_SHIPPING,
 WITHOUT_SHIPPING,
 PAYMENT,
 ) = range(16)


@sync_to_async
def _post_client(user):
    try:
        models.TGClient(
            tg_id=user['id'],
            username=user['username'],
            phone_number=user['phone_number'],
        ).save()

        return True
    except Exception as e:
        print(e)
        return False


@sync_to_async
def _is_client(user_id):
    return models.TGClient.objects.filter(tg_id=user_id).exists()


@sync_to_async
def _get_client(user_id):
    return models.TGClient.objects.filter(tg_id=user_id).values()


@sync_to_async
def _post_product(user):
    try:
        models.Product(
            tg_id=user['id'],
            username=user['username'],
            phone_number=user['phone_number'],
            category=user['category'],
            title=user['title'],
            description=user['description'],
            price=user['price'],
            photo=f'{user["photo"]}.jpg',
            ship=user['shipping'],
            payment=user['payment'],
        ).save()
        return True
    except Exception as e:
        print(e)
        return False


@sync_to_async
def _get_products(user_id):
    return models.Product.objects.filter(tg_id=user_id).values()


@sync_to_async
def _delete_product(user, photo):
    try:
        models.Product.objects.filter(tg_id=user, photo=str(photo) + '.jpg').delete()
        return True
    except Exception as e:
        print(e)
        return False


async def doc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=_about)


async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=_commands)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['id'] = user.id

    await update.message.reply_text('Assalomu alaykum, ' + user.first_name + '!')
    await update.message.reply_text('Ismingizni kiriting')

    return USERNAME


async def username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username'] = update.message.text

    button = [[KeyboardButton(text='Telefon raqamini yuborish', request_contact=True)]]

    await update.message.reply_text('Telefon raqamingizni yuborish uchun quyidagi tugmani bosing',
                                    reply_markup=ReplyKeyboardMarkup(button, resize_keyboard=True))

    return PHONE_NUMBER


async def phone_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone_number'] = update.message.contact.phone_number

    if not await _is_client(context.user_data['id']):
        await _post_client(context.user_data)

    await update.message.reply_text('Saqlandi')
    await update.message.reply_text(
        'Yangi mahsulot qo\'shishga tayyormisiz?',
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
    )

    return MENU


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    client = await _get_client(user.id)
    context.user_data['id'] = client[0]['tg_id']
    context.user_data['username'] = client[0]['username']
    context.user_data['phone_number'] = client[0]['phone_number']

    await update.message.reply_text(
        'Yangi mahsulot qo\'shishga tayyormisiz?',
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
    )

    return MENU


async def add_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    client = await _get_client(user.id)
    context.user_data['id'] = client[0]['tg_id']
    context.user_data['username'] = client[0]['username']
    context.user_data['phone_number'] = client[0]['phone_number']

    await update.message.reply_text(
        'Mahsulotingiz ma\'lumotlarini birma-bir kiriting',
        reply_markup=ReplyKeyboardMarkup(SECONDARY_MENU_KEYBOARD, resize_keyboard=True)
    )

    return ADD_PRODUCT


async def pre_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Mahsulotingiz kategoriyasini kiriting')

    return CATEGORY


async def pre_title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Mahsulotingiz nomini kiriting')

    return TITLE


async def pre_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Mahsulotingiz tavsifini kiriting')

    return DESCRIPTION


async def pre_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Mahsulotingiz narxini kiriting')

    return PRICE


async def pre_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Mahsulotingiz rasmini yuboring')

    return PHOTO


async def pre_shipping_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Mahsulotingizni yetkazib berish xizmati bormi?',
        reply_markup=ReplyKeyboardMarkup([
            ['Bor', 'Yo\'q'],
        ], resize_keyboard=True)
    )

    return SHIPPING_CHOICE


async def pre_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Mahsulotingiz uchun to\'lov linkini kiriting')

    return PAYMENT


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text

    await update.message.reply_text('Saqlandi')
    return ADD_PRODUCT


async def title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text

    await update.message.reply_text('Saqlandi')
    return ADD_PRODUCT


async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text

    await update.message.reply_text('Saqlandi')
    return ADD_PRODUCT


async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text

    await update.message.reply_text('Saqlandi')
    return ADD_PRODUCT


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id
    file = await context.bot.get_file(file_id)

    try:
        context.user_data['photo'] = file_id
        await file.download(f'img/{context.user_data["photo"]}.jpg')
        await update.message.reply_text('Saqlandi')
    except Exception as e:
        print(e)
        await update.message.reply_text('Xatolik yuz berdi\nIltimos qaytadan yuboring')

    return ADD_PRODUCT


async def with_shipping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shipping'] = update.message.text

    await update.message.reply_text('Saqlandi',
                                    reply_markup=ReplyKeyboardMarkup(SECONDARY_MENU_KEYBOARD, resize_keyboard=True)
    )

    return ADD_PRODUCT


async def without_shipping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shipping'] = update.message.text
    await update.message.reply_text('Saqlandi',
                                    reply_markup=ReplyKeyboardMarkup(SECONDARY_MENU_KEYBOARD, resize_keyboard=True)
    )

    return ADD_PRODUCT


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['payment'] = update.message.text

    await update.message.reply_text('Saqlandi',
                                    reply_markup=ReplyKeyboardMarkup(SECONDARY_MENU_KEYBOARD, resize_keyboard=True)
    )

    return ADD_PRODUCT


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = f"""
Kategoriya: {context.user_data.get('category', 'Not set')}
Nomi: {context.user_data.get('title', 'Not set')}
Tavsif: {context.user_data.get('description', 'Not set')}
Narxi: {context.user_data.get('price', 'Not set')}
Eltib berish xizmati: {context.user_data.get('shipping', 'Not set')}
To\'lov linki: {context.user_data.get('payment', 'Not set')}
ID: {context.user_data.get('photo', 'Not set')}
Kimniki: {context.user_data.get('username', 'Not set')}
Aloqa: {context.user_data.get('phone_number', 'Not set')}

    """

    if context.user_data.get('photo', 'Not set') != 'Not set':
        await update.message.reply_photo(
            photo=open(f'img/{context.user_data["photo"]}.jpg', 'rb'),
            caption=txt,
            reply_markup=ReplyKeyboardMarkup([
                ['Yangilash', 'Tasdiqlash'],
                ['Orqaga']
            ], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            txt,
            reply_markup=ReplyKeyboardMarkup([
                ['Yangilash', 'Tasdiqlash'],
                ['Orqaga']
            ], resize_keyboard=True)
        )

    return STATUS


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('photo', 'Not set') != 'Not set':
        try:
            os.remove(f'img/{context.user_data["photo"]}.jpg')
        except FileNotFoundError:
            pass
    context.user_data.clear()

    user = update.effective_user
    client = await _get_client(user.id)
    context.user_data['id'] = client[0]['tg_id']
    context.user_data['username'] = client[0]['username']
    context.user_data['phone_number'] = client[0]['phone_number']

    await update.message.reply_text('O\'chirildi')

    return STATUS


async def proceed_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['id'] = user.id

    _post = await _post_product(context.user_data)

    if _post:
        await update.message.reply_text(
            'Mahsulotingiz muvaffaqiyatli yuborildi',
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        )

        return MENU
    else:
        await update.message.reply_text(
            'Mahsulotingiz tasdiqlanmadi\nIltimos qaytadan yuboring',
            reply_markup=ReplyKeyboardMarkup(SECONDARY_MENU_KEYBOARD, resize_keyboard=True)
        )

        return ADD_PRODUCT


async def done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Mahsulotingiz ma\'lumotlarini birma-bir kiriting',
        reply_markup=ReplyKeyboardMarkup(SECONDARY_MENU_KEYBOARD, resize_keyboard=True)
    )

    return ADD_PRODUCT


async def show_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    products = await _get_products(user.id)

    if products:
        for product in products:
            txt = f"""
Kategoriya: {product['category']}
Nomi: {product['title']}
Tavsif: {product['description']}
Narxi: {product['price']}
Eltib berish xizmati: {product['ship']}
ID: {product['photo'][:-4]}
Kimniki: {product['username']}
Aloqa: {product['phone_number']}
"""

            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('↗️ Sotib olish', url=product['payment'])]])

            await update.message.reply_photo(
                photo=open(f'img/{product["photo"]}', 'rb'),
                caption=txt,
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text('Sizda hech qanday mahsulot yo\'q')

    return MENU


async def pre_delete_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'O\'chirish uchun mahsulot ID raqamini kiriting',
        reply_markup=ReplyKeyboardMarkup([
            ['Orqaga'],
        ], resize_keyboard=True)
    )

    return DELETE_PRODUCT


async def delete_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_id = update.message.text

    delete = await _delete_product(user.id, photo_id)

    if delete:
        await update.message.reply_text(
            'Mahsulot muvaffaqiyatli o\'chirildi',
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        )
        try:
            os.remove(f'img/{photo_id} + .jpg')
        except FileNotFoundError:
            pass

        return MENU
    else:
        await update.message.reply_text(
            'Mahsulot topilmadi\nIltimos qaytadan kiriting',
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        )

        return MENU


async def end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Botdan qayta foydalanish uchun /menu bosing',
                                    reply_markup=ReplyKeyboardRemove())


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).read_timeout(7).get_updates_read_timeout(42).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_handler),
            CommandHandler('menu', menu_handler),
        ],
        states={
            USERNAME: [
                MessageHandler(filters.TEXT, username_handler),
            ],
            PHONE_NUMBER: [
                MessageHandler(filters.CONTACT, phone_number_handler),
            ],
            MENU: [
                MessageHandler(filters.Regex(".*Mahsulot qo\'shish$"), add_product_handler),
                MessageHandler(filters.Regex(".*Mening mahsulotlarim$"), show_products_handler),
                MessageHandler(filters.Regex(".*Mahsulotni o\'chirish$"), pre_delete_product_handler),
            ],
            ADD_PRODUCT: [
                MessageHandler(filters.Regex(".*Kategoriya$"), pre_category_handler),
                MessageHandler(filters.Regex(".*Nom$"), pre_title_handler),
                MessageHandler(filters.Regex(".*Tavsif$"), pre_description_handler),
                MessageHandler(filters.Regex(".*Narx$"), pre_price_handler),
                MessageHandler(filters.Regex(".*Rasm$"), pre_photo_handler),
                MessageHandler(filters.Regex(".*Eltib Berish$"), pre_shipping_choice_handler),
                MessageHandler(filters.Regex(".*To\'lov$"), pre_payment_handler),
                MessageHandler(filters.Regex(".*Status$"), status_handler),
                MessageHandler(filters.Regex(".*Orqaga$"), menu_handler),
            ],
            SHOW_PRODUCTS: [
                MessageHandler(filters.TEXT, show_products_handler)
            ],
            DELETE_PRODUCT: [
                MessageHandler(filters.TEXT, delete_product_handler),
                MessageHandler(filters.Regex(".*Orqaga$"), menu_handler),
            ],
            STATUS: [
                MessageHandler(filters.Regex(".*Yangilash$"), clear_handler),
                MessageHandler(filters.Regex(".*Tasdiqlash$"), proceed_handler),
                MessageHandler(filters.Regex(".*Orqaga$"), done_handler),
            ],
            CATEGORY: [
                MessageHandler(filters.TEXT, category_handler),
            ],
            TITLE: [
                MessageHandler(filters.TEXT, title_handler)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT, description_handler)
            ],
            PRICE: [
                MessageHandler(filters.TEXT, price_handler)
            ],
            PHOTO: [
                MessageHandler(filters.PHOTO, photo_handler)
            ],
            SHIPPING_CHOICE: [
                MessageHandler(filters.Regex(".*Bor$"), with_shipping_handler),
                MessageHandler(filters.Regex(".*Yo\'q$"), without_shipping_handler),
            ],
            WITH_SHIPPING: [
                MessageHandler(filters.TEXT, with_shipping_handler),
            ],
            WITHOUT_SHIPPING: [
                MessageHandler(filters.TEXT, without_shipping_handler),
            ],
            PAYMENT: [
                MessageHandler(filters.TEXT, payment_handler),
            ],
        },

        fallbacks=[
            CommandHandler('end', end_handler),
            CommandHandler('menu', menu_handler),
            CommandHandler('add', add_product_handler),
            CommandHandler('show', show_products_handler),
            CommandHandler('del', pre_delete_product_handler),
            CommandHandler('doc', doc_handler),
            CommandHandler('cmd', cmd_handler),
        ],
    )

    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()
