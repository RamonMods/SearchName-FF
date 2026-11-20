# -*- coding: utf-8 -*-
# --- Cliente do servidor de jogo do Free Fire: sessão, login e busca por nickname. --- #

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from typing import Dict, List, Optional

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# --- chaves fixas do cliente do jogo (as mesmas usadas pelo app oficial). --- #
AES_KEY = b"Yg&tc%DEuh6%Zc^8"
AES_IV = b"6oyZDr22E3ychjM%"
CLIENT_ID = "100067"
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

# --- versão do cliente: a Garena recusa ReleaseVersion antigo. --- #
RELEASE_VERSION = os.environ.get("FF_RELEASE_VERSION", "OB55")

# --- endpoints da Garena. --- #
MSDK_REGISTER = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest:register"
MSDK_GRANT = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest/token:grant"
MSDK_GRANT_ALT = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"

# --- hosts de login: a Garena troca esses domínios de tempos em tempos. --- #
LOGIN_HOSTS = [
    "loginbp.ggblueshark.com",
    "loginbp.ppmainecoonghj.com",
]

# --- host do servidor de jogo por região. --- #
CLIENT_HOSTS = {
    "BR": "client.us.freefiremobile.com",
    "US": "client.us.freefiremobile.com",
    "NA": "client.us.freefiremobile.com",
    "SAC": "client.us.freefiremobile.com",
    "IND": "client.ind.freefiremobile.com",
    "ME": "clientbp.ppmainecoonghj.com",
    "EU": "clientbp.ppmainecoonghj.com",
    "ID": "clientbp.ppmainecoonghj.com",
    "TH": "clientbp.ppmainecoonghj.com",
    "VN": "clientbp.ppmainecoonghj.com",
    "SG": "clientbp.ppmainecoonghj.com",
    "BD": "clientbp.ppmainecoonghj.com",
    "PK": "clientbp.ppmainecoonghj.com",
    "MY": "clientbp.ppmainecoonghj.com",
    "PH": "clientbp.ppmainecoonghj.com",
    "RU": "clientbp.ppmainecoonghj.com",
    "AFR": "clientbp.ppmainecoonghj.com",
    "CIS": "clientbp.ppmainecoonghj.com",
    "TW": "clientbp.ppmainecoonghj.com",
}

USER_AGENT_MSDK = "GarenaMSDK/4.0.39(SM-A325M ;Android 13;en;HK;)"
USER_AGENT_GRANT = "GarenaMSDK/4.0.19P10(I2404 ;Android 15;en;US;)"
USER_AGENT_LOGIN = "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
USER_AGENT_GAME = "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005D Build/PI)"

# --- blob fixo de identificação do cliente, exigido no MajorRegister. --- #
_FIELD_22 = bytes.fromhex(
    "4747524501010100620200001052aa0d669c6a368f08338060d2ee0690053af84a41edcd3558556ec10f24f4"
    "6c93ac64ca41a16732c46a2cb071246a79b8929032f9e1b6f4ef331bd53cabf29b09b97349a46e9863c0314e"
    "1a0d80819fef8aabf03876b3d037db354a7ccb5c1bce96411fb3753f6f50e44c69c4ed617fa30efb8ffc0517"
    "ff2f636739be1f304d999cfd6fd48bf69454199794c3dc88f55a4bdbd66534d5a061359cdfd1fb680cd37918"
    "df9fdb3cf7d80067b0a3506c90063cf62b2ccec11e23913a2fd7c4ef091331967bb518a5ad1e551146b90821"
    "be800883abadde39d6c80a5d798611466c748f075481806c5842ce45e6bd4e3368ec08fe2ec41ceb880cd862"
    "49eb71693f79f0bccf9e590c3fae12519fe08c7a1905d0927690109e0df28574bb14847225db1a59230e6662"
    "ed7730e15ff9a6c815cb41b420edeada735a4b03e181037c37c2c850257311df2f07b0a56e759372cbd0268e"
    "3f13a292ee4373e38ab5096e0342a5e0d7fec6da2bbc265d74baadd2b24ee4f74862f82c21d6694bac53f8ce"
    "80312a30068a6276a641c19b11d0305c6fe2f531ac7de578b29f543697f5c73663e6f23aa15277b6122dcd4d"
    "4171e38f9ac0b173f39c58416a16c5c1f4a35acd065ce78f449cf538a249339e763272d458e4ed86c976591a"
    "9c066b3a37111e44091eb6b5a795249f3e5145db022a6055f2cc675936391312f688f89627845df222a91156"
    "555225be36f9714a0ba50246d0f003bda3c9c1292ab73b4f79635ddd023218eda93a302d79e023404c143965"
    "44a930b98ed54771aca7fec10d095587685b473e81a9619764fad9256529dcd6e911f4f4629612287d4ee3ec"
    "5389f6ec4ec020b0e2aac017232a9197be9e46239ce690fe5d4872b2e98e651510c971667f3aca8b59f3e9d5"
    "0e43"
)

