# Combined source bundle


# ==== SOURCE: eat ====
# app.py
import os
import requests
from flask import Flask, request, jsonify
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Target API URL – can be overridden by environment variable
TARGET_API_URL = os.environ.get("TARGET_API_URL", "https://api-otrss.garena.com/support/callback/")

@app.route('/access', methods=['GET'])
def rizer():
    # Get the eat_token from query parameters
    eat_token = request.args.get('eat_token')
    if not eat_token:
        return "Missing eat_token parameter", 400

    # Forward relevant headers (filter out problematic ones)
    headers_to_forward = {}
    for header, value in request.headers.items():
        # Skip headers that might cause issues
        if header.lower() in ['host', 'content-length', 'connection', 'transfer-encoding']:
            continue
        headers_to_forward[header] = value

    # Make the request to the target API
    try:
        # We want to follow redirects and capture the final URL
        session = requests.Session()
        # Disable automatic redirect handling so we can inspect each step
        response = session.get(TARGET_API_URL, params={'access_token': eat_token},
                               headers=headers_to_forward, allow_redirects=False)
        
        # Follow redirects manually
        while response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get('Location')
            if not location:
                break
            # Handle relative vs absolute URLs
            if not location.startswith(('http://', 'https://')):
                # Build absolute URL from base
                base = urlparse(TARGET_API_URL)
                location = base._replace(path=location).geturl()
            response = session.get(location, headers=headers_to_forward, allow_redirects=False)

        final_url = response.url

        # Extract access_token from final URL query parameters
        parsed = urlparse(final_url)
        query_params = parse_qs(parsed.query)
        access_token = query_params.get('access_token', [None])[0]

        if not access_token:
            # Fallback: try to find in response body? (not described, but just in case)
            # Here we could parse response.text but we'll just return an error.
            return "Access token not found in final URL", 500

        # Build the response text
        response_text = f"""
access token= {access_token}"""
        return response_text, 200, {'Content-Type': 'text/plain'}

    except Exception as e:
        # Log the error (you may want to use proper logging)
        print(f"Error: {e}")
        return f"Internal server error: {str(e)}", 500

# For local development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    #MADE BY RIZER..
    # CREDIT CHORO KI MAA KI CHUT

# ==== SOURCE: guest ====
from flask import Flask, request, jsonify
import requests
import urllib3
import base64
import json
from Crypto.Cipher import AES
from datetime import datetime
from google.protobuf.json_format import MessageToDict
from proto import FreeFire_pb2
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
app.json.sort_keys = False

http_session = requests.Session()

AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
FF_NICKNAME_KEY = b"1e5898ccb8dfdd921f9bdea848768b64a201"

def pad(text: bytes) -> bytes:
    padding_length = 16 - (len(text) % 16)
    return text + bytes([padding_length] * padding_length)

def encrypt(plaintext: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(plaintext))

def format_ttl(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours} hours, {minutes} mins, {secs} secs"

def decode_ff_nickname(encoded: str) -> str:
    try:
        raw = base64.b64decode(encoded)
        dec = bytearray()
        for i, b in enumerate(raw):
            dec.append(b ^ FF_NICKNAME_KEY[i % len(FF_NICKNAME_KEY)])
        return dec.decode('utf-8', errors='replace')
    except Exception:
        return "Unknown"

def extract_nickname_from_jwt(token: str) -> str:
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1]
            payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
            if 'nickname' in payload and isinstance(payload['nickname'], str):
                return decode_ff_nickname(payload['nickname'])
    except Exception:
        pass
    return "Unknown"

def convert_timestamps_to_human(data):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (int, float)) and 1000000000 < v < 3000000000:
                try:
                    human_time = datetime.utcfromtimestamp(v).strftime('%Y-%m-%d %H:%M:%S UTC')
                    data[k] = f"{v} ({human_time})"
                except: pass
            elif isinstance(v, (dict, list)):
                convert_timestamps_to_human(v)
    elif isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], (int, float)) and 1000000000 < data[i] < 3000000000:
                try:
                    human_time = datetime.utcfromtimestamp(data[i]).strftime('%Y-%m-%d %H:%M:%S UTC')
                    data[i] = f"{data[i]} ({human_time})"
                except: pass
            elif isinstance(data[i], (dict, list)):
                convert_timestamps_to_human(data[i])
    return data

