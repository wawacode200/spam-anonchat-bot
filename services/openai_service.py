import base64
import json
from typing import Any, cast

from openai import OpenAI
from config import settings


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    def image_to_base64(
        self,
        image_bytes: bytes,
    ) -> str:
        return base64.b64encode(
            image_bytes
        ).decode()

    def recognize_emoji_captcha(
        self,
        image_bytes: bytes,
        button_emojis: list[str],
    ) -> list[str]:
        image_b64 = self.image_to_base64(
            image_bytes
        )

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={
                "type": "json_object"
            },
            messages=cast(Any, [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "На изображении сверху 3 объекта в emoji-стиле. "
                                "Нужно выбрать подходящие emoji только из списка вариантов. "
                                f"Варианты emoji-кнопок: {button_emojis}. "
                                "Нельзя придумывать emoji вне списка. "
                                "Верни 3 emoji из списка, максимально похожие на объекты сверху. "
                                "Порядок — слева направо. "
                                'Ответ строго JSON: {"emojis":["...","...","..."]}'
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:image/png;base64,{image_b64}"
                                )
                            },
                        },
                    ],
                }
            ]),
        )

        content = response.choices[0].message.content

        if not content:
            return []

        data = json.loads(content)

        emojis = data.get("emojis", [])

        return [
            emoji for emoji in emojis
            if emoji in button_emojis
        ]


openai_service = OpenAIService()