# --- keystream usado para ofuscar o open_id no MajorRegister. --- #
_XOR_KEYSTREAM = bytes(
    [0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37,
     0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30]
)

# --- tempo de vida da sessão em cache (segundos). --- #
SESSION_TTL = int(os.environ.get("FF_SESSION_TTL", "3600"))


class GarenaError(Exception):
    # --- erro de comunicação/recusa vindo da Garena. --- #
    pass


# --- protobuf: escrita --- #
def _varint(valor: int) -> bytes:
    saida = bytearray()
    while True:
        byte = valor & 0x7F
        valor >>= 7
        if valor:
            saida.append(byte | 0x80)
        else:
            saida.append(byte)
            return bytes(saida)


def _campo_int(numero: int, valor: int) -> bytes:
    return _varint((numero << 3) | 0) + _varint(int(valor))


def _campo_bytes(numero: int, valor: bytes) -> bytes:
    return _varint((numero << 3) | 2) + _varint(len(valor)) + valor


def _campo_str(numero: int, valor: str) -> bytes:
    return _campo_bytes(numero, valor.encode("utf-8"))


# --- protobuf: leitura --- #
def _ler_campos(buffer: bytes) -> List[tuple]:
    campos: List[tuple] = []
    i, total = 0, len(buffer)
    while i < total:
        chave = desloc = 0
        while True:
            byte = buffer[i]
            i += 1
            chave |= (byte & 0x7F) << desloc
            desloc += 7
            if not byte & 0x80:
                break
        numero, tipo = chave >> 3, chave & 7
        if tipo == 0:
            valor = desloc = 0
            while True:
                byte = buffer[i]
                i += 1
                valor |= (byte & 0x7F) << desloc
                desloc += 7
                if not byte & 0x80:
                    break
            campos.append((numero, tipo, valor))
        elif tipo == 2:
            tamanho = desloc = 0
            while True:
                byte = buffer[i]
                i += 1
                tamanho |= (byte & 0x7F) << desloc
                desloc += 7
                if not byte & 0x80:
                    break
            campos.append((numero, tipo, buffer[i:i + tamanho]))
            i += tamanho
        elif tipo == 5:
            i += 4
        elif tipo == 1:
            i += 8
        else:
            break
    return campos


def _criptografar(payload: bytes) -> bytes:
    # --- AES-128-CBC com PKCS7, a mesma cifra do cliente. --- #
    cifra = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cifra.encrypt(pad(payload, 16))


def _headers_login(extras: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
        "Accept-Encoding": "gzip",
        "X-GA-SV": str(int(time.time())),
        "Content-Type": "application/octet-stream",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASE_VERSION,
    }
    if extras:
        headers.update(extras)
    return headers


def _headers_jogo(jwt: str) -> Dict[str, str]:
    return {
        "User-Agent": USER_AGENT_GAME,
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer " + jwt,
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "X-GA-SV": str(int(time.time())),
        "ReleaseVersion": RELEASE_VERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue",
    }


