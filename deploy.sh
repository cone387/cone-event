#/bin/bash
set -e

OPTIONS_SHORT="p:s:"
OPTIONS_LONG="port:,setting:,gunicorn,help"

DEPLOY_TO="server";
PROJECT="cone-writing-server";
PORT=8005;
SETTING='';
SET_USER='';
SET_PASSWORD='';
INIT="false";

if ! ARGS=$(getopt -o $OPTIONS_SHORT --long $OPTIONS_LONG -n "$0" -- "$@"); then
  echo "Terminating..."
  echo -e "Usage: ./$SCRIPT_NAME [options]\n"
  exit 1
fi

eval set -- "${ARGS}"

while true;
do
    case $1 in
        -t|--to)
          echo "DEPLOY_TO: $2;"
          DEPLOY_TO=$2;
          shift 2
          ;;
        -p|--port)
          echo "PORT: $2;"
          PORT=$2;
          shift 2
          ;;
        -s|--setting)
          echo "setting.py: $2;"
          SETTING=$2;
          shift 2
          ;;
        -u|--user)
          echo "SET_USER: $2;"
          SET_USER=$2;
          shift 2
          ;;
        --pwd)
          echo "SET_PASSWORD: $2;"
          SET_PASSWORD=$2;
          shift 2
          ;;
        -i|--init)
          echo "INIT: true;"
          INIT="true";
          shift
          ;;
        --gunicorn)
          echo "USE_GUNICORN: true;"
          USE_GUNICORN="true";
          shift
          ;;
        --)
          break
          ;;
        ?)
          echo "there is unrecognized parameter."
          exit 1
          ;;
    esac
done


if [ "$SETTING" != "" ];
then
  if [ ! -f "$SETTING" ];
  then
    echo "SETTING<$SETTING> does not exist"
    exit 1
  fi
  server_path="/etc/cone-writing/";
  if [ "$context" != "default" -a "$context" != "" ];
  then
    # docker context 为其它服务器, 先将配置文件拷贝到服务器上
    server=$(docker context inspect | grep -o 'Host.*' | sed 's/.*: "ssh:\/\/\(.*\)".*/\1/')
    echo "server is $server"
    if [ "$server" = "" ];
    then
      exit 1
    fi
    ssh server "mkdir -p $server_path"
    scp $SETTING $server:$server_path;
  else
    # docker context 为本地, 直接将配置文件拷贝到本地server_path
    echo "mkdir -p $server_path"
    mkdir -p $server_path
#    echo "cp -f $SETTING $server_path"
#    cp -f $SETTING $server_path
  fi
  VOLUME="-v $server_path:/app/cone-writing-server/configs"
  ENV="-e DJANGO_SETTINGS_MODULE=configs.$(basename $SETTING .py)";
fi


if [ "$USE_GUNICORN" == "true" ]
then
  GUNICORN_ENV="-e USE_GUNICORN=$USE_GUNICORN"
else
  GUNICORN_ENV=""
fi
echo "Deploying $PROJECT..."
cid=`docker ps -a | grep $PROJECT | awk '{print $1}'`
for c in $cid
  do
      docker stop $c
      docker rm $c
  done
#echo "docker build -t $PROJECT ."
#docker build -t $PROJECT .

echo "docker run -d $VOLUME  $GUNICORN_ENV $ENV -p $PORT:8000 --log-opt max-size=100m --name $PROJECT $PROJECT"
docker run -d $VOLUME  $GUNICORN_ENV $ENV -p $PORT:8000 --log-opt max-size=100m --name $PROJECT $PROJECT

echo "Done."