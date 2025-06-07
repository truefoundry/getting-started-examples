# Deploy Whisper Model with Litserve

## Setup

```bash
pip install -r requirements.txt
```

## Deploy

```bash
python deploy.py --workspace-fqn ... --host ... --port ...
```

## Test

```bash
curl -X POST http://<endpoint>/predict -F "request=@./audio.mp3"
```

You should get the following response:

```json
[{"start":0.0,"end":5.0,"text":" Oh, you think darkness is your ally."},{"start":5.0,"end":8.0,"text":" Are you merely adopted the dark?"},{"start":8.0,"end":11.0,"text":" I was born in it."},{"start":11.0,"end":14.0,"text":" More lit by it."},{"start":14.0,"end":17.0,"text":" I didn't see the light until I was already a man,"},{"start":17.0,"end":20.0,"text":" but then it was nothing to me but brightened."}]
```
