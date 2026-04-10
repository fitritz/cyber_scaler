from fastapi import FastAPI
from fastapi import HTTPException
from env.environment import CyberSOCEnv

app = FastAPI()

env = CyberSOCEnv()


@app.get("/")
def home():
    return {"message": "CyberSOC OpenEnv running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reset")
def reset(task: str = None, seed: int = None):
    try:
        state = env.reset(task_name=task, seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return state.dict()


@app.post("/step/{action}")
def step(action: int):
    try:
        state, reward, done, info = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "state": state.dict(),
        "reward": reward.value,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state():
    current_state = env.state()
    if current_state is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    return current_state.dict()