# --- 1) cria uma conta guest nova (só usada se não houver conta configurada). --- #
def registrar_guest(sessao: requests.Session, timeout: int = 20) -> Dict[str, str]:
    senha = "".join(secrets.choice("0123456789abcdef") for _ in range(32))
    corpo = json.dumps({"app_id": int(CLIENT_ID), "client_type": 2, "password": senha, "source": 2})
    assinatura = hmac.new(CLIENT_SECRET.encode(), corpo.encode(), hashlib.sha256).hexdigest()
    resposta = sessao.post(
        MSDK_REGISTER,
        data=corpo,
        timeout=timeout,
        headers={
            "User-Agent": USER_AGENT_MSDK,
            "Authorization": "Signature " + assinatura,
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    if resposta.status_code != 200:
        raise GarenaError("Garena recusou o cadastro de sessão (HTTP %s)." % resposta.status_code)
    uid = (resposta.json().get("data") or {}).get("uid")
    if not uid:
        raise GarenaError("Garena não devolveu o UID da sessão.")
    return {"uid": str(uid), "password": senha}


# --- 2) troca uid/senha por access_token + open_id. --- #
def conceder_token(sessao: requests.Session, uid: str, senha: str, timeout: int = 20) -> Dict[str, str]:
    corpo = {
        "client_id": int(CLIENT_ID),
        "client_secret": CLIENT_SECRET,
        "client_type": 2,
        "device_id": "02-" + str(uid),
        "password": senha,
        "response_type": "token",
        "uid": int(uid),
    }
    for url in (MSDK_GRANT, MSDK_GRANT_ALT):
        try:
            resposta = sessao.post(
                url,
                json=corpo,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT_GRANT},
            )
        except requests.RequestException:
            continue
        if resposta.status_code != 200:
            continue
        dados = resposta.json().get("data") or {}
        if dados.get("access_token") and dados.get("open_id"):
            return {"access_token": dados["access_token"], "open_id": dados["open_id"]}

    raise GarenaError("Conta de consulta recusada pela Garena.")


# --- 3) cria a conta de jogo (uma vez por conta, na região do IP). --- #
def registrar_jogo(sessao: requests.Session, open_id: str, access_token: str, timeout: int = 20) -> bool:
    apelido = "SRCH" + secrets.token_hex(3).upper()
    ofuscado = bytes(
        ord(caractere) ^ _XOR_KEYSTREAM[i % len(_XOR_KEYSTREAM)]
        for i, caractere in enumerate(open_id)
    )
    payload = (
        _campo_str(1, apelido)
        + _campo_str(2, access_token)
        + _campo_str(3, open_id)
        + _campo_int(5, 102000007)
        + _campo_int(6, 4)
        + _campo_int(7, 1)
        + _campo_int(13, 1)
        + _campo_bytes(14, ofuscado)
        + _campo_str(15, "bn")
        + _campo_int(16, 1)
        + _campo_int(17, 1)
        + _campo_bytes(22, _FIELD_22)
    )
    for host in LOGIN_HOSTS:
        try:
            resposta = sessao.post(
                "https://%s/MajorRegister" % host,
                data=_criptografar(payload),
                timeout=timeout,
                verify=False,
                headers=_headers_login({"Authorization": "Bearer"}),
            )
        except requests.RequestException:
            continue
        if resposta.status_code == 200 or b"ACCOUNT_EXIST" in resposta.content:
            return True
    return False


# --- 4) troca o token da Garena pelo JWT do servidor de jogo. --- #
def _device_id(uid: str) -> str:
    resumo = hashlib.md5(("ff-device-%s" % uid).encode()).hexdigest()
    return "Google|%s-%s-%s-%s-%s" % (
        resumo[0:8], resumo[8:12], resumo[12:16], resumo[16:20], resumo[20:32]
    )


def _payload_login(open_id: str, access_token: str, uid: str) -> bytes:
    # --- payload completo do cliente: é ele que devolve o cluster (campo 10). --- #
    agora = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = (
        _campo_str(3, agora)
        + _campo_str(4, "free fire")
        + _campo_int(5, 1)
        + _campo_str(7, "1.132.3")
        + _campo_str(8, "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)")
        + _campo_str(9, "Handheld")
        + _campo_str(10, "Verizon")
        + _campo_str(11, "WIFI")
        + _campo_int(12, 1920)
        + _campo_int(13, 1080)
        + _campo_str(14, "280")
        + _campo_str(15, "ARM64 FP ASIMD AES VMH | 2865 | 4")
        + _campo_int(16, 3003)
        + _campo_str(17, "Adreno (TM) 640")
        + _campo_str(18, "OpenGL ES 3.1 v1.46")
        + _campo_str(19, _device_id(uid or open_id))
        + _campo_str(20, "223.191.51.89")
        + _campo_str(21, "en")
        + _campo_str(22, open_id)
        + _campo_str(23, "4")
        + _campo_str(24, "Handheld")
        + _campo_bytes(25, _campo_int(6, 55) + _campo_int(8, 81))
        + _campo_str(29, access_token)
        + _campo_int(30, 1)
        + _campo_str(41, "Verizon")
        + _campo_str(42, "WIFI")
        + _campo_str(57, "7428b253defc164018c604a1ebbfebdf")
    )
    for numero, valor in (
        (60, 36235), (61, 31335), (62, 2519), (63, 703), (64, 25010),
        (65, 26628), (66, 32992), (67, 36235),
    ):
        payload += _campo_int(numero, valor)
    payload += (
        _campo_int(73, 3)
        + _campo_str(74, "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64")
        + _campo_int(76, 1)
        + _campo_str(77, "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk")
        + _campo_int(78, 3)
        + _campo_int(79, 2)
        + _campo_str(81, "64")
        + _campo_str(83, "2019118695")
        + _campo_str(86, "OpenGLES2")
        + _campo_int(87, 16383)
        + _campo_int(88, 4)
        + _campo_bytes(89, base64.b64decode("FwQVTgUPX1UaUllDDwcWCRBpWA0FUgsvA1snWlBaO1kFYg=="))
        + _campo_int(92, 13564)
        + _campo_str(93, "android")
        + _campo_str(94, "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY=")
        + _campo_int(95, 110009)
        + _campo_int(97, 1)
        + _campo_int(98, 1)
        + _campo_str(99, "4")
        + _campo_str(100, "4")
    )
    return payload


def _ler_login(buffer: bytes) -> Dict[str, str]:
    # --- a resposta pode vir com um prefixo de 64 bytes; tenta os dois offsets. --- #
    dados: Dict[str, str] = {}
    for blob in (buffer, buffer[64:] if len(buffer) > 64 else b""):
        if not blob:
            continue
        try:
            for numero, tipo, valor in _ler_campos(blob):
                if numero == 1 and tipo == 0:
                    dados["account_id"] = str(valor)
                elif numero == 2 and tipo == 2:
                    dados["region"] = valor.decode("utf-8", "ignore").strip()
                elif numero == 8 and tipo == 2:
                    dados["token"] = valor.decode("utf-8", "ignore").strip()
                elif numero == 10 and tipo == 2:
                    dados["server_url"] = valor.decode("utf-8", "ignore").strip().rstrip("/")
        except Exception:
            continue
        if dados.get("token"):
            return dados
    return dados


def major_login(
    sessao: requests.Session,
    open_id: str,
    access_token: str,
    uid: str = "",
    timeout: int = 25,
) -> Dict[str, str]:
    corpos = [
        _criptografar(_payload_login(open_id, access_token, uid)),
        _criptografar(_campo_str(22, open_id) + _campo_str(23, "4") + _campo_str(29, access_token) + _campo_str(99, "4")),
    ]
    ultimo_erro = "sem resposta"
    for host in LOGIN_HOSTS:
        for corpo in corpos:
            try:
                resposta = sessao.post(
                    "https://%s/MajorLogin" % host,
                    data=corpo,
                    timeout=timeout,
                    verify=False,
                    headers=_headers_login({"Authorization": "Bearer"}),
                )
            except requests.RequestException as exc:
                ultimo_erro = str(exc)[:120]
                continue

            if resposta.status_code != 200:
                ultimo_erro = "HTTP %s" % resposta.status_code
                continue

            dados = _ler_login(resposta.content)
            if not dados.get("token"):
                achado = re.search(rb"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", resposta.content)
                if achado:
                    dados["token"] = achado.group(0).decode("ascii")
            if dados.get("token"):
                return dados
            ultimo_erro = "resposta sem token"

    raise GarenaError("Login no servidor de jogo falhou (%s)." % ultimo_erro)


# --- 5) busca por nickname no servidor de jogo. --- #
def _host_da_busca(server_url: Optional[str], regiao: str) -> str:
    # --- o JWT só vale no cluster que o MajorLogin devolveu (campo 10). --- #
    if server_url:
        return re.sub(r"^https?://", "", server_url).rstrip("/")
    host = CLIENT_HOSTS.get(regiao.upper())
    if not host:
        raise GarenaError("Região '%s' não é suportada." % regiao)
    return host


def buscar_nickname(
    sessao: requests.Session,
    jwt: str,
    regiao: str,
    apelido: str,
    server_url: Optional[str] = None,
    timeout: int = 25,
) -> List[Dict[str, object]]:
    host = _host_da_busca(server_url, regiao)

    corpo = _criptografar(_campo_str(1, apelido))
    resposta = sessao.post(
        "https://%s/FuzzySearchAccountByName" % host,
        data=corpo,
        timeout=timeout,
        verify=False,
        headers=_headers_jogo(jwt),
    )

    if resposta.status_code == 401:
        raise GarenaError("A Garena recusou a busca (401).")
    if resposta.status_code != 200:
        raise GarenaError("Busca recusada pela Garena (HTTP %s)." % resposta.status_code)
    if not resposta.content:
        return []

    resultados: List[Dict[str, object]] = []
    for numero, tipo, valor in _ler_campos(resposta.content):
        if numero != 1 or tipo != 2:
            continue
        conta: Dict[str, object] = {}
        for sub_numero, sub_tipo, sub_valor in _ler_campos(valor):
            if sub_tipo == 0 and sub_numero == 1:
                conta["uid"] = str(sub_valor)
            elif sub_tipo == 2 and sub_numero == 3:
                conta["nickname"] = sub_valor.decode("utf-8", "ignore")
            elif sub_tipo == 2 and sub_numero == 5:
                conta["region"] = sub_valor.decode("utf-8", "ignore")
            elif sub_tipo == 0 and sub_numero == 6:
                conta["level"] = sub_valor
            elif sub_tipo == 0 and sub_numero == 21:
                conta["likes"] = sub_valor
        if conta.get("uid"):
            conta["nickname"] = re.sub(r"\s+", " ", str(conta.get("nickname", ""))).strip()
            resultados.append(conta)
    return resultados


# --- sessões em cache, uma por região. --- #
_sessoes: Dict[str, Dict[str, object]] = {}
_trava = threading.Lock()


def _conta_configurada(regiao: str) -> Optional[Dict[str, str]]:
    # --- contas opcionais via ambiente: FF_ACCOUNT_BR="uid:senha". --- #
    bruto = os.environ.get("FF_ACCOUNT_%s" % regiao.upper(), "").strip()
    if ":" not in bruto:
        return None
    uid, senha = bruto.split(":", 1)
    return {"uid": uid.strip(), "password": senha.strip()}


def _criar_sessao(regiao: str) -> Dict[str, object]:
    sessao = requests.Session()
    sessao.verify = False

    conta = _conta_configurada(regiao)
    if not conta:
        conta = registrar_guest(sessao)

    dados = conceder_token(sessao, conta["uid"], conta["password"])
    try:
        login = major_login(sessao, dados["open_id"], dados["access_token"], conta["uid"])
    except GarenaError:
        # --- conta guest ainda sem conta de jogo: cria uma e tenta de novo. --- #
        if not registrar_jogo(sessao, dados["open_id"], dados["access_token"]):
            raise
        time.sleep(2)
        login = major_login(sessao, dados["open_id"], dados["access_token"], conta["uid"])

    return {
        "sessao": sessao,
        "token": login["token"],
        "server_url": login.get("server_url", ""),
        "conta": conta,
        "criada_em": time.time(),
        "regiao": login.get("region", ""),
    }


def _sessao_valida(regiao: str) -> Dict[str, object]:
    regiao = regiao.upper()
    with _trava:
        atual = _sessoes.get(regiao)
        if atual and time.time() - float(atual["criada_em"]) < SESSION_TTL:
            return atual
    criada = _criar_sessao(regiao)
    with _trava:
        _sessoes[regiao] = criada
    return criada


def _invalidar(regiao: str) -> None:
    with _trava:
        _sessoes.pop(regiao.upper(), None)


def search_by_nickname(apelido: str, regiao: str = "BR") -> Dict[str, object]:
    # --- busca pública: monta/reaproveita a sessão e devolve a lista limpa. --- #
    apelido = (apelido or "").strip()
    regiao = (regiao or "BR").strip().upper()

    if len(apelido) < 3:
        raise GarenaError("Digite pelo menos 3 caracteres do nickname.")
    if len(apelido) > 32:
        raise GarenaError("Nickname muito longo: use até 32 caracteres.")

    inicio = time.time()
    dados = _sessao_valida(regiao)
    try:
        resultados = buscar_nickname(
            dados["sessao"],
            str(dados["token"]),
            regiao,
            apelido,
            str(dados.get("server_url") or ""),
        )
    except GarenaError:
        _invalidar(regiao)
        raise

    return {
        "query": apelido,
        "region": regiao,
        "total": len(resultados),
        "elapsed_ms": int((time.time() - inicio) * 1000),
        "results": resultados,
    }
