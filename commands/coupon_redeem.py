from pathlib import Path
import os
import json
import time
from utils import userUtils

# credits to Bulva2 for most of this code :)
def handle_couponRedeem(request, user_id, obj, json_data, config_data):
    if "req" not in obj:
        obj["req"] = {}

    # Temporary solution, this isn't completely safe for production use
    p = Path(__file__).parents[1]
    voucher_code = request["code"].upper().strip()
    voucher_file = os.path.join(p, "data", "voucher_codes.json.def")
    
    try:
        with open(voucher_file, "r", encoding="utf-8") as f:
            voucher_data = json.loads(f.read())

    except:
        obj["req"][request["req:"]] = {"error": "zoo.error.coupon.invalid"}
        return
    
    # Finds the voucher itself
    voucher = None
    voucher_index = -1
    for k, v in enumerate(voucher_data["vouchers"]):
        if v["code"].upper() == voucher_code:
            voucher = v
            voucher_index = k
            break
    
    # Check for invalid code
    if not voucher or not voucher["active"]:
        obj["req"][request["req:"]] = {"error": "zoo.error.coupon.invalid"}
        return

    # Check expiration date
    if voucher.get("expires", -1) != -1 and int(time.time()) > voucher["expires"]:
        obj["req"][request["req:"]] = {"error": "zoo.error.coupon.invalid"}
        return

    # Check if the voucher hasn't reached its usage limit
    max_uses = voucher.get("max_uses", -1)
    if max_uses != -1 and voucher.get("current_uses", 0) >= max_uses:
        obj["req"][request["req:"]] = {"error": "zoo.error.coupon.invalid"}
        return

    # Initialize user's redeemed vouchers list if it doesn't exist
    if "redeemed_vouchers" not in json_data:
        json_data["redeemed_vouchers"] = []
    
    # Check if user has already redeemed this voucher
    if voucher_code in json_data["redeemed_vouchers"]:
        obj["req"][request["req:"]] = {"error": "zoo.error.coupon.participated"}
        return

    # All checks passed, give rewards
    rewards = voucher["rewards"]

    if "virtual_currency" in rewards and rewards["virtual_currency"] > 0:
        json_data["uObj"]["uCv"] += rewards["virtual_currency"]

    if "real_currency" in rewards and rewards["real_currency"] > 0:
        json_data["uObj"]["uCr"] += rewards["real_currency"]

    if "xp" in rewards and rewards["xp"] > 0:
        json_data["uObj"]["uEp"] += rewards["xp"]
        json_data["uObj"]["uLvl"] = userUtils.calculate_level_based_on_xp(json_data["uObj"]["uEp"], config_data)

    # To-do: other rewards

    obj["req"][request["req:"]] = {"success": "zoo.success.coupon.redeemed"}
    json_data["redeemed_vouchers"].append(voucher_code)