@app.route('/guest', methods=['GET'])
def guest_login():
    uid = request.args.get('uid')
    pw = request.args.get('pw')

    if not uid or not pw:
        return jsonify({
            "status": "error", 
            "message": "Missing parameters. Use /guest?uid=xxx&pw=xxx"
        }), 400

    oauth_url = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    payload = {
        "client_id": 100067, 
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_type": 2, 
        "password": pw, 
        "response_type": "token", 
        "uid": int(uid)
    }

    response_payload = {
        "creator": "Crownx64Alone",
        "status": "success",
        "Guest_Auth": None,
        "MajorLogin": None
    }

    try:
        r = http_session.post(oauth_url, json=payload, timeout=8)
        auth_data = r.json()
        response_payload["Guest_Auth"] = convert_timestamps_to_human(auth_data)

        inner = auth_data.get("data", {})
        acc_token = inner.get("access_token")
        open_id = inner.get("open_id")

        if not acc_token or not open_id:
            return jsonify({
                "status": "error",
                "message": "Auth tokens not found in Step 1",
                "Guest_Auth": response_payload["Guest_Auth"]
            }), 401

        req_msg = FreeFire_pb2.LoginReq()
        req_msg.open_id = open_id
        req_msg.open_id_type = "4"
        req_msg.login_token = acc_token
        req_msg.orign_platform_type = "4"

        enc_data = encrypt(req_msg.SerializeToString())
        headers = {
            "X-GA": "v1 1", 
            "ReleaseVersion": "OB53", 
            "Content-Type": "application/octet-stream", 
            "User-Agent": USERAGENT
        }

        resp = http_session.post("https://loginbp.ggpolarbear.com/MajorLogin", data=enc_data, headers=headers, verify=False, timeout=8)

        if resp.status_code == 200:
            res_msg = FreeFire_pb2.LoginRes()
            res_msg.ParseFromString(resp.content)
            major_dict = MessageToDict(res_msg, preserving_proto_field_name=True)
            
            if 'ttl' in major_dict:
                major_dict['ttl'] = format_ttl(int(major_dict['ttl']))

            nickname = "Unknown"
            if 'token' in major_dict:
                nickname = extract_nickname_from_jwt(major_dict['token'])

            ordered_major_dict = {}
            
            if 'account_id' in major_dict:
                ordered_major_dict['account_id'] = major_dict['account_id']
                
            ordered_major_dict['nickname'] = nickname
            
            for k, v in major_dict.items():
                if k != 'account_id':
                    ordered_major_dict[k] = v

            response_payload["MajorLogin"] = convert_timestamps_to_human(ordered_major_dict)
            
            return jsonify(response_payload), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"MajorLogin failed with status {resp.status_code}",
                "Guest_Auth": response_payload["Guest_Auth"]
            }), 502

    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# ==== SOURCE: jwt ====
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DON'T EDIT
#MADE BY RIZER
#TELEGRAM @beotherjkman
# IF YOU STEAL MY CREDIT THAN I WILL ANNOUNCE YOU AS AN COPY PASTER
import json
import requests
import sys
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13MajorLoginReq.proto\"\xfa\n\n\nMajorLogin\x12\x12\n\nevent_time\x18\x03 \x01(\t\x12\x11\n\tgame_name\x18\x04 \x01(\t\x12\x13\n\x0bplatform_id\x18\x05 \x01(\x05\x12\x16\n\x0e\x63lient_version\x18\x07 \x01(\t\x12\x17\n\x0fsystem_software\x18\x08 \x01(\t\x12\x17\n\x0fsystem_hardware\x18\t \x01(\t\x12\x18\n\x10telecom_operator\x18\n \x01(\t\x12\x14\n\x0cnetwork_type\x18\x0b \x01(\t\x12\x14\n\x0cscreen_width\x18\x0c \x01(\r\x12\x15\n\rscreen_height\x18\r \x01(\r\x12\x12\n\nscreen_dpi\x18\x0e \x01(\t\x12\x19\n\x11processor_details\x18\x0f \x01(\t\x12\x0e\n\x06memory\x18\x10 \x01(\r\x12\x14\n\x0cgpu_renderer\x18\x11 \x01(\t\x12\x13\n\x0bgpu_version\x18\x12 \x01(\t\x12\x18\n\x10unique_device_id\x18\x13 \x01(\t\x12\x11\n\tclient_ip\x18\x14 \x01(\t\x12\x10\n\x08language\x18\x15 \x01(\t\x12\x0f\n\x07open_id\x18\x16 \x01(\t\x12\x14\n\x0copen_id_type\x18\x17 \x01(\t\x12\x13\n\x0b\x64\x65vice_type\x18\x18 \x01(\t\x12\'\n\x10memory_available\x18\x19 \x01(\x0b\x32\r.GameSecurity\x12\x14\n\x0c\x61\x63\x63\x65ss_token\x18\x1d \x01(\t\x12\x17\n\x0fplatform_sdk_id\x18\x1e \x01(\x05\x12\x1a\n\x12network_operator_a\x18) \x01(\t\x12\x16\n\x0enetwork_type_a\x18* \x01(\t\x12\x1c\n\x14\x63lient_using_version\x18\x39 \x01(\t\x12\x1e\n\x16\x65xternal_storage_total\x18< \x01(\x05\x12\"\n\x1a\x65xternal_storage_available\x18= \x01(\x05\x12\x1e\n\x16internal_storage_total\x18> \x01(\x05\x12\"\n\x1ainternal_storage_available\x18? \x01(\x05\x12#\n\x1bgame_disk_storage_available\x18@ \x01(\x05\x12\x1f\n\x17game_disk_storage_total\x18\x41 \x01(\x05\x12%\n\x1d\x65xternal_sdcard_avail_storage\x18\x42 \x01(\x05\x12%\n\x1d\x65xternal_sdcard_total_storage\x18\x43 \x01(\x05\x12\x10\n\x08login_by\x18I \x01(\x05\x12\x14\n\x0clibrary_path\x18J \x01(\t\x12\x12\n\nreg_avatar\x18L \x01(\x05\x12\x15\n\rlibrary_token\x18M \x01(\t\x12\x14\n\x0c\x63hannel_type\x18N \x01(\x05\x12\x10\n\x08\x63pu_type\x18O \x01(\x05\x12\x18\n\x10\x63pu_architecture\x18Q \x01(\t\x12\x1b\n\x13\x63lient_version_code\x18S \x01(\t\x12\x14\n\x0cgraphics_api\x18V \x01(\t\x12\x1d\n\x15supported_astc_bitset\x18W \x01(\r\x12\x1a\n\x12login_open_id_type\x18X \x01(\x05\x12\x18\n\x10\x61nalytics_detail\x18Y \x01(\x0c\x12\x14\n\x0cloading_time\x18\\ \x01(\r\x12\x17\n\x0frelease_channel\x18] \x01(\t\x12\x12\n\nextra_info\x18^ \x01(\t\x12 \n\x18\x61ndroid_engine_init_flag\x18_ \x01(\r\x12\x0f\n\x07if_push\x18\x61 \x01(\x05\x12\x0e\n\x06is_vpn\x18\x62 \x01(\x05\x12\x1c\n\x14origin_platform_type\x18\x63 \x01(\t\x12\x1d\n\x15primary_platform_type\x18\x64 \x01(\t\"5\n\x0cGameSecurity\x12\x0f\n\x07version\x18\x06 \x01(\x05\x12\x14\n\x0chidden_value\x18\x08 \x01(\x04\x62\x06proto3')
RIZER = "1.123.14"
"TELEGRAM:@beotherjkman" == "Verizon"
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginReq_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_MAJORLOGIN']._serialized_start = 24
  _globals['_MAJORLOGIN']._serialized_end = 1426
  _globals['_GAMESECURITY']._serialized_start = 1428
  _globals['_GAMESECURITY']._serialized_end = 1481
