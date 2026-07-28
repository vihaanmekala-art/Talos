"""
AI and calculation utilities.
"""

import requests
import sympy as sp
import streamlit as st


def groq(question: str, api_key: str) -> str:
    if not api_key:
        return "Error: API Key not provided."

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": question}],
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        data = response.json()
        if response.status_code == 200:
            return data["choices"][0]["message"]["content"]
        return f"API Error {response.status_code}: {data.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        return f"Request failed: {e}"


@st.cache_data(ttl=3600)
def calculate(question: str) -> str:
    question = question.lower().strip()
    question = question.replace("sin(", "sin_rad(")
    question = question.replace("cos(", "cos_rad(")
    question = question.replace("tan(", "tan_rad(")

    def sin_rad(x):
        return sp.sin(sp.pi / 180 * x)

    def cos_rad(x):
        return sp.cos(sp.pi / 180 * x)

    def tan_rad(x):
        return sp.tan(sp.pi / 180 * x)

    locals_dict = {
        "sin_rad": sin_rad,
        "cos_rad": cos_rad,
        "tan_rad": tan_rad,
        "pi": sp.pi,
        "sqrt": sp.sqrt,
    }

    try:
        expression = sp.sympify(question, locals=locals_dict)
        decimal = expression.evalf(5)
        fraction = sp.nsimplify(decimal)
        return f"{fraction}  (~ {decimal:.3f})"
    except sp.SympifyError:
        return "The calculation failed."
    except Exception as e:
        return f"Something went wrong... {e}"
