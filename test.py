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
PAYMENT_PROVIDER_TOKEN = '371317599:TEST:1660282710908'

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
 ) = range(15)


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
def _post_product(user):
    try:
        models.Product(
            owner=user['id'],
            category=user['category'],
            title=user['title'],
            description=user['description'],
            price=user['price'],
            photo=f'{user["photo"]}.jpg',
        ).save()

        return True
    except Exception as e:
        print(e)
        return False


@sync_to_async
def _get_products(user_id):
    return models.Product.objects.filter(owner=user_id).values()


@sync_to_async
def _delete_product(user, photo):
    try:
        models.Product.objects.filter(id=user, photo=str(photo) + '.jpg').delete()
        print(str(photo) + '.jpg')

        return True
    except Exception as e:
        print(e)
        return False


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['id'] = user.id

    await update.message.reply_text('Welcome!')
    await update.message.reply_text('Enter your username')

    return USERNAME


async def username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username'] = update.message.text

    button = [[KeyboardButton(text='send my contact', request_contact=True)]]

    await update.message.reply_text('Tap the button below to send your phone number',
                                    reply_markup=ReplyKeyboardMarkup(button, resize_keyboard=True))

    return PHONE_NUMBER


async def phone_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone_number'] = update.message.contact.phone_number

    if not await _is_client(context.user_data['id']):
        await _post_client(context.user_data)

    await update.message.reply_text('Saved')
    await update.message.reply_text(
        'What do you want to do?',
        reply_markup=ReplyKeyboardMarkup([
            ['Add product'],
            ['Show products'],
            ['Delete product'],
        ], resize_keyboard=True)
    )

    return MENU


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'What do you want to do?',
        reply_markup=ReplyKeyboardMarkup([
            ['Add product'],
            ['Show products'],
            ['Delete product'],
        ], resize_keyboard=True)
    )

    return MENU


async def add_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Choose product category',
        reply_markup=ReplyKeyboardMarkup([
            ['Category', 'Title'],
            ['Description'],
            ['Price', 'Photo', 'Ship'],
            ['Status', 'Back'],
        ], resize_keyboard=True)
    )

    return ADD_PRODUCT


async def pre_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Enter product category')

    return CATEGORY


async def pre_title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Enter product title')

    return TITLE


async def pre_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Enter product description')

    return DESCRIPTION


async def pre_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Enter product price')

    return PRICE


async def pre_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send product photo')

    return PHOTO


async def pre_shipping_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Do you want to add shipping options?',
        reply_markup=ReplyKeyboardMarkup([
            ['Yes', 'No'],
        ], resize_keyboard=True)
    )

    return SHIPPING_CHOICE


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text

    await update.message.reply_text('Saved')
    return ADD_PRODUCT


async def title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text

    await update.message.reply_text('Saved')
    return ADD_PRODUCT


async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text

    await update.message.reply_text('Saved')
    return ADD_PRODUCT


async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text

    await update.message.reply_text('Saved')
    return ADD_PRODUCT


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id
    file = await context.bot.get_file(file_id)
    context.user_data['photo'] = file_id

    await file.download(f'img/{context.user_data["photo"]}.jpg')

    await update.message.reply_text('Saved')
    return ADD_PRODUCT


async def with_shipping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shipping'] = update.message.text

    await update.message.reply_text(
        'Saved',
        reply_markup=ReplyKeyboardMarkup([
            ['Category', 'Title'],
            ['Description'],
            ['Price', 'Photo', 'Ship'],
            ['Status', 'Back'],
        ], resize_keyboard=True)
    )

    return ADD_PRODUCT