MajorLogin = _globals['MajorLogin']
GameSecurity = _globals['GameSecurity']


DESCRIPTOR2 = _descriptor_pool.Default().AddSerializedFile(b'\n\x13MajorLoginRes.proto\"|\n\rMajorLoginRes\x12\x13\n\x0b\x61\x63\x63ount_uid\x18\x01 \x01(\x04\x12\x0e\n\x06region\x18\x02 \x01(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\x0b\n\x03url\x18\n \x01(\t\x12\x11\n\ttimestamp\x18\x15 \x01(\x03\x12\x0b\n\x03key\x18\x16 \x01(\x0c\x12\n\n\x02iv\x18\x17 \x01(\x0c\x62\x06proto3')
_globals2 = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR2, _globals2)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR2, 'MajorLoginRes_pb2', _globals2)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR2._loaded_options = None
  _globals2['_MAJORLOGINRES']._serialized_start = 23
  _globals2['_MAJORLOGINRES']._serialized_end = 147
MajorLoginRes = _globals2['MajorLoginRes']



app = Flask(__name__)


AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

def encrypt_aes(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def build_major_login(open_id: str, access_token: str, platform_type: int) -> bytes:
    major = MajorLogin()
    major.event_time = "2025-03-23 12:00:00"
    major.game_name = "free fire"
    major.platform_id = 1
    major.client_version = RIZER
    major.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major.system_hardware = "Handheld"
    major.telecom_operator = "TELEGRAM:@beotherjkman"
    major.network_type = "WIFI"
    major.screen_width = 1920
    major.screen_height = 1080
    major.screen_dpi = "280"
    major.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major.memory = 3003
    major.gpu_renderer = "Adreno (TM) 640"
    major.gpu_version = "OpenGL ES 3.1 v1.46"
    major.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major.client_ip = "223.191.51.89"
    major.language = "en"
    major.open_id = open_id
    major.open_id_type = "4"
    major.device_type = "Handheld"
    major.memory_available.version = 55
    major.memory_available.hidden_value = 81
    major.access_token = access_token
    major.platform_sdk_id = 1
    major.network_operator_a = "Verizon"
    major.network_type_a = "WIFI"
    major.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major.external_storage_total = 36235
    major.external_storage_available = 31335
    major.internal_storage_total = 2519
    major.internal_storage_available = 703
    major.game_disk_storage_available = 25010
    major.game_disk_storage_total = 26628
    major.external_sdcard_avail_storage = 32992
    major.external_sdcard_total_storage = 36235
    major.login_by = 3
    major.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major.reg_avatar = 1
    major.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major.channel_type = 3
    major.cpu_type = 2
    major.cpu_architecture = "64"
    major.client_version_code = "2019118695"
    major.graphics_api = "OpenGLES2"
    major.supported_astc_bitset = 16383
    major.login_open_id_type = 4
    major.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWA0FUgsvA1snWlBaO1kFYg=="
    major.loading_time = 13564
    major.release_channel = "android"
    major.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major.android_engine_init_flag = 110009
    major.if_push = 1
    major.is_vpn = 1
    major.origin_platform_type = str(platform_type)
    major.primary_platform_type = str(platform_type)
    return major.SerializeToString()

def try_major_login(open_id: str, access_token: str, platform_type: int):
    payload = build_major_login(open_id, access_token, platform_type)
    encrypted_payload = encrypt_aes(payload)

    url = "https://loginbp.ggblueshark.com/MajorLogin"
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53"
    }
    try:
        resp = requests.post(url, data=encrypted_payload, headers=headers, verify=False, timeout=10)
        if resp.status_code != 200:
            return None
        major_res = MajorLoginRes()
        major_res.ParseFromString(resp.content)
        if major_res.token:
            return {
                "account_uid": str(major_res.account_uid),
                "region": major_res.region,
                "token": major_res.token,
                "url": major_res.url,
                "timestamp": major_res.timestamp,
                "key": major_res.key.hex(),
                "iv": major_res.iv.hex()
            }
    except Exception as e:
        print(f"MajorLogin error for platform {platform_type}: {e}")
    return None

