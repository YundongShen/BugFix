#! /bin/sh

### variable
docker login -u dokploy -p dXDYxbgY76XCvKpa 47.103.57.78:30002

TARGET=metagpt
PROJECT=dokploy
DOCKER_HOST=47.103.57.78:30002
DOCKER_USER=dokploy
DOCKER_PWD=dXDYxbgY76XCvKpa


## docker build
echo "*****[Info]***** docker build..."
docker build -f Dockerfile -t $TARGET:latest .
found_image_cout=$(docker images | grep $TARGET | wc -l)
if [[ $? -ne 0 ]] || [[ $found_image_cout -lt 1 ]]; then
    echo "*****[Error]***** docker build failed!"
    exit -1
else
    echo "*****[Info]***** docker build succeeded!"
fi


## docker login


docker login -p $DOCKER_PWD -u $DOCKER_USER $DOCKER_HOST

if [[ $? -ne 0 ]]; then
    echo "*****[Error]***** docker login failed!"
    exit -1
else
    echo "*****[Info]***** docker login succeeded!"
fi


## docker tag
docker tag $TARGET $DOCKER_HOST/$PROJECT/$TARGET:latest


## docker push
echo "*****[Info]***** docker pushing ..."
echo "docker push $DOCKER_HOST/$PROJECT/$TARGET"
docker push $DOCKER_HOST/$PROJECT/$TARGET
if [[ $? -ne 0 ]]; then
    echo "*****[Error]***** docker push failed!"
    exit -1
else
    echo "*****[Info]***** docker push succeeded!"
fi

echo "*****[Info]***** build succeeded!"

