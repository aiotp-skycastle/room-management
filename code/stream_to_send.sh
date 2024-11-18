#!/bin/bash

# Step 1: Start capturing and generating HLS files       
ffmpeg -f v4l2 -i /dev/video0 -codec:v libx264 -preset ultrafast -f hls -hls_time 1 -hls_list_size 3 -hls_flags delete_segments+split_by_time /home/yuyu/teamproject/camera/index.m3u8 &

# Step 2: Start sending HLS files to server B using rsync
while true; do
    rsync -avz /home/yuyu/teamproject/camera/ yuyu@192.168.193.92:/home/yuyu/djangotest/myproject/hls/
    sleep 1
done

