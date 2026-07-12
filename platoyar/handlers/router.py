from telegram import Update
from telegram.ext import ContextTypes

from .menu import *
from .profile import *
from .wallet import *
from .ads import *
from .myads import *
from .admin import *
from .buy import *
from .search import *
from .adminpanel import *
from .shop import *


async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # اولویت ۱: ثبت قیمت
    if data.startswith("price_set_"):
        await price_set_handler(update, context)
        return
    
    # اولویت ۲: کپی لینک
    if data.startswith("copy_link_"):
        await copy_link_callback(update, context)
        return
    
    # تماس صوتی
    if data.startswith("voice_call_"):
        await voice_call(update, context)
        return
    
    # رد کردن با گزینه‌ها
    if data.startswith("reject_fake_ad_") or data.startswith("reject_info_ad_") or data.startswith("reject_violation_ad_") or data.startswith("reject_other_ad_"):
        await handle_reject_with_option(update, context)
        return
    if data.startswith("reject_fake_price_") or data.startswith("reject_info_price_") or data.startswith("reject_violation_price_") or data.startswith("reject_other_price_"):
        await handle_reject_with_option(update, context)
        return
    
    # شارژ کیف پول
    if data.startswith("confirm_charge_"):
        await confirm_charge(update, context)
        return
    if data.startswith("reject_charge_"):
        await reject_charge(update, context)
        return
    
    # فروشگاه
    if data.startswith("shop:"):
        await shop_nav(update, context)
        return
    if data.startswith("shopstart:"):
        await shop_start(update, context)
        return
    if data.startswith("shopbuy:"):
        await shop_buy_digital(update, context)
        return
    if data.startswith("shoppaycard:"):
        await shop_pay_card(update, context)
        return
    if data.startswith("shoppayonline:"):
        await shop_pay_online(update, context)
        return
    if data.startswith("shopprice:"):
        await shop_price_start(update, context)
        return
    if data.startswith("shopbulk:"):
        await shop_bulk_start(update, context)
        return

    # پنل مدیریت کاربران
    if data == "admin_panel":
        await show_admin_panel(update, context)
        return
    if data == "ap_stats":
        await ap_stats(update, context)
        return
    if data == "ap_users":
        await ap_users_list(update, context)
        return
    if data == "ap_userinfo":
        await ap_user_info_prompt(update, context)
        return
    if data == "ap_adsearch":
        await ap_adsearch_prompt(update, context)
        return
    if data == "ap_broadcast":
        await ap_broadcast_prompt(update, context)
        return
    if data == "ap_sendone":
        await ap_sendone_prompt(update, context)
        return
    if data.startswith("ap_owner_"):
        await ap_owner_info(update, context)
        return

    # بقیه دکمه‌ها
    if data == "back_to_main":
        await back_to_main(update, context)
    elif data == "shop_menu":
        await shop_open(update, context)
    elif data == "support_menu":
        await support_menu(update, context)
    elif data == "agahi_menu":
        await show_agahi_menu(update, context)
    elif data == "referral_menu":
        await referral_menu(update, context)
    elif data == "agahi_submit_start":
        await agahi_submit_start(update, context)
    elif data == "agahi_profile":
        await show_profile(update, context)
    elif data == "agahi_profile_complete":
        await agahi_profile_complete(update, context)
    elif data == "my_ads_menu":
        await my_ads_menu(update, context)
    elif data == "view_my_ads":
        await view_my_ads(update, context)
    elif data == "cancel_my_ad":
        await cancel_my_ad(update, context)
    elif data == "request_discount_on_ad":
        await request_discount_on_ad(update, context)
    elif data == "search_menu":
        await search_menu(update, context)
    elif data == "wallet_menu":
        await wallet_menu(update, context)
    elif data == "charge_wallet":
        await charge_wallet(update, context)
    elif data == "withdraw_wallet":
        await withdraw_wallet(update, context)
    elif data == "withdraw_confirm_same":
        await withdraw_confirm_same(update, context)
    elif data == "withdraw_new_card":
        await withdraw_new_card(update, context)
    elif data == "withdraw_final":
        await withdraw_final(update, context)
    elif data == "price_only_start":
        await price_only_start(update, context)
    elif data == "game_platoyar":
        await game_platoyar(update, context)
    elif data == "game_inactive":
        await game_inactive(update, context)
    elif data == "price_method_self":
        await price_method_self(update, context)
    elif data == "price_method_admin":
        await price_method_admin(update, context)
    elif data == "publish_game":
        await publish_game(update, context)
    elif data == "publish_both":
        await publish_both(update, context)
    elif data == "pay_from_wallet":
        await pay_from_wallet(update, context)
    elif data == "card_payment_after_wallet":
        await card_payment_after_wallet(update, context)
    elif data == "card_payment_only":
        await card_payment_only(update, context)
    elif data == "payment_done":
        await payment_done(update, context)
    elif data == "payment_done_after_wallet":
        await payment_done_after_wallet(update, context)
    elif data == "check_membership":
        await check_membership_callback(update, context)
    elif data == "pay_price_only_wallet":
        await pay_price_only_wallet(update, context)
    elif data == "pay_price_only_card":
        await pay_price_only_card(update, context)
    elif data == "terms_accepted_start_form":
        await terms_accepted_start_form(update, context)
    elif data == "discount_method_amount":
        await discount_method_amount(update, context)
    elif data == "discount_method_percent":
        await discount_method_percent(update, context)
    elif data == "cancel_operation":
        await cancel_current_operation(update, context)
    elif data.startswith("view_single_ad_"):
        await view_single_ad(update, context)
    elif data.startswith("cancel_ad_"):
        await cancel_ad_confirm(update, context)
    elif data.startswith("confirm_cancel_ad_"):
        await confirm_cancel_ad(update, context)
    elif data.startswith("request_discount_"):
        await request_discount_for_ad(update, context)
    elif data.startswith("approve_discount_"):
        await approve_discount(update, context)
    elif data.startswith("reject_discount_"):
        await reject_discount(update, context)
    elif data.startswith("select_color_"):
        ad_id = int(data.split("_")[2])
        await select_button_color(update, context, ad_id)
    elif data.startswith("color_green_"):
        ad_id = int(data.split("_")[2])
        await set_button_color(update, context, ad_id, "green")
    elif data.startswith("color_red_"):
        ad_id = int(data.split("_")[2])
        await set_button_color(update, context, ad_id, "red")
    elif data.startswith("color_blue_"):
        ad_id = int(data.split("_")[2])
        await set_button_color(update, context, ad_id, "blue")
    elif data.startswith("set_price_"):
        ad_id = int(data.split("_")[2])
        await set_price_and_approve(update, context, ad_id)
    elif data.startswith("reject_ad_"):
        await reject_ad(update, context)
    elif data.startswith("reject_price_only_"):
        await reject_price_only_request(update, context)
    elif data.startswith("confirm_buy_"):
        await confirm_buy(update, context)
    elif data.startswith("receipt_buy_"):
        await receipt_buy(update, context)
    elif data.startswith("confirm_sale_"):
        await confirm_sale(update, context)
    elif data.startswith("reject_sale_"):
        await reject_sale(update, context)
    elif data.startswith("withdraw_approve_"):
        await withdraw_approve(update, context)
    elif data.startswith("withdraw_reject_"):
        await withdraw_reject(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ---- فروشگاه ----
    if context.user_data.get('shop_pending'):
        await shop_receive_payment_receipt(update, context)
        return
    if context.user_data.get('shop_collect'):
        await shop_collect_message(update, context)
        return
    if context.user_data.get('shop_dig'):
        await shop_digital_message(update, context)
        return
    if context.user_data.get('shop_setprice'):
        await shop_receive_setprice(update, context)
        return
    if context.user_data.get('shop_bulk'):
        await shop_receive_bulk(update, context)
        return

    # ---- پنل مدیریت (ورودی‌های متنی) ----
    if context.user_data.get('ap_waiting_user_id'):
        await ap_process_user_info(update, context)
        return
    if context.user_data.get('ap_waiting_adsearch'):
        await ap_process_adsearch(update, context)
        return
    if context.user_data.get('ap_waiting_broadcast'):
        await ap_process_broadcast(update, context)
        return
    if context.user_data.get('ap_waiting_sendone_id'):
        await ap_process_sendone_id(update, context)
        return
    if context.user_data.get('ap_waiting_sendone_text'):
        await ap_process_sendone_text(update, context)
        return

    if context.user_data.get('reject_other_ad_id'):
        await process_reject_other_reason(update, context)
        return
    
    if context.user_data.get('waiting_charge_receipt'):
        await handle_charge_receipt(update, context)
        return
    
    if context.user_data.get('set_price_ad_id'):
        await process_set_price(update, context)
        return
    if context.user_data.get('set_price_only_id'):
        await process_set_price_only(update, context)
        return
    
    if context.user_data.get('reject_ad_id'):
        await process_reject_reason(update, context)
        return
    if context.user_data.get('reject_sale_id'):
        await process_reject_sale_reason(update, context)
        return
    if context.user_data.get('reject_charge_user_id'):
        await process_reject_charge(update, context)
        return
    
    if context.user_data.get('profile_step'):
        await handle_profile_completion(update, context)
        return
    if context.user_data.get('agahi_step'):
        if context.user_data.get('price_only_mode'):
            await handle_price_only_form(update, context)
        else:
            await handle_normal_agahi_form(update, context)
        return
    
    if context.user_data.get('waiting_custom_price'):
        await get_custom_price(update, context)
        return
    if context.user_data.get('waiting_payment_receipt'):
        await handle_payment_receipt(update, context)
        return
    if context.user_data.get('waiting_payment_receipt_after_wallet'):
        await handle_payment_receipt_after_wallet(update, context)
        return
    if context.user_data.get('waiting_buy_receipt'):
        await handle_buy_receipt(update, context)
        return
    if context.user_data.get('search_mode'):
        await search_ad(update, context)
        return
    if context.user_data.get('waiting_new_card'):
        await process_new_card(update, context)
        return
    if context.user_data.get('withdraw_reject_user_id'):
        await process_withdraw_reject(update, context)
        return
    if context.user_data.get('waiting_group_link'):
        await receive_group_link(update, context)
        return
    if context.user_data.get('waiting_price_only_receipt'):
        await handle_price_only_receipt(update, context)
        return
    if context.user_data.get('waiting_discount_value'):
        await process_discount_value(update, context)
        return
    if context.user_data.get('withdraw_approve_user_id'):
        await handle_withdraw_receipt(update, context)
        return
    if context.user_data.get('charge_user_id'):
        await process_charge_amount(update, context)
        return
    
    if update.message and update.message.text:
        text = update.message.text
        if text.startswith('/start'):
            await start_with_ref(update, context)
            return
        elif text.startswith('/searchadmin'):
            parts = text.split()
            if len(parts) > 1:
                context.args = [parts[1]]
            await search_admin_command(update, context)
            return
        else:
            await update.message.reply_text("❓ دستور ناشناخته!\nاز /start استفاده کنید.")
