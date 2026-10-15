"""Telegram Bot API, single-chat encrypted-at-rest token managed by Windows DPAPI.

Never accepts remote commands; Telegram is outbound notifications only.
Never logs the bot token, request URL, or response bodies on exceptions.
This notifier does NOT imply broker orders have occurred.
"""
from __future__ import annotations
import json
import os
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class TelegramHalt(RuntimeError):
    pass


class TelegramBot:
    def __init__(self, token:str, chat_id:str, *, opener=urlopen):
        if not isinstance(token,str) or not re.fullmatch(r"[0-9]{5,15}:[A-Za-z0-9_-]{30,}",token):
            raise TelegramHalt("INVALID_BOT_TOKEN_FORMAT")
        if not isinstance(chat_id,str) or not re.fullmatch(r"-?[0-9]{4,20}",chat_id):
            raise TelegramHalt("INVALID_CHAT_ID_FORMAT")
        self.__token=token
        self.chat_id=chat_id
        self.opener=opener

    def send(self, text:str):
        if not isinstance(text,str) or not text or len(text)>3500:
            raise TelegramHalt("INVALID_MESSAGE_LENGTH")
        url="https://api.telegram.org/bot"+self.__token+"/sendMessage"
        p=urlparse(url)
        if p.scheme!="https" or p.hostname!="api.telegram.org":
            raise TelegramHalt("TELEGRAM_HOST_REJECTED")
        data=json.dumps({"chat_id":self.chat_id,"text":text,
                         "disable_web_page_preview":True},
                        ensure_ascii=False).encode("utf-8")
        req=Request(url,data=data,method="POST",
                    headers={"Content-Type":"application/json",
                             "User-Agent":"CryptoLab-V07-Notifications"})
        try:
            with self.opener(req,timeout=10) as response:
                if getattr(response,"status",200)!=200:
                    raise TelegramHalt("TELEGRAM_HTTP_NOT_200")
                # Do not accept redirects to unknown hosts.
                target=response.geturl() if hasattr(response,"geturl") else url
                if urlparse(target).hostname!="api.telegram.org":
                    raise TelegramHalt("TELEGRAM_REDIRECT_FORBIDDEN")
                body=response.read(250_000)
        except Exception:
            # URL could embed token; hide exception and all HTTP response.
            raise TelegramHalt("TELEGRAM_DELIVERY_UNVERIFIED") from None
        try:
            result=json.loads(body)
        except (TypeError,ValueError,UnicodeDecodeError):
            raise TelegramHalt("TELEGRAM_NON_JSON_RESPONSE")
        if (not isinstance(result,dict) or result.get("ok") is not True or
            not isinstance(result.get("result"),dict) or
            not isinstance(result["result"].get("message_id"),int)):
            raise TelegramHalt("TELEGRAM_API_NOT_ACKNOWLEDGED")
        return result["result"]["message_id"]


def message_for(event:dict):
    """Hard separation of signal, authenticated account read and actual fill."""
    if not isinstance(event,dict):raise TelegramHalt("INVALID_EVENT")
    kind=event.get("kind")
    if kind=="V5_SIGNAL_NOT_ORDER":
        if event.get("lane") not in ("SOL_CONVEX_NATIVE_5M",
                                    "SOL_CONVEX_1H","BNB_CONVEX_4H"):
            raise TelegramHalt("INVALID_LANE")
        return ("🎣 CONVEX V5 | SINAL DETETADO (NÃO É ORDEM)\n"
                f"Estratégia: {event['lane']}\n"
                f"Mercado: {event['symbol']} | LONG potencial\n"
                f"Fecho UTC: {event['close_utc']}\n"
                f"Signal ID: {event['signal_id']}\n"
                "Execução MEXC: NÃO CONFIRMADA\n"
                "STOP MEXC: NÃO CONFIRMADO\n"
                "Autoridade de trading: NENHUMA")
    if kind=="MEXC_ACCOUNT_FLAT_READ":
        return ("✅ MEXC | LEITURA AUTENTICADA\n"
                f"UTC: {event['checked_at_utc']}\n"
                "Posições: 0 | Ordens: 0 | Stops: 0\n"
                "Nenhuma operação executada por este monitor.")
    if kind=="MEXC_PROTECTION_UNVERIFIED":
        return ("🚨 MEXC | PROTEÇÃO NÃO COMPROVADA\n"
                f"UTC: {event['checked_at_utc']}\n"
                f"Posições: {event['positions']} | Ordens: {event['orders']} | Stops: {event['stops']}\n"
                "VERIFICAR POSIÇÕES E STOP NATIVO DIRETAMENTE NA MEXC.\n"
                "O monitor NÃO está autorizado a alterar ou fechar ordens.")
    if kind=="MEXC_SOURCE_BLOCKED":
        return ("⚠️ CRYPTO LAB | FONTE/BROKER BLOQUEADO\n"
                f"UTC: {event['checked_at_utc']}\n"
                f"Erro: {event['reason']}\n"
                "Sem confirmação de posições ou sinais; consultar MEXC.")
    if kind=="SYSTEM_ONLINE":
        return ("🤖 CRYPTO LAB V07 | ALERTAS LIGADOS\n"
                "3 CONVEX monitorizadas em modo leitura.\n"
                "Ordens reais DESATIVADAS; alertas ≠ trades.")
    raise TelegramHalt("EVENT_NOT_ALLOWLISTED")
