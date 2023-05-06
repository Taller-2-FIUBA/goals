FROM python:3.11

WORKDIR /user/src/goals

COPY . .
RUN pip install pip --upgrade
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

WORKDIR /user/src/goals/goals

ENTRYPOINT [ "uvicorn", "main:app", "--port=80", "--reload" ]