def decode_jwt(token: str) -> dict:
    import base64
    parts = token.split('.')
    if len(parts) != 3:
        return {}
    try:
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '==').decode())
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==').decode())
        return {"header": header, "payload": payload}
    except Exception:
        return {}

@app.route('/jwt', methods=['GET'])
def rizer_endpoint():
    access_token = request.args.get('access_token')
    if not access_token:
        return jsonify({"error": "Missing 'access_token' parameter"}), 400


    inspect_url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
    try:
        insp_resp = requests.get(inspect_url, timeout=10)
        if insp_resp.status_code != 200:
            return jsonify({"error": "Failed to inspect token", "status_code": insp_resp.status_code}), 400
        insp_data = insp_resp.json()
        open_id = insp_data.get('open_id')
        if not open_id:
            return jsonify({"error": "open_id not found in inspect response"}), 400
    except Exception as e:
        return jsonify({"error": f"Inspect request failed: {str(e)}"}), 500


    platform_types = [2, 3, 4, 6, 8]
    last_error = None
    for pt in platform_types:
        result = try_major_login(open_id, access_token, pt)
        if result:
            jwt_decoded = decode_jwt(result['token'])
            return jsonify({
                "success": True,
                "platform_type_used": pt,
                "jwt": result['token'],
                "jwt_decoded": jwt_decoded,
                "account_uid": result['account_uid'],
                "region": result['region'],
                "url": result['url'],
                "timestamp": result['timestamp']
            })
        else:
            last_error = f"Failed with platform_type {pt}"

    return jsonify({
        "success": False,
        "error": "MajorLogin failed. Account may be banned, not registered, or token invalid.",
        "detail": last_error
    }), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)