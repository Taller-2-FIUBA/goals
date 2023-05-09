FROM python:3.11

WORKDIR /user/src/goals

COPY . .
RUN pip install pip --upgrade
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

WORKDIR /user/src/goals

CMD ["uvicorn", "goals.main:app", "--host", "0.0.0.0", "--port", "8004"]
