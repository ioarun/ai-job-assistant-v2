from fastapi import FastAPI
from langfuse import get_client
from langfuse.openai import openai  # drop-in: same OpenAI API, auto-traced

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/hello")
def hello():
    response = openai.chat.completions.create(
        model="gpt-4o-mini",   # placeholder — pin the real model before Phase B
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        name="hello-phase-a",  # labels the trace in Langfuse
    )
    get_client().flush()       # force-send the trace before returning (demo-only)
    return {"message": response.choices[0].message.content}