async def without_shipping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shipping'] = update.message.text
    await update.message.reply_text(
        'Saved',
        reply_markup=ReplyKeyboardMarkup([
            ['Category', 'Title'],
            ['Description'],
            ['Price', 'Photo', 'Ship'],
            ['Status', 'Back'],
        ], resize_keyboard=True)
    )

    return ADD_PRODUCT


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = f"""
Category: {context.user_data.get('category', 'Not set')}
Title: {context.user_data.get('title', 'Not set')}
Description: {context.user_data.get('description', 'Not set')}
Price: {context.user_data.get('price', 'Not set')}
Photo ID: {context.user_data.get('photo', 'Not set')}
Shipping: {context.user_data.get('shipping', 'Not set')}
Username: {context.user_data.get('username', 'Not set')}
Contact: {context.user_data.get('phone_number', 'Not set')}

    """

    if context.user_data.get('photo', 'Not set') != 'Not set':
        await update.message.reply_photo(
            photo=open(f'img/{context.user_data["photo"]}.jpg', 'rb'),
            caption=txt,
            reply_markup=ReplyKeyboardMarkup([
                ['Clear', 'Proceed'],
                ['Done'],
            ], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            txt,
            reply_markup=ReplyKeyboardMarkup([
                ['Clear', 'Proceed'],
                ['Done'],
            ], resize_keyboard=True)
        )

    return STATUS


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('photo', 'Not set') != 'Not set':
        os.remove(f'img/{context.user_data["photo"]}.jpg')
    context.user_data.clear()

    await update.message.reply_text('Cleared')
    return STATUS


async def proceed_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['id'] = user.id

    _post = await _post_product(context.user_data)

    if _post:
        await update.message.reply_text(
            'Proceeded seccessfully',
            reply_markup=ReplyKeyboardMarkup([
                ['Add product'],
                ['Show products'],
                ['Delete product'],
            ], resize_keyboard=True)
        )

        return MENU
    else:
        await update.message.reply_text(
            'Something went wrong\nTry again',
            reply_markup=ReplyKeyboardMarkup([
                ['Category', 'Title'],
                ['Description'],
                ['Price', 'Photo', 'Ship'],
                ['Status', 'Back'],
            ], resize_keyboard=True)
        )

        return ADD_PRODUCT


async def done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Choose product category',
        reply_markup=ReplyKeyboardMarkup([
            ['Category', 'Title'],
            ['Description'],
            ['Price', 'Photo', 'Ship'],
            ['Status', 'Back'],
        ], resize_keyboard=True)
    )

    return ADD_PRODUCT


async def show_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    products = await _get_products(user.id)

    if products:
        for product in products:
            txt = f"""
Category: {product['category']}
Title: {product['title']}
Description: {product['description']}
Price: {product['price']}
                """

            await update.message.reply_photo(
                photo=open(f'img/{product["photo"]}', 'rb'),
                caption=txt
            )

    return MENU


async def pre_delete_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Enter photo ID',
        reply_markup=ReplyKeyboardMarkup([
            ['Back'],
        ], resize_keyboard=True)
    )

    return DELETE_PRODUCT


async def delete_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_id = update.message.text

    delete = await _delete_product(user.id, photo_id)

    if delete:
        await update.message.reply_text(
            'Deleted seccessfully',
            reply_markup=ReplyKeyboardMarkup([
                ['Add product'],
                ['Show products'],
                ['Delete product'],
            ], resize_keyboard=True)
        )

        return MENU
    else:
        await update.message.reply_text(
            'Something went wrong\nTry again',
            reply_markup=ReplyKeyboardMarkup([
                ['Add product'],
                ['Show products'],
                ['Delete product'],
            ], resize_keyboard=True)
        )

        return MENU



async def end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start to start again', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).read_timeout(7).get_updates_read_timeout(42).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_handler),
            CommandHandler('menu', menu_handler),
            CommandHandler('add', add_product_handler),
        ],
        states={
            USERNAME: [
                MessageHandler(filters.TEXT, username_handler),
            ],
            PHONE_NUMBER: [
                MessageHandler(filters.CONTACT, phone_number_handler),
            ],
            MENU: [
                MessageHandler(filters.Regex(".*Add product$"), add_product_handler),
                MessageHandler(filters.Regex(".*Show products$"), show_products_handler),
                MessageHandler(filters.Regex(".*Delete product$"), pre_delete_product_handler),
            ],
            ADD_PRODUCT: [
                MessageHandler(filters.Regex(".*Category$"), pre_category_handler),
                MessageHandler(filters.Regex(".*Title$"), pre_title_handler),
                MessageHandler(filters.Regex(".*Description$"), pre_description_handler),
                MessageHandler(filters.Regex(".*Price$"), pre_price_handler),
                MessageHandler(filters.Regex(".*Photo$"), pre_photo_handler),
                MessageHandler(filters.Regex(".*Ship$"), pre_shipping_choice_handler),
                MessageHandler(filters.Regex(".*Status$"), status_handler),
                MessageHandler(filters.Regex(".*Back$"), menu_handler),
            ],
            SHOW_PRODUCTS: [
                MessageHandler(filters.TEXT, show_products_handler)
            ],
            DELETE_PRODUCT: [
                MessageHandler(filters.TEXT, delete_product_handler),
                MessageHandler(filters.Regex(".*Back$"), menu_handler),
            ],
            STATUS: [
                MessageHandler(filters.Regex(".*Clear$"), clear_handler),
                MessageHandler(filters.Regex(".*Proceed$"), proceed_handler),
                MessageHandler(filters.Regex(".*Done$"), done_handler),
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
                MessageHandler(filters.Regex(".*Yes$"), with_shipping_handler),
                MessageHandler(filters.Regex(".*No$"), without_shipping_handler),
            ],
            WITH_SHIPPING: [
                MessageHandler(filters.TEXT, with_shipping_handler),
            ],
            WITHOUT_SHIPPING: [
                MessageHandler(filters.TEXT, without_shipping_handler),
            ],
        },
        fallbacks=[CommandHandler('end', end_handler)],
    )

    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()
