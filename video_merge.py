#!/usr/bin/env python

import os
import re
import sys
import glob
import subprocess
import multiprocessing
import ConfigParser

HOME = os.path.dirname(os.path.realpath(__file__))
pathEnv = os.getenv('PATH')
os.environ['PATH'] = "%s" % (HOME) + ":" + pathEnv
session_tag="new session started"


def SessionConvert(folder_name):
    child_env = os.environ.copy()
    if not os.path.isdir(folder_name):
        print "Folder " + folder_name + " does not exit"
        return
    os.chdir(folder_name)
    videos = dict()
    cmd = []
    tmp_new_prefix = "tmp_new_"
    merge_videos = []
    arr = folder_name.split("/")
    class_id_temp = arr[len(arr)-1]
    class_id_temp_arr = class_id_temp.split("_")
    class_id = class_id_temp_arr[0]
    suffix = ""
    with open("users.txt") as f:
        lines = f.readlines()
        for line in lines:
            items = line.split(" ");
            user_id = items[0]
            ts = int(items[1])
            video = glob.glob("final_"+user_id+"_*.mp4")
            my_final = video[0]
            if my_final:
                videos[user_id] = my_final
                tmp_my_final = "tmp_" + my_final
                tmp_frame = "tmp_frame_"+my_final
                tmp_new_final = tmp_new_prefix+my_final
                if ts > 0:
                    ts = str(ts)
                    cmd.append("ffmpeg -ss 00:00:00 -i "+my_final+" -vframes 1 -q:v 2 "+tmp_my_final+".jpg")
                    cmd.append("ffmpeg -i "+tmp_my_final+".jpg -vf lutyuv=u=128:v=128:y=0 "+tmp_frame+".jpg")
                    cmd.append('ffmpeg -i '+my_final+' -loop 1 -t '+ts+' -i '+tmp_frame+'.jpg -f lavfi -t '+ts+' -i aevalsrc=0 -filter_complex " [1:v] [2:a]   [0:v] [0:a] concat=n=2:v=1:a=1 [v] [a]" -c:v libx264 -c:a aac -strict -2   -map "[v]" -map "[a]" '+tmp_new_final)
                else:
                    tmp_suffix_arr = my_final.split(".")[0].split("_")
                    suffix = tmp_suffix_arr[len(tmp_suffix_arr) - 2]+"_"+tmp_suffix_arr[len(tmp_suffix_arr) - 1]
                    cmd.append('cp '+my_final+' '+tmp_new_final)
                merge_videos.append(tmp_new_final)

        hv = ['hstack', 'vstack']
        for h in hv:
            merge_cmd = "ffmpeg "
            index = 0
            n_v_n = ""
            n_a_n = ""
            for v in merge_videos:
                merge_cmd += "-i "+v+" "
                n_v_n += "["+str(index)+":v:0]"
                n_a_n += "["+str(index)+":a:0]"
                index = index + 1

            merge_cmd += '-filter_complex "' + n_v_n + h +'=inputs=' + str(len(merge_videos)) + ';' + n_a_n + ' amix=inputs=' + str(len(merge_videos)) + ':duration=first:dropout_transition=0,dynaudnorm" ' + 'ultimate-' + h + '_' + suffix + '.mp4';
            cmd.append(merge_cmd)

        real_cmd = " && ".join(cmd)
        print real_cmd
        print subprocess.Popen(real_cmd, shell=True, env=child_env).wait()
        print "\n\n"
        # remove tmp files
        os.system('rm -f tmp_*')
        f = open("ultimate-done.txt", "w")
        f.close()

def worker(dirs):
    for every_dir_name in dirs:
        print "dir_name:", every_dir_name
        if not os.path.isdir(every_dir_name):
            continue
        print "handle dir_name:", every_dir_name
        SessionConvert(every_dir_name)

config = ConfigParser.ConfigParser()
config.read("/agora2/Agora_Recording_SDK_for_Linux_FULL/tools/conf.ini")
try:
    node = config.get("global", "node")
except:
    node = 0
node = abs(int(node))
worker_num = 5
all_dirs = []
for i in range(0, worker_num):
    all_dirs.append([])
if node > 0:
    dir_names = glob.glob("/agora_public/sp" + str(node) + "/201*/*")
else:
    dir_names = glob.glob("/agora2/201*/*")
i = 1
for dir_name in dir_names:
    if not os.path.isdir(dir_name):
        continue
    convert_done_file_path = os.path.join(dir_name, "users.txt")
    if not os.path.exists(convert_done_file_path):
        print "merge_prepare_users_txt_not_done, gone"
        continue

    convert_done_file_path = os.path.join(dir_name, "ultimate-done.txt")
    print "merge_done_file_path:", convert_done_file_path
    if os.path.exists(convert_done_file_path):
        print "merge_already_done, gone"
        continue

    index = i % worker_num
    all_dirs[index].append(dir_name)
    i = i + 1
for i in range(worker_num):
    p = multiprocessing.Process(target=worker, args=(all_dirs[i],))
    p.start()
