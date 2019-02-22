FROM python:3.7
ADD  requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
ADD  . ./app
WORKDIR /app
EXPOSE 5000:5000
CMD python3 ./run.py