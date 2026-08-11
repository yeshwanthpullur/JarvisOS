"""Minimal bounded Telegram Bot API client; only the fixed HTTPS endpoint is allowed."""
from __future__ import annotations
import json, urllib.error, urllib.request

class TelegramClient:
    def __init__(self, token:str, *, timeout:float=10.0, opener=None):
        self._token=token; self.timeout=max(1.0,min(float(timeout),30.0)); self._opener=opener or urllib.request.build_opener()
    def _call(self, method:str, payload:dict[str,object]|None=None):
        if method not in {"getMe","getUpdates","sendMessage"}: raise ValueError("telegram_method_blocked")
        url=f"https://api.telegram.org/bot{self._token}/{method}"
        body=None if payload is None else json.dumps(payload).encode("utf-8")
        request=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"},method="GET" if body is None else "POST")
        with self._opener.open(request,timeout=self.timeout) as response:
            data=json.loads(response.read(262144).decode("utf-8"))
        if not data.get("ok"): raise RuntimeError("telegram_provider_error")
        return data.get("result")
    def identity(self): return self._call("getMe")
    def updates(self,offset:int,limit:int,timeout:int): return self._call("getUpdates",{"offset":offset,"limit":limit,"timeout":timeout,"allowed_updates":["message"]})
    def send_text(self,chat_id:str,text:str): return self._call("sendMessage",{"chat_id":chat_id,"text":text,"disable_web_page_preview":True})

