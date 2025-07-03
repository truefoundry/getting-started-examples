# Deploy Whisper Model with Litserve

---

> [!tip]
> This example is deployed live [here](https://platform.live-demo.truefoundry.cloud/deployments/cmblzymv1ft4g01rj52b2cjkc?tab=pods)

###  Install requirements

```bash
pip install -r requirements.txt
```

### Start the server

```bash
export MODEL_DIR="Systran/faster-whisper-tiny"
python whisper_server.py
```

### Example inference call

```bash
curl -X POST http://0.0.0.0:8000/predict -F "request=@./audio.mp3"
```

You should get the following response:

```json
[{"start":0.0,"end":5.0,"text":" Oh, you think darkness is your ally."},{"start":5.0,"end":8.0,"text":" Are you merely adopted the dark?"},{"start":8.0,"end":11.0,"text":" I was born in it."},{"start":11.0,"end":14.0,"text":" More lit by it."},{"start":14.0,"end":17.0,"text":" I didn't see the light until I was already a man,"},{"start":17.0,"end":20.0,"text":" but then it was nothing to me but brightened."}]
```
