# Talking to shopping copilot

This project demonstrates different approaches on how to implement an intelligent shopping copilot

## Deploy Infrastructure

```
echo "log into azure dev cli - only once"
azd auth login

echo "provisioning all the resources with the azure dev cli"
azd up

echo "get and set the value for AZURE_ENV_NAME"
source <(azd env get-values | grep AZURE_ENV_NAME)

echo "building and deploying the streamlit user interface"
bash ./azd-hooks/deploy.sh web-navigator $AZURE_ENV_NAME
```


## Starting up

```
conda create -n navigator python=3.12

conda activate navigator

python -m pip install -r requirements.txt   

python -m uvicorn  main:app --reload
```