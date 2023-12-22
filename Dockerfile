FROM python:3.11.5
MAINTAINER cone

LABEL project="cone-writing-server"
USER root

ENV PROJECT_DIR /app/cone-writing-server/

WORKDIR $PROJECT_DIR
copy ./cone_writing $PROJECT_DIR
copy ./requirements.txt $PROJECT_DIR
copy ./entrypoint.sh $PROJECT_DIR
# 不能使用copy ./* 这是COPY命令的一个bug， 会导致复制过去的路径混乱

RUN pip config --global set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -r requirements.txt

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
