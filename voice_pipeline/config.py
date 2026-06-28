"""
内网语音流水线配置：ASR (SenseVoice) + TTS (Kokoro) + LLM (Qwen3 235B MoE)

认证方式：
  - ASR / TTS：SM4-CBC 加密生成 nonce/ts 参数 + Bearer Token
  - LLM：APP_ID / SECRET_KEY 请求头
"""
import binascii
import urllib.parse
import time
import logging

logger = logging.getLogger("voice-pipeline")

# ============================================
# SM4 加密工具（与内网 API 网关认证协议一致）
# ============================================
SM4_KEY = "u84u6=WJQLdYvxWQ"
SM4_IV = "uboqQ5e=zndseBgy"


def sm4_encrypt(plain_text: str, key: str = SM4_KEY, iv: str = SM4_IV) -> str:
    """SM4-CBC 加密 → Base64 编码"""
    from gmssl import sm4 as gm_sm4
    crypt = gm_sm4.CryptSM4()
    crypt.set_key(bytes(key, encoding="utf-8"), gm_sm4.SM4_ENCRYPT)
    ciphertext = crypt.crypt_cbc(
        bytes(iv, encoding="utf-8"),
        bytes(plain_text, encoding="utf-8"),
    )
    return binascii.b2a_base64(ciphertext).decode("utf-8")


def build_auth_params(app_id: str, auth_key: str, serving_id: str) -> dict:
    """生成 SM4 鉴权查询参数：nonce, ts"""
    ts_millis = str(int(time.time() * 1000))
    nonce = urllib.parse.quote(
        sm4_encrypt(auth_key + ts_millis + app_id)
    ).replace("%0A", "")
    ts_enc = urllib.parse.quote(sm4_encrypt(ts_millis))
    return {
        "appId": app_id,
        "nonce": nonce,
        "ts": ts_enc,
        "servingId": serving_id,
    }


def build_url(base_url: str, app_id: str, auth_key: str, serving_id: str) -> str:
    """构建带鉴权查询参数的完整 URL"""
    params = build_auth_params(app_id, auth_key, serving_id)
    return base_url + (
        "?appId={appId}&nonce={nonce}&ts={ts}&servingId={servingId}".format(**params)
    )


# ============================================
# ASR 配置（SenseVoice 语音识别）
# ============================================
ASR_CONFIG = {
    "base_url": "http://10.141.180.150:32080/fb0491972bb9482f94848b821e99d724/api/v1/sensevoice_asr",
    "app_id": "ab3be06701034ec4b9570bcef94ddb34",
    "auth_key": (
        "c741859c1f7be3994e87ef1fb463896cc8ac7865ab73e2ad10215623300b17be"
        "f0f9025a4de52a02d2556e15a46b1e9500deff9fd4839f3732483250dce6420e"
        "bc6f050669a8a9053165f064b7aaf861fe2497ad302af6967347671800da121b"
        "878fa1a902d85e9952abd98cbb91336b49d54a6b9a050785369a13e7b8a3841"
        "3a0f672bd15605e9cc2ced895ad2efa56"
    ),
    "serving_id": "254",
    "authorization": "Bearer sk_GrmiXyrgleZLaHFqtkwFBScoLarYMvFXXmjIp",
    "lang": "zh",  # 语言：auto / zh / en
}

# ============================================
# TTS 配置（Kokoro 语音合成）
# ============================================
TTS_CONFIG = {
    "base_url": "http://10.141.180.150:32080/0e0b634ce9574695b8002feaaae97ce7/v1/audio/speech",
    "app_id": "68e95ae3a218415a9b8be478f84fdbdc",
    "auth_key": (
        "da533ca50dfcfc2859397d7cb8712ff83209a2fd0c472c267e7d3ce571327d13"
        "3424a685305c8e19bc517f0d9ce161563888f65d38932e8ec05bff64eab97879"
        "c9e0c5722d481ef9ec936abe2fce512b2733559bd848dd4d0a9910c977a42cd5"
        "c4131e190ebbb2212e7c98edb056d1777c4abe2070b9598040695e12ace549db"
        "d479fc20f450446cb2a0a4bdc78387da"
    ),
    "serving_id": "253",
    "model": "kokoro",
    "voice": "zm_009",  # 中文男声
}

# ============================================
# LLM 配置（Qwen3 235B MoE）
# ============================================
LLM_CONFIG = {
    "base_url": "http://25.41.34.249:8008/api/ai/qwen/235b/moe",
    "app_id": "c2e00b8880af43e3a8533fa7fbaa13e5",
    "secret_key": "95f4ff21ec6fae53389beb99c9b2a9ac",
    "model": "qwen3-235b-moe",  # 模型标识（用于日志/记录）
    "system_prompt": "你是一个友好的中文语音助手，回答要简洁、口语化，适合用语音播报。",
}

# ============================================
# 可选：DashScope fallback（如需外网兜底，在 .env 中配置）
# ============================================
import os

_ENV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val
